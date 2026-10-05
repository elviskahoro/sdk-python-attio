"""Tests for the generation-path selection in ``ci/pipeline.py``.

``_local_speakeasy_usable`` decides whether generation runs through the host
Speakeasy CLI (fast, no Dagger engine — the path the scheduled GitHub
workflow depends on) or through the pinned container via Dagger. A silent
regression here would only surface on the next real regeneration, so the
decision table is pinned by tests.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
PIPELINE = REPO_ROOT / "ci" / "pipeline.py"


def _load_pipeline_module():
    spec = importlib.util.spec_from_file_location("attio_test_pipeline", PIPELINE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


PIPE = _load_pipeline_module()


@pytest.mark.parametrize(
    ("cli_path", "authed", "api_key", "use_host_cli", "expected"),
    [
        pytest.param(None, False, None, None, False, id="cli-missing"),
        pytest.param(
            "/usr/local/bin/speakeasy", False, None, None, False, id="cli-no-auth-no-key"
        ),
        pytest.param(
            "/usr/local/bin/speakeasy",
            False,
            "some-key",
            None,
            False,
            id="key-alone-stays-on-pinned-container",
        ),
        pytest.param(
            "/usr/local/bin/speakeasy",
            True,
            None,
            None,
            True,
            id="login-session-without-key-uses-host-cli",
        ),
        pytest.param(
            "/usr/local/bin/speakeasy",
            True,
            "some-key",
            None,
            False,
            id="login-session-plus-key-stays-on-pinned-container",
        ),
        pytest.param(
            "/usr/local/bin/speakeasy",
            False,
            "some-key",
            "1",
            True,
            id="key-with-host-cli-opt-in",
        ),
        pytest.param(
            "/usr/local/bin/speakeasy",
            True,
            "some-key",
            "1",
            True,
            id="login-and-key-with-host-cli-opt-in",
        ),
    ],
)
def test_local_speakeasy_usable(
    monkeypatch: pytest.MonkeyPatch,
    cli_path: str | None,
    authed: bool,
    api_key: str | None,
    use_host_cli: str | None,
    expected: bool,
) -> None:
    monkeypatch.setattr(
        "shutil.which", lambda name: cli_path if name == "speakeasy" else None
    )
    monkeypatch.setattr(PIPE, "_has_local_speakeasy_auth", lambda: authed)
    for var in ("SPEAKEASY_API_KEY", "SPEAKEASY_USE_HOST_CLI"):
        monkeypatch.delenv(var, raising=False)
    if api_key is not None:
        monkeypatch.setenv("SPEAKEASY_API_KEY", api_key)
    if use_host_cli is not None:
        monkeypatch.setenv("SPEAKEASY_USE_HOST_CLI", use_host_cli)

    assert PIPE._local_speakeasy_usable() is expected


def test_sync_update_workflow_writes_repo_workflow_not_cwd(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo = tmp_path / "repo"
    repo_workflow = repo / ".speakeasy" / "workflow.yaml"
    repo_workflow.parent.mkdir(parents=True)
    repo_workflow.write_text(
        "location: openapi/api-000.json\n"
        "output: openapi/api-000-overlay.json\n",
        encoding="utf-8",
    )

    elsewhere = tmp_path / "elsewhere"
    cwd_workflow = elsewhere / ".speakeasy" / "workflow.yaml"
    cwd_workflow.parent.mkdir(parents=True)
    cwd_workflow.write_text(
        "location: openapi/api-000.json\n"
        "output: openapi/api-000-overlay.json\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(PIPE, "_WORKFLOW_YAML", repo_workflow)
    monkeypatch.chdir(elsewhere)

    PIPE._sync_update_workflow(
        "openapi/api-111-overlay.json",
        "openapi/api-111.json",
    )

    assert repo_workflow.read_text(encoding="utf-8") == (
        "location: openapi/api-111.json\n"
        "output: openapi/api-111-overlay.json\n"
    )
    assert cwd_workflow.read_text(encoding="utf-8") == (
        "location: openapi/api-000.json\n"
        "output: openapi/api-000-overlay.json\n"
    )


def test_check_openapi_forwards_flags_to_spec_diff(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """``check-openapi`` must forward --report/--no-strict verbatim and
    propagate the exit code as SystemExit."""
    import asyncio
    import importlib.util

    # Load by path (like the pipeline itself does) rather than inserting
    # ci/ into sys.path, which would cache a second copy of the module
    # under a different name and split monkeypatching across copies.
    spec = importlib.util.spec_from_file_location(
        "attio_test_spec_diff_forwarding", REPO_ROOT / "ci" / "spec_diff.py"
    )
    sd = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(sd)

    recorded: dict[str, list[str]] = {}

    def fake_main(argv: list[str]) -> int:
        recorded["argv"] = argv
        return 0

    # cmd_check_openapi loads ci/spec_diff.py by path; patch the loader so
    # it returns the module instance we can intercept.
    monkeypatch.setattr(PIPE, "_load_spec_diff_module", lambda: sd)
    monkeypatch.setattr(sd, "main", fake_main)

    asyncio.run(PIPE.cmd_check_openapi(report="tmp/x.json", no_strict=True))
    assert recorded["argv"] == ["check", "--report", "tmp/x.json", "--no-strict"]

    monkeypatch.setattr(sd, "main", lambda argv: 1)
    with pytest.raises(SystemExit) as excinfo:
        asyncio.run(PIPE.cmd_check_openapi(report=None, no_strict=False))
    assert excinfo.value.code == 1


def test_local_speakeasy_usable_requires_cli_when_opted_in(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """An explicit host-CLI opt-in with no CLI installed must fail loudly,
    not silently fall back to the Dagger path (the scheduled workflow has
    no container runtime — the fallback would die with an unrelated engine
    error after the spec was already adopted)."""
    monkeypatch.setattr("shutil.which", lambda name: None)
    monkeypatch.delenv("SPEAKEASY_API_KEY", raising=False)
    monkeypatch.setenv("SPEAKEASY_USE_HOST_CLI", "1")
    with pytest.raises(RuntimeError, match="not on PATH"):
        PIPE._local_speakeasy_usable()


def test_generate_blocks_when_overlay_unhealthy(monkeypatch: pytest.MonkeyPatch) -> None:
    """The overlay-health gate must fire before any generation runs."""
    import asyncio

    generation_calls: list[str] = []

    async def fake_run_local(*, version: str | None) -> None:
        generation_calls.append("local")

    def boom(*, skip: bool = False) -> None:
        raise RuntimeError("overlay is unhealthy — fix overlay.yaml before generating")

    monkeypatch.delenv("SKIP_OVERLAY_CHECK", raising=False)
    monkeypatch.setattr(PIPE, "_local_speakeasy_usable", lambda: True)
    monkeypatch.setattr(PIPE, "_run_local_speakeasy", fake_run_local)
    monkeypatch.setattr(PIPE, "_has_local_speakeasy_auth", lambda: True)
    monkeypatch.setattr(PIPE, "_verify_overlay_health", boom)

    with pytest.raises(RuntimeError, match="overlay is unhealthy"):
        asyncio.run(PIPE.cmd_generate(force=False, version=None, no_fetch=True))
    assert generation_calls == []


def test_generate_no_fetch_skips_fetch(monkeypatch: pytest.MonkeyPatch) -> None:
    """``--no-fetch`` must not touch the spec; the gate still runs."""
    import asyncio

    fetched: list[int] = []
    generation_calls: list[str] = []

    async def fake_fetch() -> str:
        fetched.append(1)
        return "openapi/api-unused.json"

    async def fake_run_local(*, version: str | None) -> None:
        generation_calls.append("local")

    monkeypatch.delenv("SKIP_OVERLAY_CHECK", raising=False)
    monkeypatch.setattr(PIPE, "fetch_latest_spec", fake_fetch)
    monkeypatch.setattr(PIPE, "_local_speakeasy_usable", lambda: True)
    monkeypatch.setattr(PIPE, "_run_local_speakeasy", fake_run_local)
    monkeypatch.setattr(PIPE, "_has_local_speakeasy_auth", lambda: True)
    monkeypatch.setattr(PIPE, "_verify_overlay_health", lambda *, skip=False: None)

    asyncio.run(PIPE.cmd_generate(force=False, version=None, no_fetch=True))
    assert fetched == []
    assert generation_calls == ["local"]


def test_generate_skip_overlay_check_bypasses_gate(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The escape hatch must reach the gate as skip=True and let generation
    proceed even when the gate would otherwise raise."""
    import asyncio

    generation_calls: list[str] = []

    async def fake_run_local(*, version: str | None) -> None:
        generation_calls.append("local")

    def gate(*, skip: bool = False) -> None:
        assert skip is True, "escape hatch must be forwarded to the gate"

    monkeypatch.setattr(PIPE, "_local_speakeasy_usable", lambda: True)
    monkeypatch.setattr(PIPE, "_run_local_speakeasy", fake_run_local)
    monkeypatch.setattr(PIPE, "_has_local_speakeasy_auth", lambda: True)
    monkeypatch.setattr(PIPE, "_verify_overlay_health", gate)

    asyncio.run(PIPE.cmd_generate(force=False, version=None, no_fetch=True, skip_overlay_check=True))
    assert generation_calls == ["local"]

    # The env var takes the same path without the flag — and only a truly
    # truthy value counts, so "=0"/"=false" cannot silently disable the gate.
    monkeypatch.setenv("SKIP_OVERLAY_CHECK", "1")
    asyncio.run(PIPE.cmd_generate(force=False, version=None, no_fetch=True))
    assert generation_calls == ["local", "local"]

    monkeypatch.setenv("SKIP_OVERLAY_CHECK", "0")
    with pytest.raises(AssertionError, match="escape hatch must be forwarded"):
        asyncio.run(PIPE.cmd_generate(force=False, version=None, no_fetch=True))


def test_ci_and_generate_subcommands_parse_all_flags(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """main() passes args.<flag> to the handlers for both subcommands; a
    flag added to one subparser but not the other crashes every invocation
    of the other (as happened with --skip-overlay-check). Pin both."""
    import asyncio
    import sys

    recorded: dict[str, dict] = {}

    async def fake_cmd_ci(**kwargs: object) -> None:
        recorded["ci"] = kwargs

    async def fake_cmd_generate(**kwargs: object) -> None:
        recorded["generate"] = kwargs

    monkeypatch.setattr(PIPE, "cmd_ci", fake_cmd_ci)
    monkeypatch.setattr(PIPE, "cmd_generate", fake_cmd_generate)

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "pipeline.py",
            "ci",
            "--force",
            "--version",
            "9.9.9",
            "--publish",
            "--skip-overlay-check",
        ],
    )
    PIPE.main()
    assert recorded["ci"] == {
        "force": True,
        "version": "9.9.9",
        "publish": True,
        "skip_overlay_check": True,
    }

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "pipeline.py",
            "generate",
            "--force",
            "--version",
            "9.9.9",
            "--no-fetch",
            "--skip-overlay-check",
        ],
    )
    PIPE.main()
    assert recorded["generate"] == {
        "force": True,
        "version": "9.9.9",
        "no_fetch": True,
        "skip_overlay_check": True,
    }


class _AsyncNullCM:
    """Async context manager standing in for dagger.connection(...)."""

    async def __aenter__(self) -> "_AsyncNullCM":
        return self

    async def __aexit__(self, *exc: object) -> bool:
        return False


def test_generate_sdk_dagger_path_exports_and_patches(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The container path must run generation, export src/, and re-apply
    the post-generation patches."""
    import asyncio
    from types import SimpleNamespace

    events: list[str] = []

    class FakeGeneratedDir:
        async def export(self, dest: str) -> None:
            events.append(f"export:{dest}")

    class FakePipeline:
        def __init__(self, source: object) -> None:
            events.append("pipeline_init")

        async def generate(self, *, api_key: object, force: bool, version: str | None):
            events.append(f"generate:force={force}")
            return FakeGeneratedDir()

    monkeypatch.setattr(
        PIPE,
        "dagger",
        SimpleNamespace(connection=lambda cfg: _AsyncNullCM(), Config=lambda **kw: None),
    )

    class FakeHostDir:
        def directory(self, *args: object, **kwargs: object) -> "FakeHostDir":
            return self

    host_dir = FakeHostDir()
    monkeypatch.setattr(
        PIPE,
        "dag",
        SimpleNamespace(
            set_secret=lambda n, v: f"secret:{n}",
            host=lambda: SimpleNamespace(directory=lambda *a, **k: host_dir),
        ),
    )
    monkeypatch.setattr(PIPE, "AttioSDKPipeline", FakePipeline)
    monkeypatch.setattr(PIPE, "_local_speakeasy_usable", lambda: False)
    monkeypatch.setattr(PIPE, "_apply_post_generation_patches", lambda: events.append("patch"))

    asyncio.run(PIPE._generate_sdk(force=True, version=None, api_key_str="some-key"))
    assert events == ["pipeline_init", "generate:force=True", "export:./src", "patch"]


def test_generate_sdk_dagger_path_requires_api_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The unreachable-guard must fire loudly if a refactor ever lets the
    container path run without a key."""
    import asyncio

    monkeypatch.setattr(PIPE, "_local_speakeasy_usable", lambda: False)
    with pytest.raises(RuntimeError, match="unreachable"):
        asyncio.run(PIPE._generate_sdk(force=False, version=None, api_key_str=None))


def test_cmd_ci_gates_before_generating(monkeypatch: pytest.MonkeyPatch) -> None:
    """``ci`` must fetch, run the overlay gate, then generate — in that
    order — before testing and building."""
    import asyncio
    from types import SimpleNamespace

    events: list[str] = []

    async def fake_fetch() -> str:
        events.append("fetch")
        return "openapi/api-x.json"

    def gate(*, skip: bool = False) -> None:
        events.append("gate")

    async def fake_generate_sdk(**kwargs: object) -> None:
        events.append("generate")

    class FakeDistDir:
        async def export(self, dest: str) -> None:
            events.append(f"dist:{dest}")

    class FakeBuilt:
        def directory(self, path: str) -> FakeDistDir:
            return FakeDistDir()

    class FakePipeline:
        def __init__(self, source: object) -> None:
            pass

        async def test(self) -> str:
            events.append("test")
            return "ok"

        def build(self) -> FakeBuilt:
            events.append("build")
            return FakeBuilt()

    monkeypatch.delenv("SPEAKEASY_API_KEY", raising=False)
    monkeypatch.delenv("SKIP_OVERLAY_CHECK", raising=False)
    monkeypatch.setattr(PIPE, "_has_local_speakeasy_auth", lambda: True)
    monkeypatch.setattr(PIPE, "fetch_latest_spec", fake_fetch)
    monkeypatch.setattr(PIPE, "_verify_overlay_health", gate)
    monkeypatch.setattr(PIPE, "_generate_sdk", fake_generate_sdk)
    monkeypatch.setattr(
        PIPE,
        "dagger",
        SimpleNamespace(connection=lambda cfg: _AsyncNullCM(), Config=lambda **kw: None),
    )

    class FakeHostDir:
        def directory(self, *args: object, **kwargs: object) -> "FakeHostDir":
            return self

    host_dir = FakeHostDir()
    monkeypatch.setattr(
        PIPE,
        "dag",
        SimpleNamespace(
            set_secret=lambda n, v: f"secret:{n}",
            host=lambda: SimpleNamespace(directory=lambda *a, **k: host_dir),
        ),
    )
    monkeypatch.setattr(PIPE, "AttioSDKPipeline", FakePipeline)
    monkeypatch.setattr(PIPE, "_replace_dist_directory", lambda: events.append("swap_dist"))

    asyncio.run(PIPE.cmd_ci(force=False, version=None, publish=False))
    assert events == [
        "fetch",
        "gate",
        "generate",
        "test",
        "build",
        "swap_dist",
        "dist:./dist",
    ]


def test_gate_failure_restores_prefetch_workflow_reference(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """A failed overlay gate must roll workflow.yaml back to what it said
    BEFORE the fetch adopted the new spec — snapshotting after the fetch
    would make the rollback a no-op (the bug this test pins)."""
    import asyncio

    scratch = tmp_path / "workflow.yaml"
    scratch.write_text("location: openapi/api-OLD.json\n", encoding="utf-8")
    monkeypatch.setattr(PIPE, "_WORKFLOW_YAML", scratch)
    monkeypatch.setattr(PIPE, "_REPO_ROOT", tmp_path)

    async def adopting_fetch() -> str:
        scratch.write_text("location: openapi/api-NEW.json\n", encoding="utf-8")
        spec_file = tmp_path / "openapi" / "api-NEW.json"
        spec_file.parent.mkdir(parents=True, exist_ok=True)
        spec_file.write_text("{}\n", encoding="utf-8")
        return "openapi/api-NEW.json"

    def boom(*, skip: bool = False) -> None:
        raise RuntimeError("overlay is unhealthy")

    monkeypatch.setattr(PIPE, "fetch_latest_spec", adopting_fetch)
    monkeypatch.setattr(PIPE, "_verify_overlay_health", boom)

    with pytest.raises(RuntimeError, match="overlay is unhealthy"):
        asyncio.run(PIPE._fetch_then_verify_overlay(skip=False))
    assert scratch.read_text(encoding="utf-8") == "location: openapi/api-OLD.json\n"
    # The unadopted spec file is removed too.
    assert not (tmp_path / "openapi" / "api-NEW.json").exists()


def test_gate_success_keeps_adopted_workflow_reference(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """A passing gate leaves the freshly adopted reference in place."""
    import asyncio

    scratch = tmp_path / "workflow.yaml"
    scratch.write_text("location: openapi/api-OLD.json\n", encoding="utf-8")
    monkeypatch.setattr(PIPE, "_WORKFLOW_YAML", scratch)
    monkeypatch.setattr(PIPE, "_REPO_ROOT", tmp_path)

    async def adopting_fetch() -> str:
        scratch.write_text("location: openapi/api-NEW.json\n", encoding="utf-8")
        return "openapi/api-NEW.json"

    monkeypatch.setattr(PIPE, "fetch_latest_spec", adopting_fetch)
    monkeypatch.setattr(PIPE, "_verify_overlay_health", lambda *, skip=False: None)

    asyncio.run(PIPE._fetch_then_verify_overlay(skip=False))
    assert scratch.read_text(encoding="utf-8") == "location: openapi/api-NEW.json\n"


def test_log_host_cli_version_warns_on_drift_and_unparseable_banner(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """CLI drift from the pin — and an unparsable banner — must be loud."""
    from types import SimpleNamespace

    monkeypatch.setattr(
        "shutil.which",
        lambda name: "/usr/local/bin/speakeasy" if name == "speakeasy" else None,
    )

    def fake_run(cmd: list[str], **kwargs: object) -> SimpleNamespace:
        return SimpleNamespace(stdout=banners[-1], stderr="")

    banners: list[str] = []
    monkeypatch.setattr("subprocess.run", fake_run)

    banners.append("speakeasy version 0.1.0\n")
    PIPE._log_host_cli_version()
    err = capsys.readouterr().err
    assert "differs from the pinned" in err

    banners.append("speakeasy-cli custom build, no standard banner\n")
    PIPE._log_host_cli_version()
    err = capsys.readouterr().err
    assert "could not parse the CLI version" in err

---
name: rwx
description: Run, debug, and edit RWX CI for this repo from the CLI. Use when asked to run CI/tests on RWX, check why CI or a PR is failing, fetch RWX logs/results/artifacts, run pyright/pyrefly remotely, dispatch the regenerate workflow, or create/modify any file in `.rwx/`.
allowed-tools: Read, Grep, Glob, Bash
---

# RWX CLI in this repo

CI definitions live in `.rwx/`. Upstream skills (config authoring, GitHub Actions migration) are at https://github.com/rwx-cloud/skills; this file is the repo-specific version.

| File | Trigger | Notes |
| --- | --- | --- |
| `pytest.yml` | PR, push to main, merge queue, `cli` | Uploads JUnit to Trunk Flaky Tests (main, merge-queue, manual, `elviskahoro` PRs only) |
| `trunk-check.yml` | PR, push to main, merge queue, `cli` | Trunk lint |
| `integration.yml` | PR, push to main, `cli` | Reads the `sdk-python-attio-it` vault (throwaway key, unlocked, no approver) |
| `pyright.yml`, `pyrefly.yml` | `cli` only | Type checks on the working tree; `paths` init, default `attio_cli ci` |
| `regenerate.yml` | `cli`, `dispatch` | Needs `SPEAKEASY_API_KEY`; vault is main-only with approvals, so use `rwx dispatch` |
| `spec-update-check.yml` | weekly cron (Mon 09:00 UTC), `cli` | Main-pinned; same vault rules |
| `publish.yml` | `v*` tag (manual start), `cli` | Release |

## Auth

The CLI reads only `RWX_ACCESS_TOKEN` (or `--access-token`). Sandboxes inject one token per RWX org under suffixed names, so map the right one in. Never print the value.

```bash
env | grep -E '^RW[XC]_ACCESS_TOKEN_' | cut -d= -f1      # names only
export RWX_ACCESS_TOKEN="$RWC_ACCESS_TOKEN_ELVISKAHORO"  # this repo's org
rwx whoami                                               # confirm the login
```

- The prefix may be `RWX_` or `RWC_`; match on the org suffix (the owner in `git remote get-url origin`, uppercased).
- Run, task, and log IDs resolve only under the owning org. A token for another org (e.g. `RWX_ACCESS_TOKEN_MARCHILI`) authenticates but returns `not found` or `Unauthorized`: switch tokens.
- Pullfrog GitHub Actions agents have no CLI or tokens; use `gh api repos/<owner>/<repo>/commits/<sha>/status` for the run URL and failure description.

## Run CI on your working tree

`rwx run` sends a git patch, so no commit or push is needed.

```bash
rwx run .rwx/pytest.yml --wait --fail-fast          # run and wait for the result
rwx run .rwx/pytest.yml --target <task-key> --wait  # one task plus its dependencies
rwx run .rwx/pytest.yml --title "wip: change" --json
```

- Base: nearest ancestor of `HEAD` already on `origin` (`event.git.sha`). On top: unpushed commits, staged, unstaged, and untracked files. Excluded: gitignored files. Git LFS changes error out. `RWX_DISABLE_GIT_PATCH=1` disables patching.
- The `git/clone` task uses `ref: ${{ init.commit-sha }}` and the `cli` trigger sets `commit-sha: ${{ event.git.sha }}`. Keep that wiring when editing `.rwx/*.yml`.
- Runs that need vault secrets (`regenerate`, `spec-update-check`) cannot resolve them off `main` without an approval. Use dispatch instead.

## Type checking without a local venv

```bash
rwx run .rwx/pyright.yml --wait
rwx run .rwx/pyright.yml --wait --init paths="attio_cli/foo.py ci/bar.py"
rwx run .rwx/pyrefly.yml --wait --init paths="attio_cli"
```

## Dispatch regenerate (no local Speakeasy or Docker)

```bash
rwx dispatch regenerate --ref main                 # --param fetch=true adopts the latest spec
rwx artifacts download <run-id> --task patch regenerate-patch --auto-extract
git apply .rwx/downloads/<dir>/regenerate.patch
```

It never commits or pushes. See "Regenerating on RWX" in `AGENTS.md`.

## Results, logs, artifacts

```bash
rwx results -h                                # status of a branch/commit/run
rwx results <run-id>                          # failures, including vault/approval errors GitHub hides
rwx runs list
rwx logs <task-id> --output /tmp/rwxlogs      # task ids come from `rwx results`
rwx logs <run-id> --task <task-key> --output /tmp/logs
rwx artifacts download <run-id> ...
```

The run ID is the hex id in `cloud.rwx.com/elviskahoro/runs/<id>`. Add `--json` to parse. Other useful commands: `rwx retry`, `rwx cancel`, `rwx debug <task>`, `rwx ssh`, `rwx vaults list` (the only way to see vault grants).

## Sandboxes

`rwx sandbox exec -- <command>` runs a command in a persistent RWX sandbox.

## Editing `.rwx/*.yml`

1. Pull the reference before writing config, and do not truncate the output: `rwx docs pull /migrating/rwx-reference`.
2. For anything else: `rwx docs search "<query>"`, then `rwx docs pull <path>` (e.g. `/docs/cli-triggers`). Use these instead of WebFetch.
3. Validate: `rwx lint .rwx/<name>.yml`.
4. Repo rules: pin uv in every workflow (`tests/` enforces it); never reference `--skip-overlay-check` or `SKIP_OVERLAY_CHECK` in `.rwx/` (`tests/test_no_skip_overlay_check.py` fails); keep `trunk-upload` secrets scoped as described in `AGENTS.md`.
5. Prove the change with `rwx run .rwx/<name>.yml --wait`.

#!/usr/bin/env python3
"""Build the docs site: authored docs_site/content + generated/docs -> site/.

Navigation is derived from the tree, so new generated pages appear automatically.
Authored content lives outside generated/, so Speakeasy never touches it.
"""
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "tmp" / "docs-src"
ATTIO_DOCS = "https://docs.attio.com"


def section_index(title: str, d: Path) -> None:
    pages = sorted(p for p in d.rglob("*.md") if p.name != "index.md")
    lines = [f"# {title}", ""]
    for p in pages:
        rel = p.relative_to(d).as_posix()
        label = p.parent.name if p.name == "README.md" else p.stem
        lines.append(f"- [{label}]({rel})")
    (d / "index.md").write_text("\n".join(lines) + "\n")


def main() -> int:
    if SRC.exists():
        shutil.rmtree(SRC)
    shutil.copytree(ROOT / "docs_site" / "content", SRC)
    for name in ("sdks", "models", "errors"):
        shutil.copytree(ROOT / "generated" / "docs" / name, SRC / name)
    for p in SRC.rglob("*.md"):
        text = p.read_text()
        # Root-relative links point at Attio's own docs, not this site.
        text = re.sub(r"\]\(/((?:docs|rest-api)/)", rf"]({ATTIO_DOCS}/\1", text)
        p.write_text(text)
    section_index("SDK resources", SRC / "sdks")
    section_index("Models", SRC / "models")
    section_index("Errors", SRC / "errors")

    def nav(name: str, title: str) -> str:
        items = [f"      - {name}/index.md"]
        for p in sorted((SRC / name).rglob("*.md")):
            rel = p.relative_to(SRC).as_posix()
            if p.name != "index.md":
                label = p.parent.name if p.name == "README.md" else p.stem
                items.append(f"      - {label}: {rel}")
        return f"  - {title}:\n" + "\n".join(items)

    nav_yaml = "\n".join(
        ["nav:", "  - Home: index.md", "  - Getting started: getting-started.md"]
        + [nav("sdks", "SDK resources"), nav("models", "Models"), nav("errors", "Errors")]
    )
    cfg = ROOT / "tmp" / "mkdocs.yml"
    cfg.write_text(
        (ROOT / "docs_site" / "mkdocs.yml").read_text()
        .replace("docs_dir: ../tmp/docs-src", "docs_dir: docs-src")
        .replace("site_dir: ../site", "site_dir: ../site")
        + nav_yaml + "\n"
    )
    cmd = [sys.executable, "-m", "mkdocs", "build", "-f", str(cfg)]
    if "--strict" in sys.argv:
        cmd.append("--strict")
    return subprocess.call(cmd, cwd=ROOT)


if __name__ == "__main__":
    sys.exit(main())

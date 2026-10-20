from __future__ import annotations

import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT.parent / "SY_SKhynix_DART_Agent.zip"
EXCLUDED_PARTS = {".git", ".github", "__pycache__", ".pytest_cache", ".mypy_cache"}


def build() -> Path:
    if OUTPUT.exists():
        OUTPUT.unlink()
    with zipfile.ZipFile(OUTPUT, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(ROOT.rglob("*")):
            if not path.is_file():
                continue
            relative = path.relative_to(ROOT)
            if any(part.startswith(".") or part in EXCLUDED_PARTS for part in relative.parts):
                continue
            if path.suffix in {".pyc", ".pyo"}:
                continue
            archive.write(path, Path("SY_SKhynix_DART_Agent") / relative)
    with zipfile.ZipFile(OUTPUT) as archive:
        hidden = [name for name in archive.namelist() if any(part.startswith(".") for part in Path(name).parts)]
        if hidden:
            OUTPUT.unlink(missing_ok=True)
            raise RuntimeError(f"Hidden entries found in ZIP: {hidden}")
    return OUTPUT


if __name__ == "__main__":
    print(build())

"""
run_all_animations.py
---------------------

Automatically install missing third-party packages and execute every
*.py animation script in a folder.

Usage
-----
    python run_all_animations.py            # uses ../sampled/matplotlib_fixed
    python run_all_animations.py --dir /path/to/folder
"""

from __future__ import annotations
import argparse
import importlib
import pathlib
import re
import subprocess
import sys
from subprocess import TimeoutExpired

# ---------- helpers ----------------------------------------------------------
STD_LIB_ROOTS = {
    # core & built-ins (extend as you wish—these are *not* auto-installed)
    "abc", "array", "asyncio", "base64", "collections", "contextlib", "copy",
    "csv", "datetime", "enum", "functools", "glob", "hashlib", "heapq",
    "importlib", "inspect", "io", "itertools", "json", "logging", "math",
    "operator", "os", "pathlib", "pickle", "queue", "random", "re",
    "shlex", "socket", "statistics", "string", "subprocess", "sys", "tempfile",
    "threading", "time", "typing", "uuid"
}

PIP_NAME_MAP = {
    "skimage": "scikit-image",
    "sklearn": "scikit-learn",
    "cv2": "opencv-python",
    "PIL": "pillow",
    "yaml": "PyYAML",
    "crypto": "pycryptodome",
}

IMPORT_RE = re.compile(r"^\s*(?:from|import)\s+([A-Za-z_][\w.]*)")

def extract_roots(py_file: pathlib.Path) -> set[str]:
    """Return the set of top-level import roots used in *py_file*."""
    roots: set[str] = set()
    with py_file.open(encoding="utf-8") as fh:
        for line in fh:
            m = IMPORT_RE.match(line)
            if m:
                root = m.group(1).split(".")[0]
                if root and root not in STD_LIB_ROOTS and root != "__future__":
                    roots.add(root)
    return roots

def ensure_installed(import_root: str) -> None:
    """Attempt to import *pkg*; if it fails, install it with pip."""
    try:
        importlib.import_module(import_root)
        return
    except ModuleNotFoundError:
        pass

    pip_pkg = PIP_NAME_MAP.get(import_root, import_root)
    print(f"📦 Installing: {pip_pkg} (import as {import_root})")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", pip_pkg])
    except subprocess.CalledProcessError as exc:
        print(f"⚠️ pip install failed for {pip_pkg} (exit {exc.returncode}")

# ---------- main -------------------------------------------------------------
def main(folder: pathlib.Path) -> None:
    if not folder.is_dir():
        sys.exit(f"Error: {folder} is not a directory")

    py_files = sorted(folder.glob("*.py"))
    if not py_files:
        sys.exit(f"No .py files found in {folder}")

    print(f"\n🔍 Scanning {len(py_files)} Python files in {folder}\n")

    # 1) Collect & install dependencies once per file
    for script in py_files:
        imports = extract_roots(script)
        for root in sorted(imports):
            ensure_installed(root)

    # 2) Run each script
    for script in py_files:
        print(f"▶️  Running {script.name} …")
        try:
            subprocess.run([sys.executable, str(script)], check=True, timeout=300)
            print(f"✅ Finished {script.name}\n")
        except subprocess.CalledProcessError as exc:
            with open('error.log', 'a') as log_file:
                log_file.write(f"Error running {script.name}: {exc}\n")
            print(f"❌ {script.name} exited with status {exc.returncode}\n")
        except TimeoutExpired as exc:
            with open('error.log', 'a') as log_file:
                log_file.write(f"Timeout expired for {script.name}: {exc.timeout}\n")
            print(f"⏰ {script.name} timed out after 300 seconds\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Batch-run matplotlib animations")
    parser.add_argument(
        "--dir", "-d",
        type=pathlib.Path,
        default=pathlib.Path("../../sampled/matplotlib_fixed"),
        help="Directory containing animation scripts (default: ../sampled/matplotlib_fixed)",
    )
    args = parser.parse_args()
    main(args.dir.resolve())

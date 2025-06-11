"""
Stream-sample Python files that create animations with

    • PyVista     – .open_movie(...)
    • Mayavi      – mlab.animate or an explicit time-frame loop
    • VTK         – vtkAVIWriter / vtkMP4Writer
    • VisIt (CLI) – TimeSliderGetNStates() + loop over states

Matched files are copied, de-duplicated by SHA-1, into
    ../sampled/{mayavi, pyvista, vtk, visit}/<sha1>.py
"""

import hashlib
import os
import re
from pathlib import Path
from datasets import load_dataset
from tqdm.auto import tqdm

FILTERS = {
    "pyvista": {
        "import": re.compile(r"^\s*(?:from|import)\s+pyvista\b", re.I | re.M),
        "anim":   re.compile(r"\.open_movie\s*\(", re.I),
    },
    "mayavi": {
        "import": re.compile(r"^\s*(?:from|import)\s+mayavi\b", re.I | re.M),
        "anim": re.compile(
            r"(mlab\.animate\s*\(|"
            r"for\s+\w+\s+in\s+.*(range|times?|frames?)\s*\()"
            , re.I | re.S),
    },
    "vtk": {
        "import": re.compile(r"^\s*(?:from|import)\s+vtk\b", re.I | re.M),
        "anim":   re.compile(r"vtk(?:AVI|MP4)Writer", re.I),
    },
    "visit": {
        "import": re.compile(r"^\s*(?:from|import)\s+visit\b", re.I | re.M),
        "anim": re.compile(
            r"TimeSliderGetNStates\s*\(\s*\).*?for\s+\w+\s+in\s+range\(",
            re.I | re.S),
    },
}

ROOT = Path("../sampled").resolve()
for lib in FILTERS:
    (ROOT / lib).mkdir(parents=True, exist_ok=True)


dataset = load_dataset(
    "bigcode/the-stack-dedup",
    data_dir="data/python",
    split="train",
    streaming=True,
)

def write_once(code: str, target_dir: Path) -> None:
    sha1 = hashlib.sha1(code.encode("utf-8")).hexdigest()
    path = target_dir / f"{sha1}.py"
    if not path.exists():
        with path.open("w", encoding="utf-8") as f:
            f.write(code)

for ex in tqdm(dataset, desc="Scanning The-Stack-dedup (Python)"):
    code = ex.get("content") or ""
    if not code:
        continue

    for lib, pats in FILTERS.items():
        if pats["import"].search(code) and pats["anim"].search(code):
            write_once(code, ROOT / lib)
            break           # stop at the first library that matches

print("✅ Finished.  Animation examples saved in", ROOT)

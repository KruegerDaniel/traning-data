import argparse
import hashlib
import json
import re
from pathlib import Path

from datasets import load_dataset
from tqdm.auto import tqdm

FILTERS = {
    "pyvista": {
        "import": re.compile(r"^\s*(?:from|import)\s+pyvista\b", re.I | re.M),
        "anim": re.compile(r"\.open_movie\s*\(", re.I),
    },
    "mayavi": {
        "import": re.compile(r"^\s*(?:from|import)\s+mayavi\b", re.I | re.M),
        "anim": re.compile(
            r"(mlab\.animate\s*\(|"
            r"for\s+\w+\s+in\s+.*(range|times?|frames?)\s*\()",
            re.I | re.S
        ),
    },
    "vtk": {
        "import": re.compile(r"^\s*(?:from|import)\s+vtk\b", re.I | re.M),
        "anim": re.compile(r"vtk(?:AVI|MP4)Writer", re.I),
    },
    "visit": {
        "import": re.compile(r"^\s*(?:from|import)\s+visit\b", re.I | re.M),
        "anim": re.compile(
            r"TimeSliderGetNStates\s*\(\s*\).*?for\s+\w+\s+in\s+range\(",
            re.I | re.S
        ),
    },
    "lottie": {
        "json_keys": {"v", "fr", "ip", "op", "layers"},  # Minimal Lottie signature
    }
}

ROOT = Path("../sampled").resolve()

def write_once(content: str, target_dir: Path, ext: str):
    sha1 = hashlib.sha1(content.encode("utf-8")).hexdigest()
    path = target_dir / f"{sha1}.{ext}"
    if not path.exists():
        with path.open("w", encoding="utf-8") as f:
            f.write(content)

def scan_python_files():
    for lib in FILTERS:
        if lib == "lottie":
            continue
        (ROOT / lib).mkdir(parents=True, exist_ok=True)

    dataset = load_dataset(
        "bigcode/the-stack-dedup",
        data_dir="data/python",
        split="train",
        streaming=True,
    )

    for ex in tqdm(dataset, desc="Scanning The-Stack-dedup (Python)"):
        code = ex.get("content") or ""
        if not code:
            continue

        for lib, pats in FILTERS.items():
            if lib == "lottie":
                continue
            if pats["import"].search(code) and pats["anim"].search(code):
                write_once(code, ROOT / lib, "py")
                break

def scan_json_files():
    (ROOT / "lottie").mkdir(parents=True, exist_ok=True)

    dataset = load_dataset(
        "bigcode/the-stack-dedup",
        data_dir="data/json",
        split="train",
        streaming=True,
    )

    for ex in tqdm(dataset, desc="Scanning The-Stack-dedup (JSON)"):
        text = ex.get("content") or ""
        if not text:
            continue

        try:
            data = json.loads(text)
        except Exception:
            continue

        if isinstance(data, dict) and FILTERS["lottie"]["json_keys"].issubset(data.keys()):
            write_once(text, ROOT / "lottie", "json")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--type", choices=["python", "json"], default="python",
        help="Choose the animation type to filter"
    )
    args = parser.parse_args()

    if args.type == "python":
        scan_python_files()
    elif args.type == "json":
        scan_json_files()

    print("✅ Finished. Animation examples saved in", ROOT)

if __name__ == "__main__":
    main()

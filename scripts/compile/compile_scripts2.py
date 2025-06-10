import re
import subprocess
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.compile.compile_matplotlib import run_matplot_script

SCRIPT_DIR = Path(__file__).parent.resolve()
PROJECT_ROOT = SCRIPT_DIR.parent.parent

SCRIPTS_DIR = PROJECT_ROOT / "sampled" / "matplotlib_fixed"
OUTPUT_DIR = PROJECT_ROOT / "rendered" / "manim_scenes"
MANIM_MEDIA_DIR = PROJECT_ROOT / "media" / "videos"
ERR_DIR = PROJECT_ROOT / "err" / "manim_scenes"
Path(ERR_DIR).mkdir(parents=True, exist_ok=True)

TIMEOUT = 120  # seconds


def extract_imports(code):
    imports = re.findall(r'^\s*(?:from\s+([a-zA-Z_][\w\.]*)|import\s+([a-zA-Z_][\w\.]*))', code, re.MULTILINE)
    modules = {imp.split('.')[0] for pair in imports for imp in pair if imp}

    return modules


def install_dependencies(modules):
    for mod in modules:
        if mod in sys.stdlib_module_names:
            continue
        try:
            print(f"📦 Installing: {mod}")
            subprocess.check_call([sys.executable, "-m", "pip", "install", mod])
        except Exception as e:
            print(f"⚠️ Failed to install {mod}: {e}")


def main():
    start_time = time.time()
    Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)
    Path(ERR_DIR).mkdir(parents=True, exist_ok=True)

    py_files = list(Path(SCRIPTS_DIR).glob("example_*.py"))

    for py_file in py_files:
        try:

            code = py_file.read_text(encoding="utf-8")

            # Skip large files
            # if len(code.splitlines()) > 500:
            #     print(f"❌ Skipping {py_file} due to excessive lines.")
            #     break

            try:
                modules = extract_imports(code)
                install_dependencies(modules)
                run_matplot_script(py_file, TIMEOUT)
            except Exception as e:
                print(f"⚠️ Error extracting imports from {py_file}: {e}")
                break

        except Exception as e:
            print(f"❌ Fatal error processing {py_file}: {e}")

    end_time = time.time()
    print(f"⏰ Total time taken: {end_time - start_time:.2f} seconds, files processed: {len(py_files)}")


if __name__ == "__main__":
    main()

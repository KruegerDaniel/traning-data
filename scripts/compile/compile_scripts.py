import re
import subprocess
import sys
import time
from pathlib import Path

from scripts.compile.compille_matplotlib import run_matplot_script, patch_script_for_mp4
from scripts.compile.compile_manim import run_manim_script
from scripts.config import PY_KEYWORDS

library_type = sys.argv[1] if len(sys.argv) > 1 else None
if not library_type or library_type not in PY_KEYWORDS.keys():
    raise ValueError(f"Invalid datatype. Choose from {PY_KEYWORDS.keys()}.")

SCRIPT_DIR = Path(__file__).parent.resolve()
PROJECT_ROOT = SCRIPT_DIR.parent.parent

SCRIPTS_DIR = PROJECT_ROOT / "sampled" / library_type
OUTPUT_DIR = PROJECT_ROOT / "rendered" / library_type
ERR_DIR = PROJECT_ROOT / "err" / library_type
Path(ERR_DIR).mkdir(parents=True, exist_ok=True)

TIMEOUT = 120  # seconds

def extract_imports(code):
    imports = re.findall(r'^\s*(?:from\s+([a-zA-Z_][\w\.]*)|import\s+([a-zA-Z_][\w\.]*))', code, re.MULTILINE)
    modules = {imp.split('.')[0] for pair in imports for imp in pair if imp}

    # Remove known Manim-related import issue
    modules.discard("manimlib")
    modules.discard("manimgl")
    modules.discard("manim_rubikscube")
    return modules

def install_dependencies(modules):
    for mod in modules:
        if mod in {"matplotlib", "numpy", "os", "sys", "re", "shutil", "time", "pathlib"}:
            continue
        try:
            print(f"📦 Installing: {mod}")
            subprocess.check_call([sys.executable, "-m", "pip", "install", mod])
        except Exception as e:
            print(f"⚠️ Failed to install {mod}: {e}")

def main():
    start_time = time.time()
    Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)
    py_files = list(Path(SCRIPTS_DIR).glob("example_*.py"))
    for py_file in py_files:
        try:
            code = py_file.read_text(encoding="utf-8")
            modules = extract_imports(code)
            install_dependencies(modules)

            if library_type == "matplotlib":
                temp_script = py_file.with_name(py_file.stem + "_temp.py")
                output_mp4 = str(Path(OUTPUT_DIR) / (py_file.stem + ".mp4"))

                patch_script_for_mp4(py_file, temp_script, output_mp4)
                run_matplot_script(py_file, temp_script)
                temp_script.unlink(missing_ok=True)
            elif library_type == "manim":
                pattern = r'class\s+([A-Za-z_][\w]*)\s*\(\s*Scene\s*\)'
                scene_classes = re.findall(pattern, code)
                if not scene_classes:
                    print(f"❌ No Manim scene classes found in {py_file}. Skipping.")
                    continue
                for scene in scene_classes:
                    run_manim_script(str(py_file), scene)


        except Exception as e:
            print(f"❌ Error processing {py_file}: {e}")
    end_time = time.time()
    elapsed_time = end_time - start_time
    print(f"⏰ Total time taken: {elapsed_time:.2f} seconds, files processed: {len(py_files)}")

if __name__ == "__main__":
    main()
    #rename_manim_files()
import re
import subprocess
import sys
import time
from pathlib import Path

from scripts.compile.code_fixer import fix_code
from scripts.compile.rename import rename_manim_files

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.compile.compile_matplotlib import run_matplot_script, patch_script_for_mp4
from scripts.compile.compile_manim import run_manim_script
from scripts.config import PY_KEYWORDS

library_type = sys.argv[1] if len(sys.argv) > 1 else None
if not library_type or library_type not in PY_KEYWORDS.keys():
    raise ValueError(f"Invalid datatype. Choose from {PY_KEYWORDS.keys()}.")

SCRIPT_DIR = Path(__file__).parent.resolve()
PROJECT_ROOT = SCRIPT_DIR.parent.parent

SCRIPTS_DIR = PROJECT_ROOT / "sampled" / "manim_scenes"
OUTPUT_DIR = PROJECT_ROOT / "rendered" / "manim_scenes"
MANIM_MEDIA_DIR = PROJECT_ROOT / "media" / "videos"
ERR_DIR = PROJECT_ROOT / "err" / "manim_scenes"
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
            retry = True
            fix_attempted = False
            while retry:
                retry = False

                code = py_file.read_text(encoding="utf-8")

                # Skip large files
                if len(code.splitlines()) > 500:
                    print(f"❌ Skipping {py_file} due to excessive lines.")
                    break

                try:
                    modules = extract_imports(code)
                    install_dependencies(modules)

                    scene_classes = re.findall(r'class\s+([A-Za-z_][\w]*)\s*\(\s*Scene\s*\)', code)
                    if not scene_classes:
                        print(f"❌ No Manim scene classes found in {py_file}. Skipping.")
                        break

                    for scene in scene_classes:
                        err = run_manim_script(str(py_file), scene, timeout=TIMEOUT, err_dir=ERR_DIR)
                        if err:
                            print(f"❌ Error in {py_file} for scene {scene}: {err}")
                            err_path = ERR_DIR / f"{py_file.stem}_{scene}.txt"
                            err_path.write_text(f"Error in {py_file} for scene {scene}:\n{err}", encoding="utf-8")

                            if not fix_attempted:
                                fix_code(py_file, err)
                                fix_attempted = True
                                retry = True
                                break  # retry from top of while-loop
                            else:
                                print(f"🛑 Already attempted fix for {py_file}. Skipping.")
                                break  # skip further retries

                        else:
                            print(f"✅ Successfully processed {py_file} for scene {scene}.")

                except Exception as scene_exception:
                    print(f"❌ Unexpected error in {py_file}: {scene_exception}")
                    if not fix_attempted:
                        fix_code(py_file, str(scene_exception))
                        fix_attempted = True
                        retry = True
                    else:
                        print(f"🛑 Already attempted fix for {py_file}. Skipping.")
                        break

        except Exception as e:
            print(f"❌ Fatal error processing {py_file}: {e}")

    end_time = time.time()
    print(f"⏰ Total time taken: {end_time - start_time:.2f} seconds, files processed: {len(py_files)}")


if __name__ == "__main__":
    main()
    rename_manim_files(input_dir=MANIM_MEDIA_DIR,output_dir=OUTPUT_DIR)
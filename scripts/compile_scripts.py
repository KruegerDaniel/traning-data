import subprocess
import sys
import time
from pathlib import Path
import re
import shutil

from rename import rename_manim_files

library_type = sys.argv[1] if len(sys.argv) > 1 else None
if not library_type or library_type not in ["manim", "matplotlib", "tikz"]:
    raise ValueError("Invalid datatype. Choose from 'tex', 'md', or 'js'.")

SCRIPTS_DIR = f"./sampled/{library_type}"
OUTPUT_DIR = f"./rendered/{library_type}"
ERR_DIR = f"./err/{library_type}"
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

def patch_script_for_mp4(py_path, temp_path, output_mp4):
    code = py_path.read_text(encoding="utf-8")

    anim_assign = re.search(r'(\w+)\s*=\s*animation\.FuncAnimation', code)
    anim_var = anim_assign.group(1) if anim_assign else "ani"

    code = re.sub(r'plt\.show\s*\(\s*\)', '', code)

    save_code = f"""
import matplotlib
matplotlib.use("Agg")
try:
    {anim_var}.save(r"{output_mp4}", writer='ffmpeg', fps=30)
    print("✅ Saved MP4: {output_mp4}")
except Exception as e:
    print("❌ Animation save failed:", e)
"""
    code = code.rstrip() + "\n" + save_code

    temp_path.write_text(code, encoding="utf-8")

def run_matplot_script(py_path, temp_path):
    try:
        print(f"▶️ Running: {temp_path.name}")
        result = subprocess.run(
            [sys.executable, str(temp_path)],
            capture_output=True,
            text=True,
            timeout=TIMEOUT
        )
        print("✅ STDOUT:")
        print(result.stdout)
        print("⚠️ STDERR:")
        print(result.stderr)
    except subprocess.TimeoutExpired:
        print(f"⏱ Timeout: {temp_path} took too long.")
    except Exception as e:
        print(f"❌ Error running {temp_path}: {e}")

def run_manim_script(filepath, scene_name):
    file_stem = Path(filepath).stem
    err_path = Path(ERR_DIR) / file_stem

    print(f"\n🎬 Running: manim -ql {filepath} {scene_name}")
    try:
        result = subprocess.run(
            [
                "manim",
                "-ql",  # low quality
                filepath,
                scene_name
            ],
            capture_output=True,
            text=True,
            timeout=TIMEOUT
        )
        print("✅ STDOUT:")
        print(result.stdout)
        print("⚠️ STDERR:")
        print(result.stderr)

        if result.returncode != 0:
            err_msg = result.stderr if result.stderr is not None else "(No stderr output)"
            err_path.write_text(f'Running: manim -ql {filepath} {scene_name}\n {err_msg}', encoding="utf-8")
            print(f"❌ Saved error log to {err_path}")
    except subprocess.TimeoutExpired as ex:
        print(f"⏱ Timeout: {filepath} > {scene_name} took too long.")
        err_path.write_text(str(ex), encoding="utf-8")
        print(f"❌ Saved timeout error log to {err_path}")
    except Exception as e:
        print(f"❌ Error running Manim on {filepath}: {e}")
        err_path.write_text(f'Running: manim -ql {filepath} {scene_name}\n {result.stderr}', encoding="utf-8")
        print(f"❌ Saved exception log to {err_path}")

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
    rename_manim_files()
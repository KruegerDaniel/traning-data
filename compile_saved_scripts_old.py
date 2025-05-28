import subprocess
import sys
import time
from pathlib import Path
import re
import shutil

SCRIPTS_DIR = "python"
TIMEOUT = 120  # seconds

def extract_scene_classes(code):
    """
    Extract class names inheriting from Scene (e.g., `class MyScene(Scene):`)
    """
    pattern = r'class\s+([A-Za-z_][\w]*)\s*\(\s*Scene\s*\)'
    return re.findall(pattern, code)

def extract_imports(code):
    imports = re.findall(r'^\s*(?:from\s+([a-zA-Z_][\w\.]*)|import\s+([a-zA-Z_][\w\.]*))', code, re.MULTILINE)
    modules = {imp.split('.')[0] for pair in imports for imp in pair if imp}
    modules.discard("manimlib")
    modules.discard("manimgl")
    modules.discard("manim_rubikscube")
    return modules

def install_dependencies(modules):
    for mod in modules:
        try:
            print(f"📦 Installing: {mod}")
            subprocess.check_call([sys.executable, "-m", "pip", "install", mod])
        except Exception as e:
            print(f"⚠️ Failed to install {mod}: {e}")

def move_rendered_output(stem):
    src_dir = Path("media/videos") / stem / "480p15" / f"{stem}.mp4"
    dest_file = Path("rendered") / f"{stem}.mp4"
    if src_dir.exists():
        shutil.move(str(src_dir), str(dest_file))
        print(f"📁 Moved to: {dest_file}")

def run_manim_script(filepath, scene_name):
    file_stem = Path(filepath).stem  # e.g., "example_0"
    output_path = f"rendered/{file_stem}"  # no extension; Manim adds .mp4

    print(f"\n🎬 Running: manim -ql {filepath} {scene_name} -> {output_path}.mp4")
    try:
        result = subprocess.run(
            [
                "manim",
                "-ql",  # low quality
                filepath,
                scene_name     # put media files under /rendered  # set output file name
            ],
            capture_output=True,
            text=True,
            timeout=TIMEOUT
        )
        print("✅ STDOUT:")
        print(result.stdout)
        print("⚠️ STDERR:")
        print(result.stderr)
    except subprocess.TimeoutExpired:
        print(f"⏱ Timeout: {filepath} > {scene_name} took too long.")
    except Exception as e:
        print(f"❌ Error running Manim on {filepath}: {e}")

def main():
    start_time = time.time()
    Path("rendered").mkdir(exist_ok=True)
    py_files = Path(SCRIPTS_DIR).glob("example_*.py")
    for py_file in py_files:
        try:
            code = py_file.read_text(encoding="utf-8")
            modules = extract_imports(code)
            install_dependencies(modules)
            scene_classes = extract_scene_classes(code)

            if not scene_classes:
                print(f"⚠️ No Scene classes found in {py_file}")
                continue

            for scene in scene_classes:
                run_manim_script(str(py_file), scene)
                #move_rendered_output(py_file.stem)

        except Exception as e:
            print(f"❌ Error processing {py_file}: {e}")
    end_time = time.time()
    elapsed_time = end_time - start_time
    print(f"⏰ Total time taken: {elapsed_time:.2f} seconds, files processed: {len(list(py_files))}")

if __name__ == "__main__":
    main()

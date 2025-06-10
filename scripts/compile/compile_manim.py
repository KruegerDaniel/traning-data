import subprocess
from pathlib import Path


def run_manim_script(filepath, scene_name, timeout=120, err_dir=Path("err"), retry=True):
    file_stem = Path(filepath).stem
    err_path = Path(err_dir) / file_stem

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
            encoding="utf-8",
            timeout=timeout
        )
        print("✅ STDOUT:")
        print(result.stdout)
        print("⚠️ STDERR:")
        print(result.stderr)

        if result.returncode != 0:
            err_msg = result.stderr if result.stderr is not None else "(No stderr output)"
            err_path.write_text(f'Running: manim -ql {filepath} {scene_name}\n {err_msg}', encoding="utf-8")
            return err_msg

    except subprocess.TimeoutExpired as ex:
        print(f"⏱ Timeout: {filepath} > {scene_name} took too long.")
        return str(ex)
    except Exception as e:
        print(f"❌ Error running Manim on {filepath}: {e}")
        return result.stderr

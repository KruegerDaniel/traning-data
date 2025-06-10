import os
import re
import subprocess
import sys

def patch_script_for_mp4(py_path, temp_path, output_mp4):
    code = py_path.read_text(encoding="utf-8")

    # Insert backend setup at the very top
    code = 'import matplotlib\nmatplotlib.use("Agg")\n' + code

    anim_assign = re.search(r'(\w+)\s*=\s*animation\.FuncAnimation', code)
    anim_var = anim_assign.group(1) if anim_assign else "ani"

    code = re.sub(r'plt\.show\s*\(\s*\)', '', code)

    save_code = f"""
try:
    {anim_var}.save(r"{output_mp4}", writer='ffmpeg', fps=30)
    print("✅ Saved MP4: {output_mp4}")
except Exception as e:
    print("❌ Animation save failed:", e)
"""
    code = code.rstrip() + "\n" + save_code

    temp_path.write_text(code, encoding="utf-8")


def run_matplot_script(py_path, timeout=120):
    try:

        env = os.environ.copy()
        env["PYTHONIOENCODING"] = "utf-8"
        result = subprocess.run(
            [sys.executable, str(py_path)],
            capture_output=True,
            text=True,
            timeout=timeout,
            encoding="utf-8",
            errors="replace",
            env=env
        )
        print("✅ STDOUT:")
        print(result.stdout)
        print("⚠️ STDERR:")
        print(result.stderr)
    except subprocess.TimeoutExpired:
        print(f"⏱ Timeout: {py_path} took too long.")
    except Exception as e:
        print(f"❌ Error running {py_path}: {e}")

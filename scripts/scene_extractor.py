import os
import re

from scripts.compile.code_fixer import generate_extracted_scene

MANIM_DIR = "../sampled/manim"
OUTPUT_DIR = "../sampled/manim_scenes"
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)
#
for root, _, files in os.walk(MANIM_DIR):
    for f in files:
        if f.endswith(".py"):
            file_path = os.path.join(root, f)
            try:
                with open(file_path, 'r', encoding='utf-8') as file:
                    content = file.read()
                    scenes = re.findall(r'class\s+([A-Za-z_][\w]*)\s*\(\s*Scene\s*\)', content)
                    if not scenes:
                        print(f"No scenes found in {file_path}")
                        continue
                    if len(scenes) == 1:
                        scene_filename = f"{os.path.splitext(f)[0]}_{scene}.py"
                        scene_path = os.path.join(OUTPUT_DIR, scene_filename)
                        with open(scene_path, 'w', encoding='utf-8') as scene_file:
                            scene_file.write(scene_code)
                        continue
                    for scene in scenes:
                        scene_code = generate_extracted_scene(content, scene)

                        scene_code = content if scene_code == "No change needed" else scene_code
                        if scene_code:
                            scene_filename = f"{os.path.splitext(f)[0]}_{scene}.py"
                            scene_path = os.path.join(OUTPUT_DIR, scene_filename)
                            with open(scene_path, 'w', encoding='utf-8') as scene_file:
                                scene_file.write(scene_code)
                            print(f"Extracted scene '{scene}' to {scene_path}")

            except Exception as e:
                print(f"Error reading {file_path}: {e}")
                continue
import os
import shutil
import re

# Directories
base_dir = './media/videos'
rendered_dir = './rendered'
os.makedirs(rendered_dir, exist_ok=True)

# Regex to match "example_x" pattern
example_pattern = re.compile(r'^example_(\d+)$')

# Loop through all directories in base_dir
def rename_manim_files():
    for entry in os.listdir(base_dir):
        match = example_pattern.match(entry)
        if not match:
            continue

        example_name = entry
        example_index = match.group(1)
        source_dir = os.path.join(base_dir, example_name, '480p15')

        if not os.path.exists(source_dir):
            print(f"Skipping missing directory: {source_dir}")
            continue

        mp4_files = [f for f in os.listdir(source_dir) if f.lower().endswith('.mp4')]

        for j, filename in enumerate(mp4_files):
            old_path = os.path.join(source_dir, filename)
            new_filename = f'example_{example_index}_{j}.mp4'
            new_path = os.path.join(source_dir, new_filename)

            # Rename
            os.rename(old_path, new_path)
            print(f"Renamed: {old_path} -> {new_path}")

            # Move
            final_path = os.path.join(rendered_dir, new_filename)
            shutil.move(new_path, final_path)
            print(f"Moved: {new_path} -> {final_path}")

import os
import shutil
import re


def rename_manim_files(input_dir='./media/videos', output_dir ='./rendered'):
    # Directories
    os.makedirs(output_dir, exist_ok=True)

    example_pattern = re.compile(r'^example_(\d+)_.*$')
    for entry in os.listdir(input_dir):
        match = example_pattern.match(entry)
        if not match:
            continue

        example_name = entry
        example_index = match.group(1)
        source_dir = os.path.join(input_dir, example_name, '480p15')

        if not os.path.exists(source_dir):
            print(f"Skipping missing directory: {source_dir}")
            continue

        mp4_files = [f for f in os.listdir(source_dir) if f.lower().endswith('.mp4')]

        for j, filename in enumerate(mp4_files):
            old_path = os.path.join(source_dir, filename)
            new_filename = f'example_{example_index}_{filename}'
            new_path = os.path.join(source_dir, new_filename)

            # Rename
            os.rename(old_path, new_path)
            print(f"Renamed: {old_path} -> {new_path}")

            # Move
            final_path = os.path.join(output_dir, new_filename)
            shutil.move(new_path, final_path)
            print(f"Moved: {new_path} -> {final_path}")

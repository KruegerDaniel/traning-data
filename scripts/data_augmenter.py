import os
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed

from scripts.util.openai_request import generate

CUTOFF = 1000
MAX_WORKERS = 8

PROMPTS = {
    "matplotlib": """Please generate python source code that modifies parts of the following code to create the intended diagram/visuals. 
Ensure the code is compilable and includes only the required preamble statements. 
If any external files are referenced, please modify the code to avoid referencing external files and include the content directly. 
The output should consist solely of the code itself, without any supplementary text. 
Make sure the code uses matplotlib animation.
Make sure the code exports to mp4 format with {filename}_{animation_name}.mp4 as the filename.
Refer to the error message to see what went wrong during the initial compilation:
Filename:
""",
    "vpython": """Please generate python source code that modifies parts of the following code to create the intended diagram/visuals. 
Ensure the code is compilable and includes only the required preamble statements. 
If any external files are referenced, please modify the code to avoid referencing external files and include the content directly. 
The output should consist solely of the code itself, without any supplementary text. 
Make sure the code uses vpython animation.
Make sure the code exports to mp4 format with {filename}_{animation_name}.mp4 as the filename.
Refer to the error message to see what went wrong during the initial compilation:
Filename:
"""
}

def parse_args():
    parser = argparse.ArgumentParser(description="Process Python scripts with either matplotlib or vpython prompts.")
    parser.add_argument("--mode", choices=["matplotlib", "vpython"], required=True, help="Type of visualization to support")
    return parser.parse_args()

def process_file(file_path, prompt, output_dir):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
            num_lines = len(content.splitlines())
            if num_lines > CUTOFF:
                return f"Skipping {file_path} due to excessive lines ({num_lines} lines)."

            filename = os.path.splitext(os.path.basename(file_path))[0]
            revised_code = generate(prompt, content, filename=filename, model='gpt-4.1')

            if revised_code:
                output_path = os.path.join(output_dir, f"{filename}.py")
                with open(output_path, 'w', encoding='utf-8') as out_file:
                    out_file.write(revised_code)
                return f"Revised code written to {output_path}"
    except Exception as e:
        return f"Error processing {file_path}: {e}"

def get_all_python_files(input_dir):
    python_files = []
    for root, _, files in os.walk(input_dir):
        for f in files:
            if f.endswith(".py"):
                python_files.append(os.path.join(root, f))
    return python_files

def main():
    args = parse_args()

    input_dir = f"../sampled/{args.mode}"
    output_dir = f"../sampled/{args.mode}_fixed"
    prompt = PROMPTS[args.mode]

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    files = get_all_python_files(input_dir)

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(process_file, file, prompt, output_dir): file for file in files}
        for future in as_completed(futures):
            result = future.result()
            if result:
                print(result)

if __name__ == "__main__":
    main()

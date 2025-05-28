import os
from pathlib import Path

import anthropic
from dotenv import load_dotenv
load_dotenv()

api_key = os.getenv("ANTHROPIC_API_KEY")

ERR_DIR = "err"
SAMPLED_DIR = "sampled/manim"

Fix_prompt = """Please generate python source code that modifies parts of the following code to create
the intended diagram/visuals. Ensure the code is compilable and includes only the required
preamble statements. If any external files are referenced, please modify the code to
avoid referencing external files and include the content directly. The output should
consist solely of the code itself, without any supplementary text."""

# Number of errors in err
count_err = len([name for name in os.listdir(ERR_DIR) if os.path.isfile(os.path.join(ERR_DIR, name))])

err_info = {}
all_scripts = ""

err_files = Path(ERR_DIR).glob("*")
for err_file in err_files:
    if not err_file.is_file():
        continue

    file_name = err_file.name

    with open(err_file, "r", encoding="utf-8") as f:
        content = f.read()
        err_info[file_name] = {
            "char_length": len(content),
            "line_count": content.count('\n'),
        }
        all_scripts += content + "\n\n"

    script_path = Path(SAMPLED_DIR) / f"{file_name}.py"
    if script_path.is_file():
        with open(script_path, "r", encoding="utf-8") as f:
            script_content = f.read()
            err_info[file_name]["script_char_length"] = len(script_content)
            err_info[file_name]["script_line_count"] = script_content.count('\n')
            all_scripts += script_content + "\n\n"


all_scripts_with_prompt = all_scripts + (count_err * Fix_prompt + "\n\n")

client = anthropic.Anthropic(api_key=api_key)

response = client.messages.count_tokens(
    model="claude-opus-4-20250514",
    messages=[{
        "role": "user",
        "content": all_scripts_with_prompt
    }],
)
total_input_tokens_with_prompt = response.input_tokens
response = client.messages.count_tokens(
    model="claude-opus-4-20250514",
    messages=[{
        "role": "user",
        "content": all_scripts
    }],
)
total_input_tokens = response.input_tokens

print(f"Total errors found: {count_err}")
print(f"Total input tokens with prompt: {total_input_tokens_with_prompt}")
print(f"Total input tokens without prompt: {total_input_tokens}")
print(f"Estimated input token cost: ${total_input_tokens_with_prompt / 1_000_000 * 3} USD")
print(
    f"Assuming output tokens are equal to input tokens, "
    f"estimated output token cost: ${(total_input_tokens_with_prompt / 1_000_000 * 3) + (total_input_tokens/1_000_000 * 15)} USD")

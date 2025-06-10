from openai import OpenAI

from scripts.config import OPEN_AI_API_KEY

client = OpenAI(
    api_key=OPEN_AI_API_KEY
)


def fix_code(file_path: str, err_msg: str, model: str = "gpt-4.1"):
    """
    Fixes the code in the given file based on the error message using OpenAI's API.
    Then writes the fixed code back to the file.

    Args:
        file_path (str): Path to the Python file to fix.
        err_msg (str): Error message to guide the fixing process.
        model (str): OpenAI model to use for code fixing.

    """
    print(f"🔧 Fixing code in {file_path} based on error message")
    with open(file_path, 'r', encoding='utf-8') as f:
        code = f.read()

    prompt = f"""Please generate python source code that modifies parts of the following code to create the intended diagram/visuals. 
    Ensure the code is compilable and includes only the required preamble statements. 
    If any external files are referenced, please modify the code to avoid referencing external files and include the content directly. 
    The output should consist solely of the code itself, without any supplementary text. 
    Make sure the code uses manim, instead of manimlib or manimgl.
    Refer to the error message to see what went wrong during the initial compilation:

{err_msg}\n\nCode:\n{code}"""

    response = client.responses.create(
        model=model,
        input=[
            {"role": "user", "content": prompt}
        ],
        temperature=0.5,
    )

    fixed_code = response.output_text.replace('```python', '').replace('```', '').strip()
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(fixed_code)
    print(f"Fixed code written to {file_path}")

def generate_extracted_scene(code:str, scene_name:str, model: str = "gpt-4.1") -> str:
    """
    Generates a scene from the provided code using OpenAI's API.
    """
    prompt = f"""Please extract the {scene_name} scene from the following manim code. 
    If there is only one scene, respond with 'No change needed'.
    Ensure the extracted code is compilable and includes only the required preamble statements and helper methods. 
    The output should consist solely of the code itself, without any supplementary text.
    \nCode:\n{code}"""
    response = client.responses.create(
        model=model,
        input=[
            {"role": "user", "content": prompt}
        ],
        temperature=0.5,
    )
    extracted_code = response.output_text.replace('```python', '').replace('```', '').strip()
    return extracted_code
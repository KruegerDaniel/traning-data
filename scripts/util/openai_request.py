import os

from openai import OpenAI
from dotenv import load_dotenv
load_dotenv()
client = OpenAI(
    api_key=os.getenv("OPEN_AI_API_KEY")  # Replace with your OpenAI API key
)

token_usage = {
    "input_tokens": 0,
    "output_tokens": 0,
    "total_tokens": 0
}

def generate(prompt, content, filename, model = 'gpt-4.1'):
    response = client.responses.create(
        model=model,
        input=[
            {"role": "user", "content": prompt + filename + "\n\n" + content}
        ],
        temperature=0.5,
    )
    usage = response.usage
    token_usage["input_tokens"] += usage.input_tokens
    token_usage["output_tokens"] += usage.output_tokens
    token_usage["total_tokens"] += usage.total_tokens
    print(token_usage)
    extracted_code = response.output_text.replace('```python', '').replace('```', '').strip()
    return extracted_code
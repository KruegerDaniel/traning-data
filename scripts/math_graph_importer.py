import math
import os
import sys
import time

from datasets import load_dataset

from scripts.config import PY_KEYWORDS
from scripts.filters.library_filters import filter_example

library_type = sys.argv[1] if len(sys.argv) > 1 else None
if not library_type or library_type not in PY_KEYWORDS.keys():
    raise ValueError("Invalid datatype. Choose from 'tex', 'md', or 'js'.")

MAX_RESULTS = int(sys.argv[2]) if len(sys.argv) > 2 else math.inf

language_type = "tex" if library_type in ["tikz"] else "python"
dataset = load_dataset("bigcode/the-stack-dedup", data_dir=f"data/{language_type}", split="train", streaming=True)

def save_example(code: str, index: int, label: str) -> None:
    ext = "py" if label in PY_KEYWORDS.keys() else "tex"
    filename = f"../sampled/{label}/example_{index}.{ext}"
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    with open(filename, "w", encoding='utf-8') as f:
        f.write(code)
    print(f"Saved {filename}")

# ========= Main Loop =========
saved_count = 0
label_indices = {}

start_time = time.time()
for i, example in enumerate(dataset):
    result = filter_example(example)
    if result:
        label, code = result
        if label not in label_indices:
            label_indices[label] = 0
        save_example(code, label_indices[label], label)
        label_indices[label] += 1
        saved_count += 1
        if saved_count > MAX_RESULTS:
            break

end_time = time.time()

# Format time to HH:MM:SS
def format_time(seconds: int) -> str:
    hours, remainder = divmod(seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours:02}:{minutes:02}:{seconds:02}"


print(f"Saved {saved_count} examples in {format_time(int(end_time - start_time))}")

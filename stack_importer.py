from datasets import load_dataset
import os
import sys

datatype = sys.argv[1] if len(sys.argv) > 1 else "tex"
if datatype not in ["tex", "md", "js"]:
    raise ValueError("Invalid datatype. Choose from 'tex', 'md', or 'js'.")

max_len = sys.argv[2] if len(sys.argv) > 2 else 10

tex_dataset = load_dataset("bigcode/the-stack-dedup", data_dir="data/tex", split="train", streaming=True)
md_dataset = load_dataset("bigcode/the-stack-dedup", data_dir="data/markdown", split="train", streaming=True)
js_dataset = load_dataset("bigcode/the-stack-dedup", data_dir="data/javascript", split="train", streaming=True)
# More potential datasets:
# rmarkdown rmd
# jupyter notebook ipynb
# revealjs html html

# Filters
beamer_slides = tex_dataset.filter(lambda x: "\\documentclass{beamer}" in x.get("content", ""))
reveal_slides = js_dataset.filter(lambda x: "reveal.js" in x.get("content", "") or "Reveal.initialize" in x.get("content", ""))
marp_slides = md_dataset.filter(lambda x: "marp:" in x.get("content", ""))

# Take and print 3 examples safely
if datatype == "tex":
    dataset = beamer_slides
elif datatype == "md":
    dataset = marp_slides
elif datatype == "js":
    dataset = reveal_slides
else:
    raise ValueError("Invalid datatype. Choose from 'tex', 'md', or 'js'.")

for i, example in enumerate(dataset):
    print(f"\n--- Example {i} ---")
    print("Content preview:\n", example["content"][:1000])
    filename = f"{datatype}/example{i}.{datatype}"
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    with open(filename, "w", encoding='utf-8') as f:
        f.write(example["content"])
    if i >= max_len:
        break
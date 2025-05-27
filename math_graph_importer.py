import os
import re
import sys
import time
from collections import Counter

from datasets import load_dataset
from fast_langdetect import detect_language

ACCEPTED_LANGUAGES = ["EN", "JA"]
# filter keywords
PY_KEYWORDS = {
    "manim": [
        "from manim import",
        "import manim",
        # "from manimlib import",
        # "import manimlib",
    ],
    "matplotlib": [
        "import matplotlib.animation",
        "from matplotlib.animation"
    ],
    "tikz": [
        r"\usepackage{tikz}",
        r"\usepackage{animate}",
        r"\begin{animateinline}",
        r"\begin{tikzpicture}"
    ]
}

library_type = sys.argv[1] if len(sys.argv) > 1 else None
if not library_type or library_type not in PY_KEYWORDS.keys():
    raise ValueError("Invalid datatype. Choose from 'tex', 'md', or 'js'.")

language_type = "python" if library_type in ["manim", "matplotlib"] else "tex"
dataset = load_dataset("bigcode/the-stack-dedup", data_dir=f"data/{language_type}", split="train", streaming=True)

# ========= Language Filter Function =========

def extract_comments_and_strings(code: str) -> list[str]:
    pattern = r"(#.*?$|\"\"\".*?\"\"\"|'''.*?'''|\".*?\"|'.*?')"
    matches = re.findall(pattern, code, re.DOTALL | re.MULTILINE)

    # Combine and clean
    combined_text = " ".join(matches)
    cleaned_text = re.sub(r"[\n'#\"\\]", " ", combined_text)
    cleaned_text = re.sub(r"\s+", " ", cleaned_text).strip()
    return cleaned_text.split()


def detect_language_sliding_window(words: list, window_size: int = 10, step: int = 5) -> str:
    """
    Slide a window over the words list and detect language for each window.
    Return the majority-vote language.
    """
    if len(words) < window_size:
        snippet = " ".join(words)
        return detect_language(snippet, low_memory=False).upper()

    lang_counts = Counter()
    for k in range(0, len(words) - window_size + 1, step):
        snippet = " ".join(words[k:k + window_size])
        try:
            lang = detect_language(snippet, low_memory=False).upper()
            lang_counts[lang] += 1
        except Exception as e:
            print(f"Error detecting language in sliding window: {e}")

        if not lang_counts:
            return "UNKNOWN"
    # Get the most common language
    most_common_lang, _ = lang_counts.most_common(1)[0]
    return most_common_lang


def is_accepted_language(code_text: str) -> bool:
    words = extract_comments_and_strings(code_text)
    detected_lang = detect_language_sliding_window(words)
    print(f"Detected language: {detected_lang}")
    return detected_lang in ACCEPTED_LANGUAGES


# ========= Logic Filters =========
def manim_filter(code: str) -> bool:
    blacklisted_keywords = [
        "manimgl", "manim_rubikscube", "manimlib",
    ]
    # Check for blacklisted keywords
    if any(kw in code for kw in blacklisted_keywords):
        return False

    # Require animation
    if "self.play(" not in code:
        return False

    if "from manim_ml.neural_network" in code:
        return True

    # List of visual object types considered "non-text"
    visual_mobjects = [
        "Circle", "Square", "Rectangle", "Polygon", "Line", "Dot", "Arrow", "Ellipse",
        "Arc", "RegularPolygon", "Annulus", "Sector", "Triangle", "ImageMobject",
        "SVGMobject", "Axes", "NumberPlane", "Graph", "BarChart", "Table", "Brace"
    ]

    # Regex to match object creation lines
    creation_pattern = re.compile(r'(\w+)\s*=\s*(\w+)\s*\(')
    found_visual = False

    # Scan through code, line by line
    for line in code.splitlines():
        line = line.replace('\t', '')
        m = creation_pattern.search(line)
        if m:
            class_name = m.group(2)
            if class_name in visual_mobjects:
                found_visual = True
                break  # No need to keep checking if we find one

    # If any non-text visual found, keep the script
    return found_visual


def matplotlib_filter(code: str) -> bool:
    if "plt.show()" not in code:
        return False
    return False

def tikz_animation_filter(code: str) -> bool:
    has_tikz = r"\usepackage{tikz}" in code
    has_animate = r"\usepackage{animate}" in code
    has_animateinline = r"\begin{animateinline}" in code or r"\begin{animateinline" in code
    has_tikzpicture = r"\begin{tikzpicture}" in code
    return has_tikz and has_animate and has_animateinline and has_tikzpicture


# ========= Filter Function =========
def filter_example(example: dict):
    code = example.get("content", "")

    for library, keywords in PY_KEYWORDS.items():
        if any(kw in code for kw in keywords):
            if library == "manim" and not manim_filter(code):
                return None
            elif library == "matplotlib" and not matplotlib_filter(code):
                return None
            elif library == "tikz" and not tikz_animation_filter(code):
                return None

            print(f"Detected {library} code.")
            if is_accepted_language(code):
                return library, code

    return None


def save_example(code: str, index: int, label: str) -> None:
    ext = "py" if label in ["manim", "matplotlib"] else "tex"
    filename = f"./sampled/{label}/example_{index}.{ext}"
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    with open(filename, "w", encoding='utf-8') as f:
        f.write(code)
    print(f"Saved {filename}")


# ========= Main Loop =========
MAX_RESULTS = sys.argv[2] if len(sys.argv) > 1 else float("inf")
saved_count = 0

start_time = time.time()
for i, example in enumerate(dataset):
    result = filter_example(example)
    if result:
        label, code = result
        save_example(code, saved_count, label)
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

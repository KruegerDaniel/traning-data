import re
from collections import Counter

from fast_langdetect import detect_language

from scripts.config import ACCEPTED_LANGUAGES


def extract_comments_and_strings(code: str) -> list[str]:
    pattern = r"(#.*?$|\"\"\".*?\"\"\"|'''.*?'''|\".*?\"|'.*?')"
    matches = re.findall(pattern, code, re.DOTALL | re.MULTILINE)

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

    most_common_lang, _ = lang_counts.most_common(1)[0]
    return most_common_lang


def is_accepted_language(code_text: str) -> bool:
    words = extract_comments_and_strings(code_text)
    detected_lang = detect_language_sliding_window(words)
    print(f"Detected language: {detected_lang}")
    return detected_lang in ACCEPTED_LANGUAGES


import os

from dotenv import load_dotenv
from setuptools.package_index import EXTENSIONS

load_dotenv()

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
    "vpython": [
        "import vpython",
        "from vpython import",
        "from visual import",  # older VPython
        "import visual",
        "from vpython.no_notebook import",  # sometimes used in scripts
    ],
    "tikz": ["usetikzlibrary{animations}"],
    "svg": ["<animate>", "<animateTransform>", "<animateMotion>"],
}

EXTENSIONS = {
    "manim": ["py"],
    "matplotlib": ["py"],
    "vpython": ["py"],
    "tikz": ["tex"],
    "svg": ["svg"]
}

OPEN_AI_API_KEY = os.getenv("OPEN_AI_API_KEY")

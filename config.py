
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
    ]
}
#
# "tikz": [
#         r"\usepackage{tikz}",
#         r"\usepackage{animate}",
#         r"\begin{animateinline}",
#         r"\begin{tikzpicture}"
#     ],
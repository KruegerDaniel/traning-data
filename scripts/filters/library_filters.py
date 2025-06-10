# ========= Logic Filters =========
import re

from scripts.config import PY_KEYWORDS
from scripts.filters.language_filters import is_accepted_language


def manim_filter(code: str) -> bool:
    blacklisted_keywords = [
        "manimgl", "manim_rubikscube", "manimlib",
    ]
    if any(kw in code for kw in blacklisted_keywords):
        return False

    if "self.play(" not in code:
        return False

    if "from manim_ml.neural_network" in code:
        return True

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
                break

    return found_visual


def matplotlib_filter(code: str) -> bool:
    animation_import = re.search(r"from\s+matplotlib\.animation\s+import|import\s+matplotlib\.animation", code)
    animation_call = re.search(r"(FuncAnimation|ArtistAnimation)\s*\(", code)

    # Detect showing or exporting
    has_show = "plt.show()" in code or "show(" in code

    has_save = re.search(r"\.\s*save\s*\(", code) is not None

    return (animation_import or animation_call) and (has_show or has_save)


def tikz_animation_filter(code: str) -> bool:
    has_tikzpicture = r"\begin{tikzpicture}" in code or r"\end{tikzpicture}" in code

    animation_patterns = [
        r"\\begin\{animateinline(?:\[.*?\])?\}",
        r"\\animategraphics",
        r"\\multiframe",
        r"\\usepackage\{animate\}",
    ]

    has_animation = any(re.search(pattern, code) for pattern in animation_patterns)

    return has_tikzpicture and has_animation


def vpython_filter(code: str) -> bool:
    if not any(imp in code for imp in [
        "import vpython", "from vpython import", "import visual", "from visual import"
    ]):
        return False

    vpy_objects = [
        "sphere(", "box(", "curve(", "cylinder(", "cone(", "pyramid(", "arrow(", "ellipsoid(",
        "ring(", "helix(", "label(", "points("
    ]
    animation_patterns = [
        r"rate\s*\(",
        r".animate\s*\(",
    ]
    has_object = any(obj in code for obj in vpy_objects)
    has_animation = any(re.search(pat, code) for pat in animation_patterns)
    has_loop = re.search(r"\bwhile\b|\bfor\b", code) is not None
    return has_object and (has_animation or has_loop)


# ========= Filter Function =========
def filter_example(example: dict):
    code = example.get("content", "")

    for library, keywords in PY_KEYWORDS.items():
        if any(kw in code for kw in keywords):
            if library == "manim" and not manim_filter(code):
                return None
            elif library == "matplotlib" and not matplotlib_filter(code):
                return None
            elif library == "vpython" and not vpython_filter(code):
                return None
            # elif library == "tikz" and not tikz_animation_filter(code):
            #     return None

            print(f"Detected {library} code.")
            if is_accepted_language(code):
                return library, code

    return None

"""
Visual styles for PDF generation.

Defines LaTeX configurations for different document styles.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


StyleType = Literal["default", "academic", "modern", "minimal"]


@dataclass
class StyleConfig:
    """Configuration for a PDF style."""

    name: str
    description: str
    font_family: str  # serif, sans-serif
    header_color: str  # LaTeX color
    link_color: str
    margin: str  # e.g., "2.5cm"
    line_spacing: float
    header_style: str  # LaTeX header configuration
    packages: list[str]  # Additional LaTeX packages


STYLES: dict[str, StyleConfig] = {
    "default": StyleConfig(
        name="default",
        description="Classic style with serif font (Computer Modern)",
        font_family="serif",
        header_color="000000",  # Black (hex)
        link_color="0000FF",  # Blue (hex)
        margin="2.5cm",
        line_spacing=1.15,
        header_style="",
        packages=[],
    ),
    "academic": StyleConfig(
        name="academic",
        description="Academic style with section numbering and headers",
        font_family="serif",
        header_color="000000",  # Black (hex)
        link_color="1a1a80",  # Dark blue (hex)
        margin="2.5cm",
        line_spacing=1.5,
        header_style=r"\usepackage{fancyhdr}\pagestyle{fancy}\fancyhead[L]{\leftmark}\fancyhead[R]{\thepage}",
        packages=["fancyhdr", "setspace"],
    ),
    "modern": StyleConfig(
        name="modern",
        description="Modern style with sans-serif font and colors",
        font_family="sans-serif",
        header_color="2563eb",  # Modern blue (hex)
        link_color="0d9488",  # Teal (hex)
        margin="2cm",
        line_spacing=1.2,
        header_style=r"\usepackage{fancyhdr}\pagestyle{fancy}\fancyhead{}\fancyfoot[C]{\thepage}",
        packages=["helvet", "fancyhdr", "xcolor"],
    ),
    "minimal": StyleConfig(
        name="minimal",
        description="Minimal style with wide margins and clean design",
        font_family="serif",
        header_color="000000",  # Black (hex)
        link_color="333333",  # Dark gray (hex)
        margin="3.5cm",
        line_spacing=1.3,
        header_style=r"\pagestyle{empty}",
        packages=[],
    ),
}


def get_style_config(style_name: StyleType = "default") -> StyleConfig:
    """
    Get the configuration for a style.

    Args:
        style_name: Name of the style

    Returns:
        StyleConfig for the requested style
    """
    return STYLES.get(style_name, STYLES["default"])


def get_style_latex_header(style: StyleConfig) -> str:
    """
    Generate LaTeX header configuration for a style.

    Args:
        style: The style configuration

    Returns:
        LaTeX header commands as a string
    """
    lines = []

    # Font family
    if style.font_family == "sans-serif":
        lines.append(r"\renewcommand{\familydefault}{\sfdefault}")

    # Colors (using HTML hex format)
    lines.append(r"\usepackage{xcolor}")
    lines.append(rf"\definecolor{{headercolor}}{{HTML}}{{{style.header_color}}}")
    lines.append(rf"\definecolor{{linkcolor}}{{HTML}}{{{style.link_color}}}")

    # Hyperref for links
    lines.append(r"\usepackage{hyperref}")
    lines.append(r"\hypersetup{colorlinks=true,linkcolor=linkcolor,urlcolor=linkcolor}")

    # Line spacing
    if style.line_spacing != 1.0:
        lines.append(r"\usepackage{setspace}")
        lines.append(rf"\setstretch{{{style.line_spacing}}}")

    # Header style
    if style.header_style:
        lines.append(style.header_style)

    # Additional packages
    for pkg in style.packages:
        if pkg not in ["fancyhdr", "setspace", "xcolor", "helvet"]:  # Avoid duplicates
            lines.append(rf"\usepackage{{{pkg}}}")

    return "\n".join(lines)


def get_style_info() -> dict[str, dict[str, str]]:
    """
    Get information about all available styles.

    Returns:
        Dictionary mapping style names to their descriptions
    """
    return {name: {"description": style.description} for name, style in STYLES.items()}

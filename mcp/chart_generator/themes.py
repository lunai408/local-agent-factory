"""
Color themes for chart generation.

Provides predefined color palettes compatible with matplotlib and seaborn.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend - MUST be before pyplot import

import matplotlib.pyplot as plt
import seaborn as sns


ThemeType = Literal[
    "default", "dark", "light", "colorblind", "pastel", "bold", "monochrome"
]


@dataclass
class ThemeConfig:
    """Configuration for a chart theme."""

    name: str
    description: str
    style: str  # matplotlib/seaborn style
    palette: str | list[str]  # seaborn palette name or list of colors
    background: str
    text_color: str
    grid_color: str
    grid_alpha: float


THEMES: dict[str, ThemeConfig] = {
    "default": ThemeConfig(
        name="default",
        description="Clean default theme with seaborn colors",
        style="seaborn-v0_8-whitegrid",
        palette="deep",
        background="#ffffff",
        text_color="#333333",
        grid_color="#cccccc",
        grid_alpha=0.7,
    ),
    "dark": ThemeConfig(
        name="dark",
        description="Dark background with vibrant colors",
        style="dark_background",
        palette="bright",
        background="#1a1a2e",
        text_color="#eaeaea",
        grid_color="#444444",
        grid_alpha=0.5,
    ),
    "light": ThemeConfig(
        name="light",
        description="Light background with soft colors",
        style="seaborn-v0_8-white",
        palette="muted",
        background="#fafafa",
        text_color="#444444",
        grid_color="#dddddd",
        grid_alpha=0.6,
    ),
    "colorblind": ThemeConfig(
        name="colorblind",
        description="Accessible palette for color vision deficiency",
        style="seaborn-v0_8-whitegrid",
        palette="colorblind",
        background="#ffffff",
        text_color="#333333",
        grid_color="#cccccc",
        grid_alpha=0.7,
    ),
    "pastel": ThemeConfig(
        name="pastel",
        description="Soft pastel colors",
        style="seaborn-v0_8-whitegrid",
        palette="pastel",
        background="#ffffff",
        text_color="#555555",
        grid_color="#dddddd",
        grid_alpha=0.6,
    ),
    "bold": ThemeConfig(
        name="bold",
        description="High contrast saturated colors",
        style="seaborn-v0_8-white",
        palette=[
            "#e63946",
            "#2a9d8f",
            "#264653",
            "#e9c46a",
            "#f4a261",
            "#9b5de5",
            "#00bbf9",
            "#00f5d4",
        ],
        background="#ffffff",
        text_color="#222222",
        grid_color="#cccccc",
        grid_alpha=0.5,
    ),
    "monochrome": ThemeConfig(
        name="monochrome",
        description="Grayscale shades for print-friendly charts",
        style="seaborn-v0_8-whitegrid",
        palette=[
            "#111111",
            "#333333",
            "#555555",
            "#777777",
            "#999999",
            "#bbbbbb",
            "#dddddd",
        ],
        background="#ffffff",
        text_color="#222222",
        grid_color="#cccccc",
        grid_alpha=0.6,
    ),
}


def apply_theme(theme_name: ThemeType = "default") -> ThemeConfig:
    """
    Apply a theme to matplotlib/seaborn.

    Args:
        theme_name: Name of the theme to apply

    Returns:
        The ThemeConfig that was applied
    """
    theme = THEMES.get(theme_name, THEMES["default"])

    # Try to use the style, fallback to default if not available
    try:
        plt.style.use(theme.style)
    except OSError:
        # Style not found, use default
        plt.style.use("seaborn-v0_8-whitegrid")

    # Set seaborn palette
    if isinstance(theme.palette, list):
        sns.set_palette(theme.palette)
    else:
        sns.set_palette(theme.palette)

    # Apply additional customizations
    plt.rcParams.update(
        {
            "figure.facecolor": theme.background,
            "axes.facecolor": theme.background,
            "axes.edgecolor": theme.grid_color,
            "axes.labelcolor": theme.text_color,
            "text.color": theme.text_color,
            "xtick.color": theme.text_color,
            "ytick.color": theme.text_color,
            "grid.color": theme.grid_color,
            "grid.alpha": theme.grid_alpha,
        }
    )

    return theme


def get_theme_info() -> dict[str, dict[str, str]]:
    """
    Get information about all available themes.

    Returns:
        Dictionary mapping theme names to their descriptions
    """
    return {name: {"description": theme.description} for name, theme in THEMES.items()}

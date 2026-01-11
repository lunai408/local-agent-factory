"""
Chart generation functions using matplotlib and seaborn.

Each function generates a specific type of chart and returns PNG bytes.
"""

from __future__ import annotations

import io
from dataclasses import dataclass, field
from typing import Any, Literal

import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend (no GUI windows)

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns

try:
    from .themes import ThemeType, apply_theme
except ImportError:
    from themes import ThemeType, apply_theme


ChartType = Literal[
    "scatter",
    "line",
    "bar",
    "barh",
    "histogram",
    "pie",
    "heatmap",
    "box",
    "violin",
    "area",
]

FormatType = Literal["square", "landscape", "portrait"]
QualityType = Literal["high", "medium", "low", "very_low"]


# Format ratios (width:height)
FORMAT_RATIOS = {
    "square": (1, 1),
    "landscape": (16, 9),
    "portrait": (9, 16),
}

# Quality sizes (longest edge in pixels, converted to inches at 100 DPI)
QUALITY_SIZES = {
    "high": 1024,
    "medium": 720,
    "low": 256,
    "very_low": 128,
}

DPI = 100  # Fixed DPI for consistent sizing


@dataclass
class ChartConfig:
    """Configuration for chart generation."""

    title: str = ""
    xlabel: str = ""
    ylabel: str = ""
    legend: list[str] = field(default_factory=list)
    theme: ThemeType = "default"
    format: FormatType = "square"
    quality: QualityType = "high"


# Chart type specifications
CHART_SPECS: dict[str, dict[str, Any]] = {
    "scatter": {
        "description": "Scatter plot showing relationships between two variables",
        "required": ["x", "y"],
        "optional": ["labels", "sizes", "colors"],
        "example": {"x": [1, 2, 3, 4, 5], "y": [2, 4, 1, 5, 3]},
    },
    "line": {
        "description": "Line plot for time series or continuous data",
        "required": ["x", "y"],
        "optional": [],
        "example": {
            "x": [1, 2, 3, 4, 5],
            "y": [2, 4, 6, 8, 10],
        },
        "note": "y can be a single list or list of lists for multiple lines",
    },
    "bar": {
        "description": "Vertical bar chart for categorical comparisons",
        "required": ["categories", "values"],
        "optional": [],
        "example": {"categories": ["A", "B", "C"], "values": [10, 20, 15]},
        "note": "values can be a single list or list of lists for grouped bars",
    },
    "barh": {
        "description": "Horizontal bar chart for categorical comparisons",
        "required": ["categories", "values"],
        "optional": [],
        "example": {"categories": ["A", "B", "C"], "values": [10, 20, 15]},
    },
    "histogram": {
        "description": "Distribution of numerical data",
        "required": ["values"],
        "optional": ["bins"],
        "example": {"values": [1, 2, 2, 3, 3, 3, 4, 4, 5], "bins": 10},
    },
    "pie": {
        "description": "Pie chart showing proportions of a whole",
        "required": ["labels", "values"],
        "optional": [],
        "example": {"labels": ["A", "B", "C"], "values": [30, 50, 20]},
    },
    "heatmap": {
        "description": "2D matrix visualization with color intensity",
        "required": ["data"],
        "optional": ["xlabels", "ylabels", "annot"],
        "example": {
            "data": [[1, 2, 3], [4, 5, 6], [7, 8, 9]],
            "xlabels": ["A", "B", "C"],
            "ylabels": ["X", "Y", "Z"],
        },
    },
    "box": {
        "description": "Box plot showing distribution statistics",
        "required": ["data"],
        "optional": ["labels"],
        "example": {
            "data": [[1, 2, 3, 4, 5], [2, 3, 4, 5, 6], [3, 4, 5, 6, 7]],
            "labels": ["Group A", "Group B", "Group C"],
        },
    },
    "violin": {
        "description": "Violin plot combining box plot with density estimation",
        "required": ["data"],
        "optional": ["labels"],
        "example": {
            "data": [[1, 2, 3, 4, 5], [2, 3, 4, 5, 6]],
            "labels": ["Group A", "Group B"],
        },
    },
    "area": {
        "description": "Stacked area chart for cumulative totals over time",
        "required": ["x", "y"],
        "optional": [],
        "example": {
            "x": [1, 2, 3, 4, 5],
            "y": [[1, 2, 3, 4, 5], [2, 3, 4, 5, 6]],
        },
    },
}


def calculate_figsize(
    format: FormatType = "square",
    quality: QualityType = "high",
) -> tuple[float, float]:
    """
    Calculate figure size in inches from format and quality.

    Args:
        format: Aspect ratio preset
        quality: Size preset

    Returns:
        Tuple of (width, height) in inches
    """
    ratio_w, ratio_h = FORMAT_RATIOS.get(format, (1, 1))
    max_pixels = QUALITY_SIZES.get(quality, 1024)

    if ratio_w >= ratio_h:
        width_px = max_pixels
        height_px = int(max_pixels * ratio_h / ratio_w)
    else:
        height_px = max_pixels
        width_px = int(max_pixels * ratio_w / ratio_h)

    return width_px / DPI, height_px / DPI


def figure_to_bytes(fig: plt.Figure) -> bytes:
    """Convert a matplotlib figure to PNG bytes."""
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=DPI, bbox_inches="tight", pad_inches=0.1)
    buf.seek(0)
    plt.close(fig)
    return buf.getvalue()


def create_scatter(data: dict[str, Any], config: ChartConfig) -> bytes:
    """Create a scatter plot."""
    apply_theme(config.theme)

    figsize = calculate_figsize(config.format, config.quality)
    fig, ax = plt.subplots(figsize=figsize)

    x = data["x"]
    y = data["y"]
    sizes = data.get("sizes")
    colors = data.get("colors")

    ax.scatter(x, y, s=sizes, c=colors, alpha=0.7)

    if config.title:
        ax.set_title(config.title)
    if config.xlabel:
        ax.set_xlabel(config.xlabel)
    if config.ylabel:
        ax.set_ylabel(config.ylabel)

    fig.tight_layout()
    return figure_to_bytes(fig)


def create_line(data: dict[str, Any], config: ChartConfig) -> bytes:
    """Create a line plot (single or multi-line)."""
    apply_theme(config.theme)

    figsize = calculate_figsize(config.format, config.quality)
    fig, ax = plt.subplots(figsize=figsize)

    x = data["x"]
    y = data["y"]

    # Check if y is multi-series (list of lists)
    if y and isinstance(y[0], list):
        for i, series in enumerate(y):
            label = config.legend[i] if i < len(config.legend) else f"Series {i + 1}"
            ax.plot(x, series, label=label, marker="o", markersize=4)
        if config.legend:
            ax.legend()
    else:
        label = config.legend[0] if config.legend else None
        ax.plot(x, y, label=label, marker="o", markersize=4)
        if label:
            ax.legend()

    if config.title:
        ax.set_title(config.title)
    if config.xlabel:
        ax.set_xlabel(config.xlabel)
    if config.ylabel:
        ax.set_ylabel(config.ylabel)

    fig.tight_layout()
    return figure_to_bytes(fig)


def create_bar(data: dict[str, Any], config: ChartConfig) -> bytes:
    """Create a vertical bar chart."""
    apply_theme(config.theme)

    figsize = calculate_figsize(config.format, config.quality)
    fig, ax = plt.subplots(figsize=figsize)

    categories = data["categories"]
    values = data["values"]

    # Check if values is multi-series
    if values and isinstance(values[0], list):
        x = np.arange(len(categories))
        n_series = len(values)
        width = 0.8 / n_series

        for i, series in enumerate(values):
            offset = (i - n_series / 2 + 0.5) * width
            label = config.legend[i] if i < len(config.legend) else f"Series {i + 1}"
            ax.bar(x + offset, series, width, label=label)

        ax.set_xticks(x)
        ax.set_xticklabels(categories)
        ax.legend()
    else:
        ax.bar(categories, values)

    if config.title:
        ax.set_title(config.title)
    if config.xlabel:
        ax.set_xlabel(config.xlabel)
    if config.ylabel:
        ax.set_ylabel(config.ylabel)

    fig.tight_layout()
    return figure_to_bytes(fig)


def create_barh(data: dict[str, Any], config: ChartConfig) -> bytes:
    """Create a horizontal bar chart."""
    apply_theme(config.theme)

    figsize = calculate_figsize(config.format, config.quality)
    fig, ax = plt.subplots(figsize=figsize)

    categories = data["categories"]
    values = data["values"]

    ax.barh(categories, values)

    if config.title:
        ax.set_title(config.title)
    if config.xlabel:
        ax.set_xlabel(config.xlabel)
    if config.ylabel:
        ax.set_ylabel(config.ylabel)

    fig.tight_layout()
    return figure_to_bytes(fig)


def create_histogram(data: dict[str, Any], config: ChartConfig) -> bytes:
    """Create a histogram."""
    apply_theme(config.theme)

    figsize = calculate_figsize(config.format, config.quality)
    fig, ax = plt.subplots(figsize=figsize)

    values = data["values"]
    bins = data.get("bins", 10)

    ax.hist(values, bins=bins, edgecolor="white", alpha=0.7)

    if config.title:
        ax.set_title(config.title)
    if config.xlabel:
        ax.set_xlabel(config.xlabel)
    if config.ylabel:
        ax.set_ylabel(config.ylabel)

    fig.tight_layout()
    return figure_to_bytes(fig)


def create_pie(data: dict[str, Any], config: ChartConfig) -> bytes:
    """Create a pie chart."""
    apply_theme(config.theme)

    figsize = calculate_figsize(config.format, config.quality)
    fig, ax = plt.subplots(figsize=figsize)

    labels = data["labels"]
    values = data["values"]

    ax.pie(values, labels=labels, autopct="%1.1f%%", startangle=90)
    ax.axis("equal")

    if config.title:
        ax.set_title(config.title)

    fig.tight_layout()
    return figure_to_bytes(fig)


def create_heatmap(data: dict[str, Any], config: ChartConfig) -> bytes:
    """Create a heatmap."""
    apply_theme(config.theme)

    figsize = calculate_figsize(config.format, config.quality)
    fig, ax = plt.subplots(figsize=figsize)

    matrix = np.array(data["data"])
    xlabels = data.get("xlabels")
    ylabels = data.get("ylabels")
    annot = data.get("annot", True)

    sns.heatmap(
        matrix,
        ax=ax,
        annot=annot,
        fmt=".2g",
        xticklabels=xlabels if xlabels else "auto",
        yticklabels=ylabels if ylabels else "auto",
        cmap="viridis",
    )

    if config.title:
        ax.set_title(config.title)
    if config.xlabel:
        ax.set_xlabel(config.xlabel)
    if config.ylabel:
        ax.set_ylabel(config.ylabel)

    fig.tight_layout()
    return figure_to_bytes(fig)


def create_box(data: dict[str, Any], config: ChartConfig) -> bytes:
    """Create a box plot."""
    apply_theme(config.theme)

    figsize = calculate_figsize(config.format, config.quality)
    fig, ax = plt.subplots(figsize=figsize)

    plot_data = data["data"]
    labels = data.get("labels")

    ax.boxplot(plot_data, labels=labels)

    if config.title:
        ax.set_title(config.title)
    if config.xlabel:
        ax.set_xlabel(config.xlabel)
    if config.ylabel:
        ax.set_ylabel(config.ylabel)

    fig.tight_layout()
    return figure_to_bytes(fig)


def create_violin(data: dict[str, Any], config: ChartConfig) -> bytes:
    """Create a violin plot."""
    apply_theme(config.theme)

    figsize = calculate_figsize(config.format, config.quality)
    fig, ax = plt.subplots(figsize=figsize)

    plot_data = data["data"]
    labels = data.get("labels")

    parts = ax.violinplot(plot_data, showmeans=True, showmedians=True)

    # Apply colors from palette
    palette = sns.color_palette()
    for i, pc in enumerate(parts["bodies"]):
        pc.set_facecolor(palette[i % len(palette)])
        pc.set_alpha(0.7)

    if labels:
        ax.set_xticks(range(1, len(labels) + 1))
        ax.set_xticklabels(labels)

    if config.title:
        ax.set_title(config.title)
    if config.xlabel:
        ax.set_xlabel(config.xlabel)
    if config.ylabel:
        ax.set_ylabel(config.ylabel)

    fig.tight_layout()
    return figure_to_bytes(fig)


def create_area(data: dict[str, Any], config: ChartConfig) -> bytes:
    """Create a stacked area chart."""
    apply_theme(config.theme)

    figsize = calculate_figsize(config.format, config.quality)
    fig, ax = plt.subplots(figsize=figsize)

    x = data["x"]
    y = data["y"]

    # Ensure y is a list of series
    if not isinstance(y[0], list):
        y = [y]

    labels = config.legend if config.legend else [f"Series {i + 1}" for i in range(len(y))]

    ax.stackplot(x, *y, labels=labels, alpha=0.7)

    if len(y) > 1 or config.legend:
        ax.legend(loc="upper left")

    if config.title:
        ax.set_title(config.title)
    if config.xlabel:
        ax.set_xlabel(config.xlabel)
    if config.ylabel:
        ax.set_ylabel(config.ylabel)

    fig.tight_layout()
    return figure_to_bytes(fig)


# Mapping of chart types to their creation functions
CHART_FUNCTIONS: dict[ChartType, callable] = {
    "scatter": create_scatter,
    "line": create_line,
    "bar": create_bar,
    "barh": create_barh,
    "histogram": create_histogram,
    "pie": create_pie,
    "heatmap": create_heatmap,
    "box": create_box,
    "violin": create_violin,
    "area": create_area,
}


def create_chart(
    chart_type: ChartType,
    data: dict[str, Any],
    config: ChartConfig,
) -> bytes:
    """
    Create a chart of the specified type.

    Args:
        chart_type: Type of chart to create
        data: Data for the chart (format depends on chart type)
        config: Chart configuration (title, labels, theme, etc.)

    Returns:
        PNG image bytes

    Raises:
        ValueError: If chart_type is not supported
    """
    if chart_type not in CHART_FUNCTIONS:
        raise ValueError(
            f"Unsupported chart type: {chart_type}. "
            f"Supported types: {list(CHART_FUNCTIONS.keys())}"
        )

    create_fn = CHART_FUNCTIONS[chart_type]
    return create_fn(data, config)

"""
LaTeX templates for PDF generation.

Provides cover page templates and document configuration.
"""

from __future__ import annotations

from datetime import date

try:
    from .styles import StyleConfig
except ImportError:
    from styles import StyleConfig


def get_cover_page_template(
    title: str,
    author: str = "",
    doc_date: str = "",
    style: StyleConfig = None,
) -> str:
    """
    Generate LaTeX code for a centered cover page.

    Args:
        title: Document title
        author: Author name (optional)
        doc_date: Date string (optional, defaults to today)
        style: Style configuration

    Returns:
        LaTeX code for the title page
    """
    if not doc_date:
        doc_date = date.today().strftime("%d %B %Y")

    # Escape LaTeX special characters
    title = escape_latex(title)
    author = escape_latex(author)
    doc_date = escape_latex(doc_date)

    return rf"""
\begin{{titlepage}}
    \centering
    \vspace*{{\fill}}
    {{\Huge\bfseries {title}\par}}
    \vspace{{1.5cm}}
    {{\Large {author}\par}}
    \vspace{{0.8cm}}
    {{\large {doc_date}\par}}
    \vspace*{{\fill}}
\end{{titlepage}}
\newpage
"""


def get_document_header(
    style: StyleConfig,
    paper_size: str = "a4",
    font_size: str = "11pt",
    toc: bool = False,
) -> str:
    """
    Generate the LaTeX document header/preamble additions.

    Args:
        style: Style configuration
        paper_size: Paper size (a4, letter, legal)
        font_size: Font size (10pt, 11pt, 12pt)
        toc: Whether to include table of contents

    Returns:
        LaTeX preamble additions
    """
    try:
        from .styles import get_style_latex_header
    except ImportError:
        from styles import get_style_latex_header

    lines = []

    # Essential packages for Markdown conversion
    lines.append(r"\usepackage{longtable}")  # For tables
    lines.append(r"\usepackage{booktabs}")  # Better table formatting
    lines.append(r"\usepackage{graphicx}")  # For images
    lines.append(r"\usepackage{amsmath}")  # For math
    lines.append(r"\usepackage{amssymb}")  # Math symbols
    lines.append(r"\usepackage{listings}")  # Code blocks
    lines.append(r"\usepackage{float}")  # Figure placement

    # Code block styling
    lines.append(r"""
\lstset{
    basicstyle=\ttfamily\small,
    breaklines=true,
    frame=single,
    backgroundcolor=\color{gray!10},
    numbers=left,
    numberstyle=\tiny\color{gray},
    tabsize=4
}
""")

    # Style-specific configuration
    lines.append(get_style_latex_header(style))

    # Add page break after table of contents
    if toc:
        lines.append(r"""
% Redefine TOC to add page break after it
\let\oldtableofcontents\tableofcontents
\renewcommand{\tableofcontents}{\oldtableofcontents\newpage}
""")

    return "\n".join(lines)


def escape_latex(text: str) -> str:
    """
    Escape special LaTeX characters in text.

    Args:
        text: Text to escape

    Returns:
        Escaped text safe for LaTeX
    """
    if not text:
        return ""

    # Characters that need escaping in LaTeX
    replacements = [
        ("\\", r"\textbackslash{}"),
        ("&", r"\&"),
        ("%", r"\%"),
        ("$", r"\$"),
        ("#", r"\#"),
        ("_", r"\_"),
        ("{", r"\{"),
        ("}", r"\}"),
        ("~", r"\textasciitilde{}"),
        ("^", r"\textasciicircum{}"),
    ]

    for char, replacement in replacements:
        text = text.replace(char, replacement)

    return text

"""
Markdown to PDF converter using Pandoc.

Handles the conversion pipeline: Markdown → LaTeX → PDF
"""

from __future__ import annotations

import asyncio
import os
import shutil
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

try:
    from .styles import StyleConfig, get_style_config
    from .templates import get_cover_page_template, get_document_header
except ImportError:
    from styles import StyleConfig, get_style_config
    from templates import get_cover_page_template, get_document_header


PANDOC_PATH = os.getenv("PANDOC_PATH", "pandoc")
LATEX_ENGINE = os.getenv("LATEX_ENGINE", "pdflatex")


def preprocess_markdown(content: str) -> str:
    """
    Preprocess markdown content to handle common issues.

    Converts literal escape sequences to their actual characters
    to prevent LaTeX interpretation errors.

    Args:
        content: Raw markdown content

    Returns:
        Preprocessed markdown content
    """
    # Convert literal \n to actual newlines
    content = content.replace("\\n", "\n")
    # Convert literal \t to actual tabs
    content = content.replace("\\t", "\t")
    # Convert literal \r to nothing (normalize line endings)
    content = content.replace("\\r", "")

    return content


@dataclass
class ConversionConfig:
    """Configuration for PDF conversion."""

    title: str = ""
    author: str = ""
    date: str = ""
    cover_page: bool = True
    toc: bool = False
    style: str = "default"
    paper_size: str = "a4"
    font_size: str = "11pt"


async def check_pandoc_available() -> tuple[bool, Optional[str]]:
    """
    Check if Pandoc is available.

    Returns:
        Tuple of (available, version_string)
    """
    try:
        proc = await asyncio.create_subprocess_exec(
            PANDOC_PATH,
            "--version",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, _ = await proc.communicate()

        if proc.returncode == 0:
            version_line = stdout.decode().split("\n")[0]
            return True, version_line
        return False, None
    except FileNotFoundError:
        return False, None


async def check_latex_available() -> tuple[bool, str]:
    """
    Check if LaTeX engine is available.

    Returns:
        Tuple of (available, engine_name)
    """
    try:
        proc = await asyncio.create_subprocess_exec(
            LATEX_ENGINE,
            "--version",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, _ = await proc.communicate()

        if proc.returncode == 0:
            return True, LATEX_ENGINE
        return False, LATEX_ENGINE
    except FileNotFoundError:
        return False, LATEX_ENGINE


async def convert_markdown_to_pdf(
    content: str,
    config: ConversionConfig,
) -> bytes:
    """
    Convert Markdown content to PDF using Pandoc.

    Args:
        content: Markdown content
        config: Conversion configuration

    Returns:
        PDF file bytes

    Raises:
        RuntimeError: If conversion fails
        FileNotFoundError: If Pandoc is not available
    """
    # Preprocess markdown content
    content = preprocess_markdown(content)

    # Get style configuration
    style = get_style_config(config.style)

    # Create temporary directory for conversion
    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)

        # Write markdown content
        md_file = tmppath / "input.md"
        md_file.write_text(content, encoding="utf-8")

        # Create LaTeX header file
        header_file = tmppath / "header.tex"
        header_content = get_document_header(
            style=style,
            paper_size=config.paper_size,
            font_size=config.font_size,
            toc=config.toc,
        )
        header_file.write_text(header_content, encoding="utf-8")

        # Create cover page if requested
        before_body_file = None
        if config.cover_page and config.title:
            before_body_file = tmppath / "cover.tex"
            cover_content = get_cover_page_template(
                title=config.title,
                author=config.author,
                doc_date=config.date,
                style=style,
            )
            before_body_file.write_text(cover_content, encoding="utf-8")

        # Output PDF file
        pdf_file = tmppath / "output.pdf"

        # Build Pandoc command
        cmd = [
            PANDOC_PATH,
            str(md_file),
            "-o",
            str(pdf_file),
            f"--pdf-engine={LATEX_ENGINE}",
            f"--include-in-header={header_file}",
            f"-V", f"geometry:margin={style.margin}",
            f"-V", f"fontsize={config.font_size}",
            f"-V", f"papersize={config.paper_size}",
            "--standalone",
        ]

        # Add cover page
        if before_body_file:
            cmd.extend(["--include-before-body", str(before_body_file)])

        # Add table of contents
        if config.toc:
            cmd.append("--toc")
            cmd.extend(["--toc-depth", "3"])

        # Run Pandoc
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        stdout, stderr = await proc.communicate()

        if proc.returncode != 0:
            error_msg = stderr.decode() if stderr else "Unknown error"
            raise RuntimeError(f"Pandoc conversion failed: {error_msg}")

        # Read and return PDF bytes
        if not pdf_file.exists():
            raise RuntimeError("PDF file was not created")

        return pdf_file.read_bytes()


def get_pandoc_path() -> str:
    """Get the configured Pandoc path."""
    return PANDOC_PATH


def get_latex_engine() -> str:
    """Get the configured LaTeX engine."""
    return LATEX_ENGINE

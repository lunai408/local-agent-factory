"""
MCP Server for PDF generation.

Provides tools for generating PDFs from Markdown using Pandoc and LaTeX.
"""

from __future__ import annotations

import argparse
import logging
import os
import sys
from pathlib import Path
from typing import Literal

from mcp.server.fastmcp import FastMCP, Context
from mcp.server.transport_security import TransportSecuritySettings
from starlette.responses import FileResponse, Response

try:
    from .converter import (
        ConversionConfig,
        convert_markdown_to_pdf,
        check_pandoc_available,
        check_latex_available,
        get_pandoc_path,
        get_latex_engine,
    )
    from .storage import PDFStorage
    from .styles import StyleType, get_style_info
    from shared.context import get_conversation_id
except ImportError:
    # When running directly with mcp dev
    from converter import (
        ConversionConfig,
        convert_markdown_to_pdf,
        check_pandoc_available,
        check_latex_available,
        get_pandoc_path,
        get_latex_engine,
    )
    from storage import PDFStorage
    from styles import StyleType, get_style_info

    def get_conversation_id(ctx: Context) -> str:
        """Fallback for mcp dev mode."""
        try:
            if ctx.request_context and ctx.request_context.request:
                raw_conv_id = ctx.request_context.request.headers.get("X-Conversation-ID")
                if raw_conv_id:
                    return "".join(c if c.isalnum() or c in "-_" else "_" for c in raw_conv_id[:64])
        except Exception:
            pass
        return "_shared"


# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger("pdf-generator-mcp")

# Server configuration (set in main())
_server_config = {
    "host": "127.0.0.1",
    "port": 8000,
    "base_url": None,  # Set when server starts with HTTP transport
}

# Data directory for generated PDFs
DATA_DIR = Path(os.getenv("PDFS_DIR", "./data/generated_pdfs")).resolve()


def get_base_url() -> str | None:
    """Get the base URL for file serving."""
    return _server_config.get("base_url")


def get_file_url(conv_id: str, filename: str) -> str:
    """Generate URL for a file."""
    base_url = get_base_url()
    if base_url:
        return f"{base_url}/files/{conv_id}/{filename}"
    # Fallback to file:// for stdio transport
    return f"file://{DATA_DIR / conv_id / filename}"


# Initialize MCP server
# Disable DNS rebinding protection for Docker compatibility (allows Host: mcp-pdf:3001)
mcp = FastMCP(
    "pdf-generator",
    transport_security=TransportSecuritySettings(
        enable_dns_rebinding_protection=False,
    ),
    instructions=(
        "Generate PDF documents from Markdown content using Pandoc and LaTeX. "
        "Supports cover pages, table of contents, math formulas, tables, images, and code blocks."
    ),
)


# Health check endpoint for Docker
@mcp.custom_route("/health", methods=["GET"])
async def health_check(request) -> Response:
    """Health check endpoint for Docker."""
    return Response(content="OK", status_code=200)


# File serving endpoint
@mcp.custom_route("/files/{conv_id}/{filename}", methods=["GET"])
async def serve_file(request) -> Response:
    """Serve generated PDF files."""
    conv_id = request.path_params.get("conv_id", "_shared")
    filename = request.path_params.get("filename", "")

    # Sanitize inputs to prevent path traversal
    safe_conv_id = "".join(c if c.isalnum() or c in "-_" else "_" for c in conv_id[:64])
    safe_filename = Path(filename).name  # Remove any path components

    file_path = DATA_DIR / safe_conv_id / safe_filename

    if not file_path.exists():
        return Response(content="File not found", status_code=404)

    # Verify file is within DATA_DIR (security check)
    try:
        file_path.resolve().relative_to(DATA_DIR.resolve())
    except ValueError:
        return Response(content="Access denied", status_code=403)

    return FileResponse(file_path)

# Type aliases
PaperSizeType = Literal["a4", "letter", "legal"]
FontSizeType = Literal["10pt", "11pt", "12pt"]


@mcp.tool()
async def generate_pdf(
    ctx: Context,
    content: str,
    title: str = "",
    author: str = "",
    date: str = "",
    cover_page: bool = True,
    toc: bool = False,
    style: StyleType = "default",
    paper_size: PaperSizeType = "a4",
    font_size: FontSizeType = "11pt",
) -> dict:
    """
    Generate a PDF from Markdown content.

    Args:
        content: Markdown content to convert
        title: Document title (shown on cover page)
        author: Author name (shown on cover page)
        date: Date (defaults to today if not specified)
        cover_page: Include a centered cover page with title/author/date
        toc: Include table of contents
        style: Visual style - "default", "academic", "modern", or "minimal"
        paper_size: Paper size - "a4", "letter", or "legal"
        font_size: Font size - "10pt", "11pt", or "12pt"

    Supports:
        - Headings (# ## ###)
        - Lists (- * 1.)
        - Tables (| col1 | col2 |)
        - Images (![alt](path))
        - Code blocks (``` or indentation)
        - Math formulas ($inline$ or $$block$$)
        - Links, bold, italic, etc.

    Returns:
        Dictionary with:
        - success: Whether generation succeeded
        - pdf_path: Absolute path to the saved PDF
        - pdf_url: File URL for opening the PDF
        - title: Document title
        - metadata: Generation parameters
    """

    conv_id = get_conversation_id(ctx)
    logger.debug("Generating PDF for conversation: %s", conv_id)
    storage = PDFStorage(conv_id=conv_id)

    # Validate style
    valid_styles = ["default", "academic", "modern", "minimal"]
    if style not in valid_styles:
        return {
            "success": False,
            "error": f"Invalid style: {style}. Valid styles: {valid_styles}",
        }

    # Validate paper size
    valid_paper_sizes = ["a4", "letter", "legal"]
    if paper_size not in valid_paper_sizes:
        return {
            "success": False,
            "error": f"Invalid paper_size: {paper_size}. Valid sizes: {valid_paper_sizes}",
        }

    # Validate font size
    valid_font_sizes = ["10pt", "11pt", "12pt"]
    if font_size not in valid_font_sizes:
        return {
            "success": False,
            "error": f"Invalid font_size: {font_size}. Valid sizes: {valid_font_sizes}",
        }

    # Check Pandoc availability
    pandoc_ok, _ = await check_pandoc_available()
    if not pandoc_ok:
        return {
            "success": False,
            "error": "Pandoc is not available. Install it with: brew install pandoc",
        }

    # Check LaTeX availability
    latex_ok, _ = await check_latex_available()
    if not latex_ok:
        return {
            "success": False,
            "error": "LaTeX is not available. Install it with: brew install --cask mactex",
        }

    try:
        # Create conversion config
        config = ConversionConfig(
            title=title,
            author=author,
            date=date,
            cover_page=cover_page,
            toc=toc,
            style=style,
            paper_size=paper_size,
            font_size=font_size,
        )

        # Convert to PDF
        pdf_bytes = await convert_markdown_to_pdf(content, config)

        # Save PDF
        pdf_path, pdf_metadata = storage.save_pdf(
            pdf_bytes=pdf_bytes,
            content=content,
            title=title or "Untitled",
            author=author,
            style=style,
            paper_size=paper_size,
            font_size=font_size,
            has_cover_page=cover_page and bool(title),
            has_toc=toc,
        )

        # Generate URL (HTTP if available, file:// otherwise)
        pdf_url = get_file_url(conv_id, pdf_path.name)

        return {
            "success": True,
            "pdf_path": str(pdf_path),
            "pdf_url": pdf_url,
            "title": title or "Untitled",
            "metadata": {
                "author": author,
                "style": style,
                "paper_size": paper_size,
                "font_size": font_size,
                "has_cover_page": cover_page and bool(title),
                "has_toc": toc,
                "created_at": pdf_metadata.created_at,
                "conversation_id": conv_id,
            },
        }

    except RuntimeError as e:
        return {
            "success": False,
            "error": f"PDF generation failed: {e}",
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Unexpected error: {e}",
        }


@mcp.tool()
async def list_generated_pdfs(ctx: Context, limit: int = 20) -> dict:
    """
    List recently generated PDFs.

    Args:
        limit: Maximum number of PDFs to return (default 20)

    Returns:
        Dictionary with:
        - success: Whether listing succeeded
        - pdfs: List of PDF metadata (path, title, author, etc.)
        - count: Number of PDFs returned
    """
    conv_id = get_conversation_id(ctx)
    storage = PDFStorage(conv_id=conv_id)

    try:
        pdfs = storage.list_pdfs(limit=limit)

        return {
            "success": True,
            "pdfs": [
                {
                    "pdf_path": meta.local_path,
                    "pdf_url": get_file_url(conv_id, Path(meta.local_path).name),
                    "title": meta.title,
                    "author": meta.author,
                    "style": meta.style,
                    "paper_size": meta.paper_size,
                    "has_cover_page": meta.has_cover_page,
                    "has_toc": meta.has_toc,
                    "created_at": meta.created_at,
                }
                for meta in pdfs
            ],
            "count": len(pdfs),
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to list PDFs: {e}",
        }


@mcp.tool()
async def list_styles() -> dict:
    """
    List available visual styles for PDF generation.

    Returns:
        Dictionary with:
        - success: Whether operation succeeded
        - styles: Map of style name to description
    """
    return {
        "success": True,
        "styles": get_style_info(),
    }


@mcp.tool()
async def check_pandoc_status() -> dict:
    """
    Check if Pandoc and LaTeX are available for PDF generation.

    Returns:
        Dictionary with:
        - available: Whether PDF generation is possible
        - pandoc_available: Whether Pandoc is installed
        - pandoc_version: Pandoc version string
        - latex_available: Whether LaTeX is installed
        - latex_engine: LaTeX engine being used
    """
    pandoc_ok, pandoc_version = await check_pandoc_available()
    latex_ok, latex_engine = await check_latex_available()

    result = {
        "available": pandoc_ok and latex_ok,
        "pandoc_available": pandoc_ok,
        "pandoc_version": pandoc_version,
        "pandoc_path": get_pandoc_path(),
        "latex_available": latex_ok,
        "latex_engine": latex_engine,
    }

    if not pandoc_ok:
        result["error"] = "Pandoc not found. Install with: brew install pandoc"
    elif not latex_ok:
        result["error"] = "LaTeX not found. Install with: brew install --cask mactex"

    return result


def main():
    """Entry point for the MCP server."""
    parser = argparse.ArgumentParser(description="PDF Generator MCP Server")
    parser.add_argument(
        "--transport",
        choices=["stdio", "sse", "streamable-http"],
        default="stdio",
        help="Transport type (default: stdio)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port for HTTP transports (default: 8000)",
    )
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Host for HTTP transports (default: 127.0.0.1)",
    )
    args = parser.parse_args()

    # Store server config for URL generation
    _server_config["host"] = args.host
    _server_config["port"] = args.port

    logger.info("=" * 50)
    logger.info("Starting pdf-generator MCP server...")
    logger.info("Transport: %s", args.transport)
    logger.info("Pandoc path: %s", get_pandoc_path())
    logger.info("LaTeX engine: %s", get_latex_engine())
    logger.info("Data directory: %s", DATA_DIR)

    if args.transport in ["sse", "streamable-http"]:
        mcp.settings.port = args.port
        mcp.settings.host = args.host
        _server_config["base_url"] = f"http://{args.host}:{args.port}"
        logger.info("Listening on %s:%s", args.host, args.port)
        logger.info("Files served at: %s/files/<conv_id>/<filename>", _server_config["base_url"])

    logger.info("=" * 50)
    mcp.run(transport=args.transport)


if __name__ == "__main__":
    main()

"""
MCP Server for chart generation.

Provides tools for generating charts using matplotlib and seaborn.
"""

from __future__ import annotations

import argparse
import logging
import os
import sys
from pathlib import Path
from typing import Any

from mcp.server.fastmcp import FastMCP, Context
from mcp.server.transport_security import TransportSecuritySettings
from starlette.responses import FileResponse, Response

try:
    from .charts import (
        ChartConfig,
        ChartType,
        FormatType,
        QualityType,
        CHART_SPECS,
        DPI,
        QUALITY_SIZES,
        FORMAT_RATIOS,
        create_chart,
    )
    from .storage import ChartStorage
    from .themes import ThemeType, get_theme_info
    from shared.context import get_conversation_id
except ImportError:
    # When running directly with mcp dev
    from charts import (
        ChartConfig,
        ChartType,
        FormatType,
        QualityType,
        CHART_SPECS,
        DPI,
        QUALITY_SIZES,
        FORMAT_RATIOS,
        create_chart,
    )
    from storage import ChartStorage
    from themes import ThemeType, get_theme_info

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
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger("chart-generator-mcp")

# Server configuration (set in main())
_server_config = {
    "host": "127.0.0.1",
    "port": 8000,
    "base_url": None,  # Set when server starts with HTTP transport
}

# Data directory for generated charts
DATA_DIR = Path(os.getenv("CHARTS_DIR", "./data/generated_charts")).resolve()


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
# Disable DNS rebinding protection for Docker compatibility (allows Host: mcp-chart:3003)
mcp = FastMCP(
    "chart-generator",
    transport_security=TransportSecuritySettings(
        enable_dns_rebinding_protection=False,
    ),
    instructions=(
        "Generate charts and graphs using matplotlib and seaborn. "
        "Supports scatter, line, bar, histogram, pie, heatmap, box, violin, and area charts."
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
    """Serve generated chart files."""
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


def calculate_pixel_dimensions(
    format: FormatType = "square",
    quality: QualityType = "high",
) -> tuple[int, int]:
    """Calculate pixel dimensions from format and quality."""
    ratio_w, ratio_h = FORMAT_RATIOS.get(format, (1, 1))
    max_pixels = QUALITY_SIZES.get(quality, 1024)

    if ratio_w >= ratio_h:
        width = max_pixels
        height = int(max_pixels * ratio_h / ratio_w)
    else:
        height = max_pixels
        width = int(max_pixels * ratio_w / ratio_h)

    return width, height


@mcp.tool()
async def generate_chart(
    ctx: Context,
    chart_type: ChartType,
    data: dict,
    title: str = "",
    xlabel: str = "",
    ylabel: str = "",
    legend: dict = {},
    theme: ThemeType = "default",
    format: FormatType = "square",
    quality: QualityType = "high",
) -> dict:
    """
    Generate a chart from data.

    Args:
        chart_type: Type of chart - "scatter", "line", "bar", "barh", "histogram",
                   "pie", "heatmap", "box", "violin", or "area"
        data: Data for the chart. Format depends on chart_type:
            - scatter: {"x": [...], "y": [...]}
            - line: {"x": [...], "y": [...]} or {"x": [...], "y": [[...], [...]]} for multi-line
            - bar/barh: {"categories": [...], "values": [...]}
            - histogram: {"values": [...], "bins": 10}
            - pie: {"labels": [...], "values": [...]}
            - heatmap: {"data": [[...]], "xlabels": [...], "ylabels": [...]}
            - box/violin: {"data": [[group1], [group2]], "labels": [...]}
            - area: {"x": [...], "y": [[...], [...]]}
        title: Chart title
        xlabel: X-axis label
        ylabel: Y-axis label
        legend: Legend labels as object with "value" key (e.g. {"value": ["A", "B"]}), empty {} for no legend
        theme: Color theme - "default", "dark", "light", "colorblind", "pastel", "bold", "monochrome"
        format: Aspect ratio - "square" (1:1), "landscape" (16:9), "portrait" (9:16)
        quality: Resolution - "high" (1024px), "medium" (720px), "low" (256px), "very_low" (128px)

    Returns:
        Dictionary with:
        - success: Whether generation succeeded
        - image_path: Absolute path to the saved chart
        - image_url: URL for markdown display (HTTP if available, file:// otherwise)
        - chart_type: The type of chart generated
        - metadata: Generation parameters

    Examples:
        - Scatter: data={"x": [1,2,3], "y": [4,5,6]}
        - Line with 2 series: data={"x": [1,2,3], "y": [[1,2,3], [3,2,1]]}, legend={"value": ["A", "B"]}
        - Bar: data={"categories": ["A","B","C"], "values": [10,20,15]}
        - Histogram: data={"values": [1,2,2,3,3,3,4,5], "bins": 5}
        - Pie: data={"labels": ["A","B","C"], "values": [30,50,20]}
        - Heatmap: data={"data": [[1,2],[3,4]], "xlabels": ["X1","X2"], "ylabels": ["Y1","Y2"]}
    """
    conv_id = get_conversation_id(ctx)
    storage = ChartStorage(conv_id=conv_id)

    # Validate chart type
    if chart_type not in CHART_SPECS:
        return {
            "success": False,
            "error": f"Unsupported chart type: {chart_type}. "
            f"Supported: {list(CHART_SPECS.keys())}",
        }

    # Validate required data fields
    spec = CHART_SPECS[chart_type]
    missing = [field for field in spec["required"] if field not in data]
    if missing:
        return {
            "success": False,
            "error": f"Missing required data fields for {chart_type}: {missing}. "
            f"Required: {spec['required']}",
        }

    try:
        # Extract legend list from dict (expects {"value": [...]})
        legend_list = legend.get("value", []) if legend else []

        # Create chart config
        config = ChartConfig(
            title=title,
            xlabel=xlabel,
            ylabel=ylabel,
            legend=legend_list,
            theme=theme,
            format=format,
            quality=quality,
        )

        # Generate chart
        image_bytes = create_chart(chart_type, data, config)

        # Calculate dimensions for metadata
        width, height = calculate_pixel_dimensions(format, quality)

        # Save chart
        image_path, chart_metadata = storage.save_chart(
            image_bytes=image_bytes,
            chart_type=chart_type,
            data=data,
            title=title,
            width=width,
            height=height,
            theme=theme,
            format=format,
            quality=quality,
            xlabel=xlabel,
            ylabel=ylabel,
            legend=legend_list if legend_list else None,
        )

        # Generate URL (HTTP if available, file:// otherwise)
        image_url = get_file_url(conv_id, image_path.name)

        return {
            "success": True,
            "image_path": str(image_path),
            "image_url": image_url,
            "chart_type": chart_type,
            "metadata": {
                "title": title,
                "theme": theme,
                "format": format,
                "quality": quality,
                "width": width,
                "height": height,
                "created_at": chart_metadata.created_at,
            },
        }

    except ValueError as e:
        return {
            "success": False,
            "error": f"Invalid data: {e}",
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Chart generation failed: {e}",
        }


@mcp.tool()
async def list_chart_types() -> dict[str, Any]:
    """
    List all supported chart types with their data format requirements.

    Returns:
        Dictionary with:
        - chart_types: Map of chart type to its specification
          (required fields, optional fields, description, example)
    """
    return {
        "success": True,
        "chart_types": CHART_SPECS,
    }


@mcp.tool()
async def list_themes() -> dict[str, Any]:
    """
    List all available color themes.

    Returns:
        Dictionary with:
        - themes: Map of theme name to its description
    """
    return {
        "success": True,
        "themes": get_theme_info(),
    }


@mcp.tool()
async def list_generated_charts(ctx: Context, limit: int = 20) -> dict[str, Any]:
    """
    List recently generated charts.

    Args:
        limit: Maximum number of charts to return (default 20)

    Returns:
        Dictionary with:
        - success: Whether listing succeeded
        - charts: List of chart metadata (path, type, title, etc.)
        - count: Number of charts returned
    """
    conv_id = get_conversation_id(ctx)
    storage = ChartStorage(conv_id=conv_id)

    try:
        charts = storage.list_charts(limit=limit)

        return {
            "success": True,
            "charts": [
                {
                    "image_path": meta.local_path,
                    "image_url": get_file_url(conv_id, Path(meta.local_path).name),
                    "chart_type": meta.chart_type,
                    "title": meta.title,
                    "theme": meta.theme,
                    "format": meta.format,
                    "quality": meta.quality,
                    "width": meta.width,
                    "height": meta.height,
                    "created_at": meta.created_at,
                }
                for meta in charts
            ],
            "count": len(charts),
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to list charts: {e}",
        }


def main():
    """Entry point for the MCP server."""
    parser = argparse.ArgumentParser(description="Chart Generator MCP Server")
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
    logger.info("Starting chart-generator MCP server...")
    logger.info("Transport: %s", args.transport)
    logger.info("Supported chart types: %s", list(CHART_SPECS.keys()))
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

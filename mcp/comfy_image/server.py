"""
MCP Server for image generation via ComfyUI.

Provides tools for generating images using ComfyUI workflows.
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import random
import sys
from pathlib import Path
from typing import Any, Literal

from mcp.server.fastmcp import FastMCP, Context
from mcp.server.transport_security import TransportSecuritySettings
from starlette.responses import FileResponse, Response

try:
    from .comfy_client import ComfyClient, extract_image_info
    from .storage import ImageStorage
    from shared.context import get_conversation_id
except ImportError:
    # When running directly with mcp dev
    from comfy_client import ComfyClient, extract_image_info
    from storage import ImageStorage

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
logger = logging.getLogger("comfy-image-mcp")

# Server configuration (set in main())
_server_config = {
    "host": "127.0.0.1",
    "port": 8000,
    "base_url": None,  # Set when server starts with HTTP transport
}

# Data directory for generated images
DATA_DIR = Path(os.getenv("GENERATED_IMAGES_DIR", "./data/generated_images")).resolve()

# Workflow directory
WORKFLOWS_DIR = Path(__file__).parent / "workflows"

# ComfyUI configuration
COMFY_URL = os.getenv("COMFY_URL", "http://localhost:8188")


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


def load_workflow(name: str) -> dict[str, Any]:
    """Load a workflow JSON file."""
    workflow_path = WORKFLOWS_DIR / f"{name}.json"
    if not workflow_path.exists():
        raise FileNotFoundError(f"Workflow not found: {name}")
    return json.loads(workflow_path.read_text())


def prepare_workflow(
    workflow: dict[str, Any],
    prompt: str,
    seed: int | None = None,
    width: int = 1024,
    height: int = 1024,
    steps: int = 9,
) -> dict[str, Any]:
    """
    Prepare a workflow by injecting parameters.

    Modifies the workflow in-place for the z_image_api workflow format.
    """
    # Generate random seed if not provided
    if seed is None:
        seed = random.randint(0, 2**32 - 1)

    # Update prompt (node 45 - CLIPTextEncode)
    if "45" in workflow:
        workflow["45"]["inputs"]["text"] = prompt

    # Update seed and steps (node 44 - KSampler)
    if "44" in workflow:
        workflow["44"]["inputs"]["seed"] = seed
        workflow["44"]["inputs"]["steps"] = steps

    # Update dimensions (node 41 - EmptySD3LatentImage)
    if "41" in workflow:
        workflow["41"]["inputs"]["width"] = width
        workflow["41"]["inputs"]["height"] = height

    return workflow


# Initialize MCP server
# Disable DNS rebinding protection for Docker compatibility (allows Host: mcp-comfy:3002)
mcp = FastMCP(
    "comfy-image",
    transport_security=TransportSecuritySettings(
        enable_dns_rebinding_protection=False,
    ),
    instructions=(
        "Generate images using ComfyUI. "
        "Supports text-to-image generation with configurable dimensions, steps, and seeds."
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
    """Serve generated image files."""
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
QualityType = Literal["draft", "normal", "high"]
AspectRatioType = Literal["square", "landscape", "portrait", "wide", "tall"]

# Quality presets (steps)
QUALITY_STEPS = {
    "draft": 5,
    "normal": 9,
    "high": 15,
}

# Aspect ratio presets (width, height)
ASPECT_RATIOS = {
    "square": (1024, 1024),
    "landscape": (1280, 768),
    "portrait": (768, 1280),
    "wide": (1536, 640),
    "tall": (640, 1536),
}


@mcp.tool()
async def generate_image(
    ctx: Context,
    prompt: str,
    aspect_ratio: AspectRatioType = "square",
    quality: QualityType = "normal",
    seed: int | None = None,
) -> dict[str, Any]:
    """
    Generate an image from a text prompt using ComfyUI.

    Args:
        prompt: Text description of the image to generate
        aspect_ratio: Image dimensions - "square" (1024x1024), "landscape" (1280x768),
                     "portrait" (768x1280), "wide" (1536x640), "tall" (640x1536)
        quality: Generation quality - "draft" (5 steps), "normal" (9 steps), "high" (15 steps)
        seed: Random seed for reproducibility (optional, random if not provided)

    Returns:
        Dictionary with:
        - success: Whether generation succeeded
        - image_path: Absolute path to the saved image
        - image_url: URL for markdown display (HTTP if available, file:// otherwise)
        - prompt: The prompt used
        - metadata: Generation parameters (seed, dimensions, steps)

    Examples:
        - Simple: prompt="A cat sitting on a windowsill"
        - Detailed: prompt="A majestic lion in the savanna at sunset, golden hour lighting"
        - With options: prompt="Forest landscape", aspect_ratio="wide", quality="high"
    """
    conv_id = get_conversation_id(ctx)
    storage = ImageStorage(conv_id=conv_id)
    client = ComfyClient(base_url=COMFY_URL)

    # Check ComfyUI availability
    if not await client.is_available():
        return {
            "success": False,
            "error": f"ComfyUI is not available at {COMFY_URL}. Make sure it's running.",
        }

    # Get dimensions and steps from presets
    width, height = ASPECT_RATIOS.get(aspect_ratio, (1024, 1024))
    steps = QUALITY_STEPS.get(quality, 9)

    # Generate seed if not provided
    actual_seed = seed if seed is not None else random.randint(0, 2**32 - 1)

    try:
        # Load and prepare workflow
        workflow = load_workflow("z_image_api")
        workflow = prepare_workflow(
            workflow=workflow,
            prompt=prompt,
            seed=actual_seed,
            width=width,
            height=height,
            steps=steps,
        )

        logger.info("Submitting workflow to ComfyUI...")
        prompt_id = await client.queue_prompt(workflow)
        logger.info("Prompt ID: %s", prompt_id)

        # Wait for completion
        logger.info("Waiting for generation to complete...")
        history = await client.wait_for_completion(prompt_id)

        # Extract image info
        images = extract_image_info(history)
        if not images:
            return {
                "success": False,
                "error": "No images were generated",
            }

        # Download and save the first image
        img_info = images[0]
        image_bytes = await client.get_image(
            filename=img_info["filename"],
            subfolder=img_info["subfolder"],
            folder_type=img_info["type"],
        )

        # Save locally
        image_path, metadata = storage.save_image(
            image_bytes=image_bytes,
            prompt=prompt,
            seed=actual_seed,
            width=width,
            height=height,
            steps=steps,
            model="z_image_turbo",
            comfy_filename=img_info["filename"],
        )

        # Generate URL (HTTP if available, file:// otherwise)
        image_url = get_file_url(conv_id, image_path.name)

        return {
            "success": True,
            "image_path": str(image_path),
            "image_url": image_url,
            "prompt": prompt,
            "metadata": {
                "seed": actual_seed,
                "width": width,
                "height": height,
                "steps": steps,
                "aspect_ratio": aspect_ratio,
                "quality": quality,
                "model": "z_image_turbo",
                "created_at": metadata.created_at,
            },
        }

    except FileNotFoundError as e:
        return {
            "success": False,
            "error": str(e),
        }
    except TimeoutError as e:
        return {
            "success": False,
            "error": f"Generation timed out: {e}",
        }
    except RuntimeError as e:
        return {
            "success": False,
            "error": f"ComfyUI error: {e}",
        }
    except Exception as e:
        logger.exception("Unexpected error during image generation")
        return {
            "success": False,
            "error": f"Unexpected error: {e}",
        }


@mcp.tool()
async def list_generated_images(ctx: Context, limit: int = 20) -> dict[str, Any]:
    """
    List recently generated images.

    Args:
        limit: Maximum number of images to return (default 20)

    Returns:
        Dictionary with:
        - success: Whether listing succeeded
        - images: List of image metadata (path, prompt, seed, dimensions, etc.)
        - count: Number of images returned
    """
    conv_id = get_conversation_id(ctx)
    storage = ImageStorage(conv_id=conv_id)

    try:
        images = storage.list_images(limit=limit)

        return {
            "success": True,
            "images": [
                {
                    "image_path": meta.local_path,
                    "image_url": get_file_url(conv_id, Path(meta.local_path).name),
                    "prompt": meta.prompt,
                    "seed": meta.seed,
                    "width": meta.width,
                    "height": meta.height,
                    "steps": meta.steps,
                    "model": meta.model,
                    "created_at": meta.created_at,
                }
                for meta in images
            ],
            "count": len(images),
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to list images: {e}",
        }


@mcp.tool()
async def check_comfy_status() -> dict[str, Any]:
    """
    Check if ComfyUI is available and get system stats.

    Returns:
        Dictionary with:
        - available: Whether ComfyUI is reachable
        - url: The ComfyUI URL being used
        - stats: System stats if available
    """
    client = ComfyClient(base_url=COMFY_URL)

    try:
        stats = await client.get_system_stats()
        return {
            "available": True,
            "url": COMFY_URL,
            "stats": stats,
        }
    except Exception as e:
        return {
            "available": False,
            "url": COMFY_URL,
            "error": str(e),
        }


@mcp.tool()
async def list_aspect_ratios() -> dict[str, Any]:
    """
    List available aspect ratio presets.

    Returns:
        Dictionary with aspect ratio names and their dimensions.
    """
    return {
        "success": True,
        "aspect_ratios": {
            name: {"width": w, "height": h}
            for name, (w, h) in ASPECT_RATIOS.items()
        },
    }


@mcp.tool()
async def list_quality_presets() -> dict[str, Any]:
    """
    List available quality presets.

    Returns:
        Dictionary with quality names and their step counts.
    """
    return {
        "success": True,
        "quality_presets": {
            name: {"steps": steps, "description": desc}
            for name, steps, desc in [
                ("draft", 5, "Fast preview with lower quality"),
                ("normal", 9, "Balanced quality and speed"),
                ("high", 15, "Best quality, slower generation"),
            ]
        },
    }


def main():
    """Entry point for the MCP server."""
    parser = argparse.ArgumentParser(description="ComfyUI Image MCP Server")
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
    logger.info("Starting comfy-image MCP server...")
    logger.info("Transport: %s", args.transport)
    logger.info("ComfyUI URL: %s", COMFY_URL)
    logger.info("Data directory: %s", DATA_DIR)
    logger.info("Workflows directory: %s", WORKFLOWS_DIR)

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

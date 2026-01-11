"""
Async HTTP client for ComfyUI API.

Handles workflow submission, polling for completion, and image retrieval.
"""

from __future__ import annotations

import asyncio
import os
import uuid
from typing import Any

import httpx

COMFY_URL = os.getenv("COMFY_URL", "http://localhost:8188")
DEFAULT_TIMEOUT = float(os.getenv("COMFY_TIMEOUT", "1800"))  # 30 minutes default
POLL_INTERVAL = 0.5  # seconds


class ComfyClient:
    """Async client for ComfyUI HTTP API."""

    def __init__(self, base_url: str = COMFY_URL):
        self.base_url = base_url.rstrip("/")
        self.client_id = str(uuid.uuid4())

    async def queue_prompt(self, workflow: dict[str, Any]) -> str:
        """
        Submit a workflow to ComfyUI's queue.

        Args:
            workflow: The workflow JSON (API format)

        Returns:
            The prompt_id for tracking the job
        """
        payload = {
            "prompt": workflow,
            "client_id": self.client_id,
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/prompt",
                json=payload,
                timeout=30.0,
            )
            response.raise_for_status()
            data = response.json()
            return data["prompt_id"]

    async def get_history(self, prompt_id: str) -> dict[str, Any] | None:
        """
        Get the execution history for a prompt.

        Args:
            prompt_id: The prompt ID to check

        Returns:
            History data if available, None if not yet complete
        """
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/history/{prompt_id}",
                timeout=10.0,
            )
            response.raise_for_status()
            data = response.json()

            if prompt_id in data:
                return data[prompt_id]
            return None

    async def wait_for_completion(
        self,
        prompt_id: str,
        timeout: float = DEFAULT_TIMEOUT,
    ) -> dict[str, Any]:
        """
        Poll until the prompt execution is complete.

        Args:
            prompt_id: The prompt ID to wait for
            timeout: Maximum time to wait in seconds

        Returns:
            The history data for the completed prompt

        Raises:
            TimeoutError: If the prompt doesn't complete in time
            RuntimeError: If the execution fails
        """
        start_time = asyncio.get_event_loop().time()

        while True:
            elapsed = asyncio.get_event_loop().time() - start_time
            if elapsed > timeout:
                raise TimeoutError(
                    f"Prompt {prompt_id} did not complete within {timeout}s"
                )

            history = await self.get_history(prompt_id)

            if history is not None:
                # Check for errors
                if "status" in history:
                    status = history["status"]
                    if status.get("status_str") == "error":
                        messages = status.get("messages", [])
                        error_msg = "; ".join(
                            str(m) for m in messages if m
                        ) or "Unknown error"
                        raise RuntimeError(f"ComfyUI execution failed: {error_msg}")

                # Check if outputs are available
                if "outputs" in history and history["outputs"]:
                    return history

            await asyncio.sleep(POLL_INTERVAL)

    async def get_image(
        self,
        filename: str,
        subfolder: str = "",
        folder_type: str = "output",
    ) -> bytes:
        """
        Download a generated image from ComfyUI.

        Args:
            filename: The image filename
            subfolder: Optional subfolder
            folder_type: Type of folder (output, input, temp)

        Returns:
            Raw image bytes
        """
        params = {
            "filename": filename,
            "subfolder": subfolder,
            "type": folder_type,
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/view",
                params=params,
                timeout=30.0,
            )
            response.raise_for_status()
            return response.content

    async def get_system_stats(self) -> dict[str, Any]:
        """Get ComfyUI system stats (useful for health check)."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/system_stats",
                timeout=10.0,
            )
            response.raise_for_status()
            return response.json()

    async def is_available(self) -> bool:
        """Check if ComfyUI is available and responding."""
        try:
            await self.get_system_stats()
            return True
        except Exception:
            return False


def extract_image_info(history: dict[str, Any]) -> list[dict[str, str]]:
    """
    Extract image information from ComfyUI history.

    Args:
        history: The history data from get_history()

    Returns:
        List of dicts with filename, subfolder, type for each image
    """
    images = []

    outputs = history.get("outputs", {})
    for node_output in outputs.values():
        if "images" in node_output:
            for img in node_output["images"]:
                images.append({
                    "filename": img.get("filename", ""),
                    "subfolder": img.get("subfolder", ""),
                    "type": img.get("type", "output"),
                })

    return images

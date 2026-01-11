"""
Local storage management for generated images.

Stores images with metadata in a structured directory.
"""

from __future__ import annotations

import hashlib
import json
import os
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


@dataclass
class ImageMetadata:
    """Metadata for a generated image."""

    local_path: str
    prompt: str
    seed: int
    width: int
    height: int
    steps: int
    model: str
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    comfy_filename: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "ImageMetadata":
        """Create from dictionary."""
        return cls(**data)


DEFAULT_CONV_ID = "_shared"


class ImageStorage:
    """
    Manager for locally stored generated images.

    Stores images in a configurable directory with associated metadata.
    Images are organized in subdirectories by conversation ID.
    """

    def __init__(self, base_dir: Optional[Path] = None, conv_id: str = DEFAULT_CONV_ID):
        self.base_dir = base_dir or Path(
            os.getenv("GENERATED_IMAGES_DIR", "./data/generated_images")
        ).resolve()
        self.conv_id = conv_id
        self.conv_dir = self.base_dir / conv_id
        self._ensure_dirs()

    def _ensure_dirs(self) -> None:
        """Ensure the conversation directory exists."""
        self.conv_dir.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _prompt_hash(prompt: str) -> str:
        """Generate a short hash from the prompt."""
        return hashlib.sha256(prompt.encode()).hexdigest()[:8]

    def _generate_filename(self, prompt: str, seed: int) -> str:
        """Generate a unique filename for an image."""
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        prompt_hash = self._prompt_hash(prompt)
        return f"{timestamp}_{prompt_hash}_{seed}.png"

    def save_image(
        self,
        image_bytes: bytes,
        prompt: str,
        seed: int,
        width: int,
        height: int,
        steps: int,
        model: str,
        comfy_filename: Optional[str] = None,
    ) -> tuple[Path, ImageMetadata]:
        """
        Save an image and its metadata.

        Args:
            image_bytes: Raw PNG image data
            prompt: The prompt used for generation
            seed: The seed used
            width: Image width
            height: Image height
            steps: Number of inference steps
            model: Model name used
            comfy_filename: Original filename from ComfyUI

        Returns:
            Tuple of (image_path, metadata)
        """
        filename = self._generate_filename(prompt, seed)
        image_path = self.conv_dir / filename
        metadata_path = self.conv_dir / f"{filename}.json"

        # Save image
        image_path.write_bytes(image_bytes)

        # Create and save metadata
        metadata = ImageMetadata(
            local_path=str(image_path),
            prompt=prompt,
            seed=seed,
            width=width,
            height=height,
            steps=steps,
            model=model,
            comfy_filename=comfy_filename,
        )

        metadata_path.write_text(json.dumps(metadata.to_dict(), indent=2))

        return image_path, metadata

    def list_images(self, limit: int = 20) -> list[ImageMetadata]:
        """
        List recently generated images.

        Args:
            limit: Maximum number of images to return

        Returns:
            List of ImageMetadata, sorted by creation time (newest first)
        """
        images = []

        # Find all .json metadata files in conversation directory
        metadata_files = sorted(
            self.conv_dir.glob("*.json"),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )

        for meta_path in metadata_files[:limit]:
            try:
                data = json.loads(meta_path.read_text())
                metadata = ImageMetadata.from_dict(data)

                # Verify the image file still exists
                if Path(metadata.local_path).exists():
                    images.append(metadata)
            except (json.JSONDecodeError, TypeError, KeyError):
                # Skip invalid metadata files
                continue

        return images

    def get_image_by_path(self, path: str) -> Optional[ImageMetadata]:
        """
        Get metadata for a specific image.

        Args:
            path: The image path

        Returns:
            ImageMetadata if found, None otherwise
        """
        metadata_path = Path(path).with_suffix(".png.json")
        if not metadata_path.exists():
            # Try alternate naming
            metadata_path = Path(f"{path}.json")

        if not metadata_path.exists():
            return None

        try:
            data = json.loads(metadata_path.read_text())
            return ImageMetadata.from_dict(data)
        except (json.JSONDecodeError, TypeError, KeyError):
            return None

    def delete_image(self, path: str) -> bool:
        """
        Delete an image and its metadata.

        Args:
            path: The image path

        Returns:
            True if deleted, False if not found
        """
        image_path = Path(path)
        metadata_path = Path(f"{path}.json")

        deleted = False

        if image_path.exists():
            image_path.unlink()
            deleted = True

        if metadata_path.exists():
            metadata_path.unlink()
            deleted = True

        return deleted

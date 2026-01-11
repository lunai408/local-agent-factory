"""
Local storage management for generated charts.

Stores chart images with metadata in a structured directory.
"""

from __future__ import annotations

import hashlib
import json
import os
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional


@dataclass
class ChartMetadata:
    """Metadata for a generated chart."""

    local_path: str
    chart_type: str
    title: str
    width: int
    height: int
    theme: str
    format: str
    quality: str
    data_hash: str  # Hash of input data for reference
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    xlabel: Optional[str] = None
    ylabel: Optional[str] = None
    legend: Optional[list[str]] = None

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "ChartMetadata":
        """Create from dictionary."""
        return cls(**data)


DEFAULT_CONV_ID = "_shared"


class ChartStorage:
    """
    Manager for locally stored generated charts.

    Stores chart images in a configurable directory with associated metadata.
    Charts are organized in subdirectories by conversation ID.
    """

    def __init__(self, base_dir: Optional[Path] = None, conv_id: str = DEFAULT_CONV_ID):
        self.base_dir = base_dir or Path(
            os.getenv("CHARTS_DIR", "./data/generated_charts")
        ).resolve()
        self.conv_id = conv_id
        self.conv_dir = self.base_dir / conv_id
        self._ensure_dirs()

    def _ensure_dirs(self) -> None:
        """Ensure the conversation directory exists."""
        self.conv_dir.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _data_hash(data: dict[str, Any]) -> str:
        """Generate a short hash from the data."""
        data_str = json.dumps(data, sort_keys=True)
        return hashlib.sha256(data_str.encode()).hexdigest()[:8]

    def _generate_filename(self, chart_type: str, data: dict[str, Any]) -> str:
        """Generate a unique filename for a chart."""
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S_%f")
        data_hash = self._data_hash(data)
        return f"{chart_type}_{timestamp}_{data_hash}.png"

    def save_chart(
        self,
        image_bytes: bytes,
        chart_type: str,
        data: dict[str, Any],
        title: str,
        width: int,
        height: int,
        theme: str,
        format: str,
        quality: str,
        xlabel: Optional[str] = None,
        ylabel: Optional[str] = None,
        legend: Optional[list[str]] = None,
    ) -> tuple[Path, ChartMetadata]:
        """
        Save a chart and its metadata.

        Args:
            image_bytes: Raw PNG image data
            chart_type: Type of chart generated
            data: The input data used
            title: Chart title
            width: Image width in pixels
            height: Image height in pixels
            theme: Theme name used
            format: Format preset used
            quality: Quality preset used
            xlabel: X-axis label
            ylabel: Y-axis label
            legend: Legend labels

        Returns:
            Tuple of (image_path, metadata)
        """
        filename = self._generate_filename(chart_type, data)
        image_path = self.conv_dir / filename
        metadata_path = self.conv_dir / f"{filename}.json"

        # Save image
        image_path.write_bytes(image_bytes)

        # Create and save metadata
        metadata = ChartMetadata(
            local_path=str(image_path),
            chart_type=chart_type,
            title=title,
            width=width,
            height=height,
            theme=theme,
            format=format,
            quality=quality,
            data_hash=self._data_hash(data),
            xlabel=xlabel,
            ylabel=ylabel,
            legend=legend,
        )

        metadata_path.write_text(json.dumps(metadata.to_dict(), indent=2))

        return image_path, metadata

    def list_charts(self, limit: int = 20) -> list[ChartMetadata]:
        """
        List recently generated charts.

        Args:
            limit: Maximum number of charts to return

        Returns:
            List of ChartMetadata, sorted by creation time (newest first)
        """
        charts = []

        # Find all .json metadata files in conversation directory
        metadata_files = sorted(
            self.conv_dir.glob("*.json"),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )

        for meta_path in metadata_files[:limit]:
            try:
                data = json.loads(meta_path.read_text())
                metadata = ChartMetadata.from_dict(data)

                # Verify the image file still exists
                if Path(metadata.local_path).exists():
                    charts.append(metadata)
            except (json.JSONDecodeError, TypeError, KeyError):
                # Skip invalid metadata files
                continue

        return charts

    def get_chart_by_path(self, path: str) -> Optional[ChartMetadata]:
        """
        Get metadata for a specific chart.

        Args:
            path: The chart image path

        Returns:
            ChartMetadata if found, None otherwise
        """
        metadata_path = Path(path).with_suffix(".png.json")
        if not metadata_path.exists():
            # Try alternate naming
            metadata_path = Path(f"{path}.json")

        if not metadata_path.exists():
            return None

        try:
            data = json.loads(metadata_path.read_text())
            return ChartMetadata.from_dict(data)
        except (json.JSONDecodeError, TypeError, KeyError):
            return None

    def delete_chart(self, path: str) -> bool:
        """
        Delete a chart and its metadata.

        Args:
            path: The chart image path

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

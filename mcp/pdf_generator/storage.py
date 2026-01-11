"""
Local storage management for generated PDFs.

Stores PDF files with metadata in a structured directory.
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
class PDFMetadata:
    """Metadata for a generated PDF."""

    local_path: str
    title: str
    author: str
    style: str
    paper_size: str
    font_size: str
    has_cover_page: bool
    has_toc: bool
    content_hash: str  # Hash of input content for reference
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "PDFMetadata":
        """Create from dictionary."""
        return cls(**data)


DEFAULT_CONV_ID = "_shared"


class PDFStorage:
    """
    Manager for locally stored generated PDFs.

    Stores PDF files in a configurable directory with associated metadata.
    PDFs are organized in subdirectories by conversation ID.
    """

    def __init__(self, base_dir: Optional[Path] = None, conv_id: str = DEFAULT_CONV_ID):
        self.base_dir = base_dir or Path(
            os.getenv("PDFS_DIR", "./data/generated_pdfs")
        ).resolve()
        self.conv_id = conv_id
        self.conv_dir = self.base_dir / conv_id
        self._ensure_dirs()

    def _ensure_dirs(self) -> None:
        """Ensure the conversation directory exists."""
        self.conv_dir.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _content_hash(content: str) -> str:
        """Generate a short hash from the content."""
        return hashlib.sha256(content.encode()).hexdigest()[:8]

    def _generate_filename(self, title: str, content: str) -> str:
        """Generate a unique filename for a PDF."""
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        content_hash = self._content_hash(content)

        # Create safe title slug
        safe_title = "".join(c if c.isalnum() else "_" for c in title[:30])
        safe_title = safe_title.strip("_") or "document"

        return f"{safe_title}_{timestamp}_{content_hash}.pdf"

    def save_pdf(
        self,
        pdf_bytes: bytes,
        content: str,
        title: str,
        author: str,
        style: str,
        paper_size: str,
        font_size: str,
        has_cover_page: bool,
        has_toc: bool,
    ) -> tuple[Path, PDFMetadata]:
        """
        Save a PDF and its metadata.

        Args:
            pdf_bytes: Raw PDF data
            content: Original Markdown content (for hashing)
            title: Document title
            author: Author name
            style: Style used
            paper_size: Paper size
            font_size: Font size
            has_cover_page: Whether cover page was included
            has_toc: Whether TOC was included

        Returns:
            Tuple of (pdf_path, metadata)
        """
        filename = self._generate_filename(title, content)
        pdf_path = self.conv_dir / filename
        metadata_path = self.conv_dir / f"{filename}.json"

        # Save PDF
        pdf_path.write_bytes(pdf_bytes)

        # Create and save metadata
        metadata = PDFMetadata(
            local_path=str(pdf_path),
            title=title,
            author=author,
            style=style,
            paper_size=paper_size,
            font_size=font_size,
            has_cover_page=has_cover_page,
            has_toc=has_toc,
            content_hash=self._content_hash(content),
        )

        metadata_path.write_text(json.dumps(metadata.to_dict(), indent=2))

        return pdf_path, metadata

    def list_pdfs(self, limit: int = 20) -> list[PDFMetadata]:
        """
        List recently generated PDFs.

        Args:
            limit: Maximum number of PDFs to return

        Returns:
            List of PDFMetadata, sorted by creation time (newest first)
        """
        pdfs = []

        # Find all .json metadata files in conversation directory
        metadata_files = sorted(
            self.conv_dir.glob("*.json"),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )

        for meta_path in metadata_files[:limit]:
            try:
                data = json.loads(meta_path.read_text())
                metadata = PDFMetadata.from_dict(data)

                # Verify the PDF file still exists
                if Path(metadata.local_path).exists():
                    pdfs.append(metadata)
            except (json.JSONDecodeError, TypeError, KeyError):
                # Skip invalid metadata files
                continue

        return pdfs

    def get_pdf_by_path(self, path: str) -> Optional[PDFMetadata]:
        """
        Get metadata for a specific PDF.

        Args:
            path: The PDF path

        Returns:
            PDFMetadata if found, None otherwise
        """
        metadata_path = Path(f"{path}.json")

        if not metadata_path.exists():
            return None

        try:
            data = json.loads(metadata_path.read_text())
            return PDFMetadata.from_dict(data)
        except (json.JSONDecodeError, TypeError, KeyError):
            return None

    def delete_pdf(self, path: str) -> bool:
        """
        Delete a PDF and its metadata.

        Args:
            path: The PDF path

        Returns:
            True if deleted, False if not found
        """
        pdf_path = Path(path)
        metadata_path = Path(f"{path}.json")

        deleted = False

        if pdf_path.exists():
            pdf_path.unlink()
            deleted = True

        if metadata_path.exists():
            metadata_path.unlink()
            deleted = True

        return deleted

"""
Local file storage management for knowledge files.

Usage (sync):
    from utils.storage import get_storage_manager

    storage = get_storage_manager()
    local_path, metadata = storage.cache_from_url(url)

Usage (async):
    storage = get_storage_manager()
    local_path, metadata = await storage.cache_from_url_async(url)

    # Or with Knowledge integration
    local_path, metadata = await storage.prepare_for_knowledge_async(url)
"""

from __future__ import annotations

import asyncio
import hashlib
import os
import shutil
import urllib.request
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

from dotenv import load_dotenv

load_dotenv()


@dataclass
class StorageConfig:
    """Configuration for local file storage."""

    base_dir: Path = field(
        default_factory=lambda: Path(
            os.getenv("KNOWLEDGE_FILES_DIR", "./data/knowledge_files")
        ).resolve()
    )
    chunk_size: int = 1024 * 1024  # 1MB chunks for hashing


@dataclass
class FileMetadata:
    """Metadata for a stored file."""

    local_path: Path
    sha256: str
    filename: str
    size_bytes: int
    created_at: datetime
    original_url: Optional[str] = None
    content_type: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert to dictionary for use in Knowledge metadata."""
        return {
            "local_path": str(self.local_path),
            "sha256": self.sha256,
            "filename": self.filename,
            "size_bytes": self.size_bytes,
            "created_at": self.created_at.isoformat(),
            "original_url": self.original_url,
            "content_type": self.content_type,
        }


class StorageManager:
    """
    Manager for local file storage.

    Handles downloading, caching, and organizing knowledge files.
    Uses content-addressable storage with URL-based directory structure.
    """

    _instance: Optional[StorageManager] = None
    _initialized: bool = False

    def __new__(cls, config: Optional[StorageConfig] = None) -> StorageManager:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, config: Optional[StorageConfig] = None) -> None:
        if StorageManager._initialized:
            return

        self.config = config or StorageConfig()
        self._ensure_base_dir()
        StorageManager._initialized = True

    def _ensure_base_dir(self) -> None:
        """Ensure the base directory exists."""
        self.config.base_dir.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _url_to_key(url: str) -> str:
        """Generate a stable directory key from a URL."""
        return hashlib.sha1(url.encode("utf-8")).hexdigest()

    @staticmethod
    def _filename_from_url(url: str, default: str = "document") -> str:
        """Extract filename from URL."""
        parsed = urlparse(url)
        filename = Path(parsed.path).name
        return filename if filename else default

    def _get_dest_dir(self, url: str) -> Path:
        """Get the destination directory for a URL."""
        url_key = self._url_to_key(url)
        return self.config.base_dir / url_key

    def compute_sha256(self, path: Path) -> str:
        """Compute SHA256 hash of a file."""
        h = hashlib.sha256()
        with path.open("rb") as f:
            for chunk in iter(lambda: f.read(self.config.chunk_size), b""):
                h.update(chunk)
        return h.hexdigest()

    async def compute_sha256_async(self, path: Path) -> str:
        """Compute SHA256 hash of a file asynchronously."""
        return await asyncio.to_thread(self.compute_sha256, path)

    def _build_metadata(
        self, path: Path, sha256: str, original_url: Optional[str] = None
    ) -> FileMetadata:
        """Build metadata for a stored file."""
        stat = path.stat()
        return FileMetadata(
            local_path=path,
            sha256=sha256,
            filename=path.name,
            size_bytes=stat.st_size,
            created_at=datetime.fromtimestamp(stat.st_ctime, tz=timezone.utc),
            original_url=original_url,
            content_type=self._guess_content_type(path),
        )

    @staticmethod
    def _guess_content_type(path: Path) -> Optional[str]:
        """Guess content type from file extension."""
        extension_map = {
            ".pdf": "application/pdf",
            ".txt": "text/plain",
            ".md": "text/markdown",
            ".json": "application/json",
            ".csv": "text/csv",
            ".html": "text/html",
            ".xml": "application/xml",
            ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        }
        return extension_map.get(path.suffix.lower())

    def cache_from_url(
        self, url: str, force_download: bool = False
    ) -> tuple[Path, FileMetadata]:
        """
        Download and cache a file from URL.

        Args:
            url: URL to download from
            force_download: If True, re-download even if file exists

        Returns:
            Tuple of (local_path, metadata)
        """
        dest_dir = self._get_dest_dir(url)
        dest_dir.mkdir(parents=True, exist_ok=True)

        filename = self._filename_from_url(url)
        dest_path = dest_dir / filename

        if not dest_path.exists() or force_download:
            urllib.request.urlretrieve(url, dest_path)

        sha256 = self.compute_sha256(dest_path)
        metadata = self._build_metadata(dest_path, sha256, original_url=url)

        return dest_path, metadata

    async def cache_from_url_async(
        self, url: str, force_download: bool = False
    ) -> tuple[Path, FileMetadata]:
        """
        Download and cache a file from URL asynchronously.

        Args:
            url: URL to download from
            force_download: If True, re-download even if file exists

        Returns:
            Tuple of (local_path, metadata)
        """
        return await asyncio.to_thread(self.cache_from_url, url, force_download)

    def store_local_file(
        self, source_path: Path, collection: Optional[str] = None, copy: bool = True
    ) -> tuple[Path, FileMetadata]:
        """
        Store a local file in the managed storage.

        Args:
            source_path: Path to the source file
            collection: Optional collection/category name for organization
            copy: If True, copy the file; if False, move it

        Returns:
            Tuple of (stored_path, metadata)
        """
        source_path = Path(source_path).resolve()
        if not source_path.exists():
            raise FileNotFoundError(f"Source file not found: {source_path}")

        # Use file hash as directory key for content-addressable storage
        sha256 = self.compute_sha256(source_path)

        if collection:
            dest_dir = self.config.base_dir / collection / sha256[:16]
        else:
            dest_dir = self.config.base_dir / "local" / sha256[:16]

        dest_dir.mkdir(parents=True, exist_ok=True)
        dest_path = dest_dir / source_path.name

        if not dest_path.exists():
            if copy:
                shutil.copy2(source_path, dest_path)
            else:
                shutil.move(str(source_path), str(dest_path))

        metadata = self._build_metadata(dest_path, sha256)
        return dest_path, metadata

    async def store_local_file_async(
        self, source_path: Path, collection: Optional[str] = None, copy: bool = True
    ) -> tuple[Path, FileMetadata]:
        """Store a local file asynchronously."""
        return await asyncio.to_thread(
            self.store_local_file, source_path, collection, copy
        )

    def get_file_metadata(self, path: Path) -> FileMetadata:
        """Get metadata for an existing file."""
        path = Path(path).resolve()
        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")

        sha256 = self.compute_sha256(path)
        return self._build_metadata(path, sha256)

    async def get_file_metadata_async(self, path: Path) -> FileMetadata:
        """Get metadata for an existing file asynchronously."""
        return await asyncio.to_thread(self.get_file_metadata, path)

    def prepare_for_knowledge(
        self, source: str | Path, force_download: bool = False
    ) -> tuple[Path, dict]:
        """
        Prepare a file for use with Agno Knowledge.

        Handles both URLs and local paths. Returns the local path
        and a metadata dict ready for Knowledge.add_content().

        Args:
            source: URL or local file path
            force_download: If True, re-download URLs even if cached

        Returns:
            Tuple of (local_path, metadata_dict)
        """
        source_str = str(source)

        if source_str.startswith(("http://", "https://")):
            path, metadata = self.cache_from_url(source_str, force_download)
        else:
            path, metadata = self.store_local_file(Path(source_str))

        return path, metadata.to_dict()

    async def prepare_for_knowledge_async(
        self, source: str | Path, force_download: bool = False
    ) -> tuple[Path, dict]:
        """Prepare a file for use with Agno Knowledge asynchronously."""
        return await asyncio.to_thread(self.prepare_for_knowledge, source, force_download)

    def list_cached_files(self, collection: Optional[str] = None) -> list[Path]:
        """List all cached files, optionally filtered by collection."""
        if collection:
            search_dir = self.config.base_dir / collection
        else:
            search_dir = self.config.base_dir

        if not search_dir.exists():
            return []

        return [
            f for f in search_dir.rglob("*") if f.is_file() and not f.name.startswith(".")
        ]

    def clear_cache(self, collection: Optional[str] = None) -> int:
        """
        Clear cached files.

        Args:
            collection: If provided, only clear files in this collection

        Returns:
            Number of files deleted
        """
        files = self.list_cached_files(collection)
        count = 0

        for f in files:
            f.unlink()
            count += 1
            # Remove empty parent directories
            parent = f.parent
            if parent != self.config.base_dir and not any(parent.iterdir()):
                parent.rmdir()

        return count

    @classmethod
    def reset(cls) -> None:
        """Reset the singleton (useful for testing)."""
        cls._instance = None
        cls._initialized = False


def get_storage_manager(config: Optional[StorageConfig] = None) -> StorageManager:
    """Get the StorageManager singleton instance."""
    return StorageManager(config)

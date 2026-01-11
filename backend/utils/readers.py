"""
Custom readers for Agno Knowledge with SurrealDB-safe IDs.

SurrealDB record IDs don't support certain characters (like '-').
This module provides reader wrappers that generate safe IDs.

Usage:
    from utils.readers import safe_pdf_reader, safe_reader, SafeIdsReader

    # Pre-configured PDF reader
    knowledge.add_content(path="doc.pdf", reader=safe_pdf_reader)

    # Custom prefix
    my_reader = safe_reader(PDFReader(), prefix="recipes")

    # Or wrap any reader manually
    custom = SafeIdsReader(MyReader(), prefix="custom")
"""

from __future__ import annotations

import hashlib
import re
from typing import TYPE_CHECKING, Optional

from agno.knowledge.document import Document
from agno.knowledge.reader.base import Reader
from agno.knowledge.reader.pdf_reader import PDFReader
from agno.knowledge.reader.text_reader import TextReader
from agno.knowledge.reader.csv_reader import CSVReader
from agno.knowledge.reader.json_reader import JSONReader
from agno.knowledge.reader.docx_reader import DocxReader

if TYPE_CHECKING:
    from collections.abc import Sequence

# Pattern for SurrealDB-safe IDs: alphanumeric and underscores only
_SAFE_ID_RE = re.compile(r"^[A-Za-z0-9_]+$")


def _stable_hex_id(*parts: str) -> str:
    """Generate a stable hex ID from input parts."""
    seed = "||".join(parts)
    return hashlib.sha1(seed.encode("utf-8")).hexdigest()


class SafeIdsReader(Reader):
    """
    Reader wrapper that ensures document IDs are SurrealDB-safe.

    SurrealDB record IDs have restrictions on allowed characters.
    This wrapper transforms any problematic IDs into safe hex-based IDs
    while preserving the original ID in metadata.

    Args:
        inner: The underlying reader to wrap
        prefix: Prefix for generated IDs (helps identify document source)
    """

    def __init__(self, inner: Reader, prefix: str = "doc") -> None:
        super().__init__()
        self.inner = inner
        self.prefix = prefix

    def _fix_ids(self, docs: Sequence[Document]) -> list[Document]:
        """Transform document IDs to be SurrealDB-safe."""
        for i, doc in enumerate(docs):
            current_id = getattr(doc, "id", None)

            # Skip if ID is already safe
            if isinstance(current_id, str) and _SAFE_ID_RE.fullmatch(current_id):
                continue

            # Generate stable ID from document properties
            page = str((doc.meta_data or {}).get("page", ""))
            name = str(getattr(doc, "name", "") or "")
            content = doc.content or ""

            new_id = _stable_hex_id(self.prefix, name, page, str(i), content)

            # Preserve original ID in metadata
            if doc.meta_data is None:
                doc.meta_data = {}
            doc.meta_data["original_id"] = current_id
            doc.id = new_id

        return list(docs)

    def read(self, obj: str, name: Optional[str] = None) -> list[Document]:
        """Read and fix document IDs synchronously."""
        return self._fix_ids(self.inner.read(obj, name=name))

    async def async_read(self, obj: str, name: Optional[str] = None) -> list[Document]:
        """Read and fix document IDs asynchronously."""
        return self._fix_ids(await self.inner.async_read(obj, name=name))


def safe_reader(inner: Reader, prefix: str = "doc") -> SafeIdsReader:
    """
    Wrap any reader to produce SurrealDB-safe IDs.

    Args:
        inner: The reader to wrap
        prefix: Prefix for generated IDs

    Returns:
        SafeIdsReader wrapping the input reader

    Example:
        reader = safe_reader(PDFReader(), prefix="manual")
    """
    return SafeIdsReader(inner, prefix=prefix)


# Pre-configured safe readers for common file types
safe_pdf_reader = SafeIdsReader(PDFReader(), prefix="pdf")
safe_text_reader = SafeIdsReader(TextReader(), prefix="txt")
safe_csv_reader = SafeIdsReader(CSVReader(), prefix="csv")
safe_json_reader = SafeIdsReader(JSONReader(), prefix="json")
safe_docx_reader = SafeIdsReader(DocxReader(), prefix="docx")


def get_safe_reader_for_extension(extension: str, prefix: Optional[str] = None) -> SafeIdsReader:
    """
    Get a safe reader based on file extension.

    Args:
        extension: File extension (with or without leading dot)
        prefix: Optional custom prefix (defaults to extension-based)

    Returns:
        Appropriate SafeIdsReader for the file type

    Raises:
        ValueError: If extension is not supported

    Example:
        reader = get_safe_reader_for_extension(".pdf")
        reader = get_safe_reader_for_extension("docx", prefix="manual")
    """
    ext = extension.lower().lstrip(".")

    reader_map: dict[str, tuple[type[Reader], str]] = {
        "pdf": (PDFReader, "pdf"),
        "txt": (TextReader, "txt"),
        "text": (TextReader, "txt"),
        "md": (TextReader, "md"),
        "markdown": (TextReader, "md"),
        "csv": (CSVReader, "csv"),
        "json": (JSONReader, "json"),
        "docx": (DocxReader, "docx"),
    }

    if ext not in reader_map:
        supported = ", ".join(sorted(reader_map.keys()))
        raise ValueError(f"Unsupported extension '{ext}'. Supported: {supported}")

    reader_class, default_prefix = reader_map[ext]
    return SafeIdsReader(reader_class(), prefix=prefix or default_prefix)

"""
Tool for managing knowledge bases dynamically.

Allows agents to add, remove, and search knowledge content at runtime.
"""

from __future__ import annotations

from typing import Optional

from agno.tools import Toolkit
from agno.knowledge.knowledge import Knowledge
from agno.utils.log import logger

from utils import get_db_manager, get_storage_manager, get_safe_reader_for_extension


class KnowledgeTool(Toolkit):
    """
    Tool for managing knowledge bases.

    Provides functions to:
    - Add content from URLs or local files
    - Remove content by ID
    - List all content
    - Search content
    """

    def __init__(
        self,
        knowledge: Knowledge,
        allow_add: bool = True,
        allow_remove: bool = True,
    ):
        super().__init__(name="knowledge_manager")
        self.knowledge = knowledge
        self.storage = get_storage_manager()

        if allow_add:
            self.register(self.add_knowledge_from_url)
            self.register(self.add_knowledge_from_file)

        if allow_remove:
            self.register(self.remove_knowledge_by_id)
            self.register(self.remove_knowledge_by_name)
            self.register(self.remove_all_knowledge)

        self.register(self.list_knowledge_contents)

    def add_knowledge_from_url(self, url: str, name: Optional[str] = None) -> str:
        """
        Add content to the knowledge base from a URL.

        Args:
            url: The URL to download and add (PDF, TXT, DOCX, etc.)
            name: Optional name for the content (defaults to filename)

        Returns:
            Success message with content ID
        """
        try:
            # Download and cache the file (returns dict metadata)
            local_path, metadata = self.storage.prepare_for_knowledge(url)

            # Get appropriate reader
            reader = get_safe_reader_for_extension(local_path.suffix)

            # Add to knowledge with a tag for vector removal
            content_name = name or local_path.stem
            metadata["knowledge_content_name"] = content_name

            self.knowledge.add_content(
                name=content_name,
                path=str(local_path),
                reader=reader,
                metadata=metadata,
            )

            return f"Successfully added '{content_name}' to knowledge base from {url}"

        except Exception as e:
            logger.error(f"Failed to add knowledge from URL: {e}")
            return f"Error adding content: {str(e)}"

    def add_knowledge_from_file(
        self, file_path: str, name: Optional[str] = None
    ) -> str:
        """
        Add content to the knowledge base from a local file.

        Args:
            file_path: Path to the local file (PDF, TXT, DOCX, etc.)
            name: Optional name for the content (defaults to filename)

        Returns:
            Success message with content ID
        """
        try:
            from pathlib import Path

            path = Path(file_path)
            if not path.exists():
                return f"Error: File not found at {file_path}"

            # Store in managed storage (returns dict metadata)
            local_path, metadata = self.storage.prepare_for_knowledge(path)

            # Get appropriate reader
            reader = get_safe_reader_for_extension(path.suffix)

            # Add to knowledge with a tag for vector removal
            content_name = name or path.stem
            metadata["knowledge_content_name"] = content_name

            self.knowledge.add_content(
                name=content_name,
                path=str(local_path),
                reader=reader,
                metadata=metadata,
            )

            return f"Successfully added '{content_name}' to knowledge base"

        except Exception as e:
            logger.error(f"Failed to add knowledge from file: {e}")
            return f"Error adding content: {str(e)}"

    def remove_knowledge_by_id(self, content_id: str) -> str:
        """
        Remove content from the knowledge base by its ID.
        Also removes associated vectors and local files.

        Args:
            content_id: The ID of the content to remove

        Returns:
            Success or error message
        """
        try:
            from pathlib import Path

            # Get content info before deletion
            contents, _ = self.knowledge.get_content()
            content_to_remove = None
            for content in contents:
                if getattr(content, "id", None) == content_id:
                    content_to_remove = content
                    break

            if not content_to_remove:
                return f"Error: Content with ID '{content_id}' not found"

            content_name = getattr(content_to_remove, "name", None)
            metadata = getattr(content_to_remove, "metadata", {}) or {}
            local_path = metadata.get("local_path")
            knowledge_tag = metadata.get("knowledge_content_name")

            # Remove vectors - try both methods
            if content_name:
                try:
                    self.knowledge.remove_vectors_by_name(content_name)
                    logger.info(f"Removed vectors by name: {content_name}")
                except Exception as e:
                    logger.warning(f"Could not remove vectors by name: {e}")

            if knowledge_tag:
                try:
                    self.knowledge.remove_vectors_by_metadata(
                        {"knowledge_content_name": knowledge_tag}
                    )
                    logger.info(f"Removed vectors by metadata: {knowledge_tag}")
                except Exception as e:
                    logger.warning(f"Could not remove vectors by metadata: {e}")

            # Remove local file
            if local_path:
                try:
                    file_path = Path(local_path)
                    if file_path.exists():
                        file_path.unlink()
                        logger.info(f"Removed local file: {local_path}")
                        # Remove parent dir if empty
                        parent = file_path.parent
                        if parent.exists() and not any(parent.iterdir()):
                            parent.rmdir()
                except Exception as e:
                    logger.warning(f"Could not remove local file: {e}")

            # Remove content record
            self.knowledge.remove_content_by_id(content_id)

            return f"Successfully removed content '{content_name}' (ID: {content_id}), its vectors, and local file"

        except Exception as e:
            logger.error(f"Failed to remove knowledge: {e}")
            return f"Error removing content: {str(e)}"

    def remove_knowledge_by_name(self, name: str) -> str:
        """
        Remove content from the knowledge base by its name.
        Also removes associated vectors and local files.

        Args:
            name: The name of the content to remove

        Returns:
            Success or error message
        """
        try:
            from pathlib import Path

            # Get content info before deletion
            contents, _ = self.knowledge.get_content()
            content_to_remove = None
            for content in contents:
                if getattr(content, "name", None) == name:
                    content_to_remove = content
                    break

            if not content_to_remove:
                return f"Error: Content with name '{name}' not found"

            content_id = getattr(content_to_remove, "id", None)
            metadata = getattr(content_to_remove, "metadata", {}) or {}
            local_path = metadata.get("local_path")
            knowledge_tag = metadata.get("knowledge_content_name")

            # Remove vectors - try both methods
            try:
                self.knowledge.remove_vectors_by_name(name)
                logger.info(f"Removed vectors by name: {name}")
            except Exception as e:
                logger.warning(f"Could not remove vectors by name: {e}")

            if knowledge_tag:
                try:
                    self.knowledge.remove_vectors_by_metadata(
                        {"knowledge_content_name": knowledge_tag}
                    )
                    logger.info(f"Removed vectors by metadata: {knowledge_tag}")
                except Exception as e:
                    logger.warning(f"Could not remove vectors by metadata: {e}")

            # Remove local file
            if local_path:
                try:
                    file_path = Path(local_path)
                    if file_path.exists():
                        file_path.unlink()
                        logger.info(f"Removed local file: {local_path}")
                        # Remove parent dir if empty
                        parent = file_path.parent
                        if parent.exists() and not any(parent.iterdir()):
                            parent.rmdir()
                except Exception as e:
                    logger.warning(f"Could not remove local file: {e}")

            # Remove content record
            if content_id:
                self.knowledge.remove_content_by_id(content_id)

            return f"Successfully removed content '{name}', its vectors, and local file"

        except Exception as e:
            logger.error(f"Failed to remove knowledge: {e}")
            return f"Error removing content: {str(e)}"

    def remove_all_knowledge(self) -> str:
        """
        Remove all content from the knowledge base.
        Also removes all vectors and local files.

        Returns:
            Success or error message
        """
        try:
            from pathlib import Path

            # Get all content before deletion
            contents, _ = self.knowledge.get_content()
            removed_count = 0

            for content in contents:
                content_name = getattr(content, "name", None)
                metadata = getattr(content, "metadata", {}) or {}
                local_path = metadata.get("local_path")
                knowledge_tag = metadata.get("knowledge_content_name")

                # Remove vectors - try both methods
                if content_name:
                    try:
                        self.knowledge.remove_vectors_by_name(content_name)
                    except Exception as e:
                        logger.warning(f"Could not remove vectors by name: {e}")

                if knowledge_tag:
                    try:
                        self.knowledge.remove_vectors_by_metadata(
                            {"knowledge_content_name": knowledge_tag}
                        )
                    except Exception as e:
                        logger.warning(f"Could not remove vectors by metadata: {e}")

                # Remove local file
                if local_path:
                    try:
                        file_path = Path(local_path)
                        if file_path.exists():
                            file_path.unlink()
                            # Remove parent dir if empty
                            parent = file_path.parent
                            if parent.exists() and not any(parent.iterdir()):
                                parent.rmdir()
                    except Exception as e:
                        logger.warning(f"Could not remove local file {local_path}: {e}")

                removed_count += 1

            # Remove all content records
            self.knowledge.remove_all_content()

            return f"Successfully removed {removed_count} content(s), their vectors, and local files"

        except Exception as e:
            logger.error(f"Failed to remove all knowledge: {e}")
            return f"Error removing content: {str(e)}"

    def list_knowledge_contents(self) -> str:
        """
        List all content currently in the knowledge base.

        Returns:
            Formatted list of content with IDs and names
        """
        try:
            contents, _ = self.knowledge.get_content()

            if not contents:
                return "Knowledge base is empty. No content has been added yet."

            lines = ["Knowledge base contents:", ""]
            for content in contents:
                name = getattr(content, "name", "Unknown")
                content_id = getattr(content, "id", "Unknown")
                lines.append(f"- ID: {content_id}")
                lines.append(f"  Name: {name}")
                lines.append("")

            return "\n".join(lines)

        except Exception as e:
            logger.error(f"Failed to list knowledge: {e}")
            return f"Error listing content: {str(e)}"

    # def search_knowledge(self, query: str, limit: int = 5) -> str:
    #     """
    #     Search the knowledge base for relevant content.

    #     Args:
    #         query: The search query
    #         limit: Maximum number of results to return (default: 5)

    #     Returns:
    #         Formatted search results
    #     """
    #     try:
    #         results = self.knowledge.search(query=query, num_documents=limit)

    #         if not results:
    #             return f"No results found for query: '{query}'"

    #         lines = [f"Search results for '{query}':", ""]
    #         for i, doc in enumerate(results, 1):
    #             content_preview = (doc.content or "")[:200]
    #             if len(doc.content or "") > 200:
    #                 content_preview += "..."
    #             lines.append(f"{i}. {content_preview}")
    #             lines.append("")

    #         return "\n".join(lines)

    #     except Exception as e:
    #         logger.error(f"Failed to search knowledge: {e}")
    #         return f"Error searching content: {str(e)}"


def create_knowledge_tool(
    knowledge_name: str = "default_kb",
    collection: str = "default",
    description: str = "Default knowledge base",
) -> tuple[Knowledge, KnowledgeTool]:
    """
    Factory function to create a Knowledge instance with its management tool.

    Args:
        knowledge_name: Name for the knowledge base
        collection: Vector DB collection name
        description: Description of the knowledge base

    Returns:
        Tuple of (Knowledge, KnowledgeTool)
    """
    db = get_db_manager()

    knowledge = Knowledge(
        name=knowledge_name,
        description=description,
        contents_db=db.agno_db,
        vector_db=db.get_vector_db(collection),
    )

    tool = KnowledgeTool(knowledge=knowledge)

    return knowledge, tool

"""
Centralized SurrealDB connection management for Agno agents.

Usage (sync context):
    from utils.database import get_db_manager
    db_manager = get_db_manager()
    db_manager.connect_sync()

    agent = Agent(db=db_manager.agno_db, ...)

Usage (async context / notebook):
    from utils.database import get_db_manager
    db_manager = get_db_manager()
    await db_manager.connect_async()

    vector_db = db_manager.get_vector_db("my_collection")
    agent = Agent(db=db_manager.agno_db, knowledge=Knowledge(vector_db=vector_db), ...)
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Optional

from dotenv import load_dotenv
from surrealdb import AsyncSurreal, Surreal

from agno.db.surrealdb import SurrealDb as AgnoSurrealDb
from agno.vectordb.surrealdb import SurrealDb as SurrealVDb

from utils.models import Embedder, get_embedder

load_dotenv()


@dataclass
class SurrealDBConfig:
    """SurrealDB connection configuration."""

    url: str = field(
        default_factory=lambda: os.getenv("SURREALDB_URL", "ws://localhost:8000")
    )
    username: str = field(
        default_factory=lambda: os.getenv("SURREALDB_USERNAME", "root")
    )
    password: str = field(
        default_factory=lambda: os.getenv("SURREALDB_PASSWORD", "root")
    )
    namespace: str = field(
        default_factory=lambda: os.getenv("SURREALDB_NAMESPACE", "local_agent_memory")
    )
    database: str = field(
        default_factory=lambda: os.getenv("SURREALDB_DATABASE", "main_database")
    )

    @property
    def credentials(self) -> dict[str, str]:
        return {"username": self.username, "password": self.password}


class DatabaseManager:
    """
    Singleton manager for SurrealDB connections.

    Handles both sync and async clients, plus Agno-specific wrappers
    (AgnoSurrealDb for sessions/memories, SurrealVDb for vector search).
    """

    _instance: Optional[DatabaseManager] = None
    _initialized: bool = False

    def __new__(cls, config: Optional[SurrealDBConfig] = None) -> DatabaseManager:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, config: Optional[SurrealDBConfig] = None) -> None:
        if DatabaseManager._initialized:
            return

        self.config = config or SurrealDBConfig()
        self._sync_client: Optional[Surreal] = None
        self._async_client: Optional[AsyncSurreal] = None
        self._agno_db: Optional[AgnoSurrealDb] = None
        self._vector_dbs: dict[str, SurrealVDb] = {}
        self._sync_connected: bool = False
        self._async_connected: bool = False

        DatabaseManager._initialized = True

    @property
    def sync_client(self) -> Surreal:
        """Get the synchronous SurrealDB client (lazy init)."""
        if self._sync_client is None:
            self._sync_client = Surreal(url=self.config.url)
        return self._sync_client

    @property
    def async_client(self) -> AsyncSurreal:
        """Get the asynchronous SurrealDB client (lazy init)."""
        if self._async_client is None:
            self._async_client = AsyncSurreal(url=self.config.url)
        return self._async_client

    @property
    def agno_db(self) -> AgnoSurrealDb:
        """
        Get the Agno SurrealDb wrapper for sessions/memories/knowledge contents.
        This is what you pass to Agent(db=...).
        """
        if self._agno_db is None:
            # Ensure sync client is connected before creating AgnoSurrealDb
            if not self._sync_connected:
                self.connect_sync()
            self._agno_db = AgnoSurrealDb(
                self.sync_client,  # Pass the connected client instead of None
                self.config.url,
                self.config.credentials,
                self.config.namespace,
                self.config.database,
            )
        return self._agno_db

    def connect_sync(self) -> None:
        """Connect the synchronous client (for scripts)."""
        if self._sync_connected:
            return
        self.sync_client.signin(self.config.credentials)
        self.sync_client.use(
            namespace=self.config.namespace, database=self.config.database
        )
        self._sync_connected = True

    async def connect_async(self) -> None:
        """Connect the asynchronous client (for notebooks/async code)."""
        if self._async_connected:
            return
        await self.async_client.signin(self.config.credentials)
        await self.async_client.use(
            namespace=self.config.namespace, database=self.config.database
        )
        self._async_connected = True

    def connect_all_sync(self) -> None:
        """Connect both sync and async clients from a sync context.

        Note: For async client in sync context, you'll need to call
        connect_async() separately in an async context.
        """
        self.connect_sync()

    async def connect_all_async(self) -> None:
        """Connect both sync and async clients from an async context."""
        self.connect_sync()
        await self.connect_async()

    def get_vector_db(
        self,
        collection: str,
        embedder: Optional[Embedder] = None,
        efc: int = 150,
        m: int = 12,
        search_ef: int = 40,
    ) -> SurrealVDb:
        """
        Get or create a vector database for a collection.

        Args:
            collection: Name of the vector collection (e.g., "recipes", "documents")
            embedder: Embedder to use (defaults to OpenAIEmbedder)
            efc: HNSW efConstruction parameter
            m: HNSW M parameter
            search_ef: HNSW search ef parameter

        Returns:
            SurrealVDb instance configured for the collection
        """
        if collection not in self._vector_dbs:
            self._vector_dbs[collection] = SurrealVDb(
                client=self.sync_client,
                async_client=self.async_client,
                collection=collection,
                efc=efc,
                m=m,
                search_ef=search_ef,
                embedder=embedder or get_embedder(),
            )
        return self._vector_dbs[collection]

    def close_sync(self) -> None:
        """Close the synchronous client."""
        if self._sync_client is not None:
            self._sync_client.close()
            self._sync_client = None
            self._sync_connected = False

    async def close_async(self) -> None:
        """Close the asynchronous client."""
        if self._async_client is not None:
            await self._async_client.close()
            self._async_client = None
            self._async_connected = False

    async def close_all(self) -> None:
        """Close all clients."""
        self.close_sync()
        await self.close_async()
        self._vector_dbs.clear()

    @classmethod
    def reset(cls) -> None:
        """Reset the singleton (useful for testing)."""
        cls._instance = None
        cls._initialized = False


# Convenience function to get the singleton instance
def get_db_manager(config: Optional[SurrealDBConfig] = None) -> DatabaseManager:
    """Get the DatabaseManager singleton instance."""
    return DatabaseManager(config)

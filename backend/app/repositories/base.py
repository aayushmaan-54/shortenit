from collections.abc import Sequence
from typing import Any, ClassVar

from pymongo import AsyncMongoClient, IndexModel, MongoClient
from pymongo.asynchronous.collection import AsyncCollection
from pymongo.collection import Collection
from pymongo.errors import OperationFailure
from pymongo.operations import SearchIndexModel

from app.core.config import settings
from app.core.logger import logger


class BaseRepository:
    """
    Base repository for MongoDB, managing sync and async clients,
    collection connections, index creation, and session handling.
    """

    _sync_db_client: ClassVar[MongoClient] = MongoClient(
        settings.mongodb_uri, tz_aware=True
    )
    _async_db_client: ClassVar[AsyncMongoClient] = AsyncMongoClient(
        settings.mongodb_uri, tz_aware=True
    )
    _default_db_name: ClassVar[str] = settings.mongodb_database

    collection_name: ClassVar[str | None] = None
    db_name: ClassVar[str | None] = None
    # Tuples in subclasses: immutable, so no `ClassVar` annotation needed there
    indexes: ClassVar[Sequence[dict[str, Any]]] = ()
    search_indexes: ClassVar[Sequence[dict[str, Any]]] = ()

    _indexed_collections: ClassVar[set[str]] = set()

    sync_collection: Collection
    async_collection: AsyncCollection

    def __init__(self, collection_name: str | None = None):
        self._setup_connection(collection_name)
        self._create_indexes()

    @classmethod
    def _get_db_name(cls):
        db_name = cls.db_name or cls._default_db_name

        if not db_name:
            raise ValueError("MongoDB database name is not configured")

        return db_name

    def _setup_connection(self, collection_name: str | None = None):
        collection_name = collection_name or self.collection_name

        if not collection_name:
            raise ValueError("Collection name not defined")

        db_name = self._get_db_name()
        self.sync_collection = self._sync_db_client[db_name][collection_name]
        self.async_collection = self._async_db_client[db_name][collection_name]

    def _create_indexes(self):
        """
        Ensure indexes once per collection per process;
        uses sync client as `__init__` can't await
        """
        full_name = self.sync_collection.full_name

        if full_name in self._indexed_collections:
            return

        if self.indexes:
            self.sync_collection.create_indexes(
                [IndexModel(**index) for index in self.indexes]
            )

        if self.search_indexes:
            self._create_search_indexes()

        self._indexed_collections.add(full_name)

    def _create_search_indexes(self):
        """
        Create missing Atlas Search / Vector Search indexes;
        existing names are skipped as recreating raises, unlike regular indexes
        """
        try:
            existing = {
                index["name"] for index in self.sync_collection.list_search_indexes()
            }
            missing = [
                SearchIndexModel(**index)
                for index in self.search_indexes
                if index["name"] not in existing
            ]

            if missing:
                self.sync_collection.create_search_indexes(missing)

        except OperationFailure as exc:
            logger.warning(
                "Skipping search indexes for %s: %s",
                self.sync_collection.full_name,
                exc,
            )

    @classmethod
    async def ping(cls):
        """Check MongoDB is reachable; raises if not so startup fails fast"""
        await cls._async_db_client.admin.command("ping")

    @classmethod
    def _all_subclasses(cls) -> list[type["BaseRepository"]]:
        """All repository subclasses, including nested ones"""
        subclasses = []
        for subclass in cls.__subclasses__():
            subclasses.append(subclass)
            subclasses.extend(subclass._all_subclasses())
        return subclasses

    @classmethod
    def create_all_indexes(cls):
        """
        Instantiate every repository with a `collection_name` so indexes are built at startup;
        only repositories imported before startup are found (routers import them)
        """
        for repository in cls._all_subclasses():
            if repository.collection_name:
                repository()

    @classmethod
    def start_async_session(cls):
        return cls._async_db_client.start_session()

    @classmethod
    def start_sync_session(cls):
        return cls._sync_db_client.start_session()

    @classmethod
    async def shutdown(cls):
        cls._sync_db_client.close()
        await cls._async_db_client.close()

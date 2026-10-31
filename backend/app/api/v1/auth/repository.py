from datetime import UTC, datetime

from app.repositories.base import BaseRepository


class UserRepository(BaseRepository):
    collection_name = "users"
    indexes = (
        {"keys": {"email": 1}, "unique": True, "name": "uniq_email"},
        {"keys": {"username": 1}, "unique": True, "name": "uniq_username"},
    )

    async def create_user(self, username: str, email: str, password_hash: str):
        """
        Create User; returns inserted id
        """
        now = datetime.now(UTC)

        result = await self.async_collection.insert_one(
            {
                "username": username,
                "email": email,
                "password_hash": password_hash,
                "verified": False,
                "profile": None,
                "created_at": now,
                "updated_at": now,
            }
        )

        return str(result.inserted_id)

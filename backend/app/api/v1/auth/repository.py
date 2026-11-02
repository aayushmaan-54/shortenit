from datetime import UTC, datetime

from pymongo import ReturnDocument

from app.repositories.base import BaseRepository


class UserRepository(BaseRepository):
    collection_name = "users"
    indexes = (
        {"keys": {"email": 1}, "unique": True, "name": "uniq_email"},
        {"keys": {"username": 1}, "unique": True, "name": "uniq_username"},
    )

    async def create_user(self, username: str, email: str, password_hash: str):
        """
        Create User;
        returns inserted id;
        """
        now = datetime.now(UTC)

        result = await self.async_collection.insert_one(
            {
                "username": username,
                "email": email,
                "password_hash": password_hash,
                "is_verified": False,
                "profile": None,
                "created_at": now,
                "updated_at": now,
            }
        )

        return str(result.inserted_id)

    async def verify_user(self, email: str):
        """
        Mark an unverified user as verified;
        returns the updated user;
        """
        return await self.async_collection.find_one_and_update(
            {"email": email, "is_verified": False},
            {"$set": {"is_verified": True, "updated_at": datetime.now(UTC)}},
            projection={"password_hash": 0},
            return_document=ReturnDocument.AFTER,
        )

    async def get_unverified_user(self, email: str):
        """Get an unverified user's id by email; None if not found / already verified"""
        return await self.async_collection.find_one(
            {"email": email, "is_verified": False}, projection={"_id": 1}
        )

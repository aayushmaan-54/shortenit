from pymongo.errors import DuplicateKeyError

from app.api.v1.auth.repository import UserRepository
from app.clients import redis_client
from app.core import logger
from app.core.exceptions import ConflictException
from app.core.redis_keys import OTP_COOLDOWN_TTL, OTP_TTL, OtpPurpose, RedisKey
from app.core.security import create_hardened_hash, create_keyed_hash, create_otp

DUPLICATE_FIELD_MESSAGES = {
    "username": "Username is already taken",
    "email": "Email is already registered",
}


class AuthService:
    async def _send_otp(self, purpose: OtpPurpose, email: str):
        """
        Generate an OTP, store only its keyed hash with a TTL, start resend cooldown;
        a new OTP replaces the old one and resets its failed attempts;
        """
        otp = create_otp()

        logger.debug(f"Email verification OTP generated: {otp}")

        async with redis_client.pipeline(transaction=True) as pipe:
            pipe.set(RedisKey.otp(purpose, email), create_keyed_hash(otp), ex=OTP_TTL)
            pipe.delete(RedisKey.otp_attempts(purpose, email))
            pipe.set(RedisKey.otp_cooldown(purpose, email), 1, ex=OTP_COOLDOWN_TTL)
            await pipe.execute()

        # TODO: send `otp` via email client (background task)

    async def sign_up(self, username: str, email: str, password: str):
        """
        Create an unverified user and send an email verification OTP;
        uniqueness is enforced by the unique indexes;
        """
        password_hash = create_hardened_hash(password)

        try:
            user_id = await UserRepository().create_user(
                username=username, email=email, password_hash=password_hash
            )
        except DuplicateKeyError as exc:
            duplicate_field = next(iter((exc.details or {}).get("keyPattern", {})), "")

            message = DUPLICATE_FIELD_MESSAGES.get(
                duplicate_field, "Account already exists"
            )

            raise ConflictException(message) from None

        await self._send_otp(purpose="verify_email", email=email)

        return {
            "message": "Account created. We've sent a verification code to your email",
            "user_id": user_id,
        }

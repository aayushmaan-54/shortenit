from typing import cast

from pymongo.errors import DuplicateKeyError

from app.api.v1.auth.repository import UserRepository
from app.clients import redis_client
from app.core import logger, settings
from app.core.exceptions import (
    BadRequestException,
    ConflictException,
    NotFoundException,
    TooManyRequestsException,
)
from app.core.redis_keys import OtpPurpose, RedisKey
from app.core.security import (
    create_hardened_hash,
    create_keyed_hash,
    create_otp,
    verify_keyed_hash,
)

ONE_DAY_SECONDS = 86_400

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

        logger.debug("OTP generated for %s (%s): %s", email, purpose, otp)

        async with redis_client.pipeline(transaction=True) as pipe:
            pipe.set(
                RedisKey.otp(purpose, email),
                create_keyed_hash(otp),
                ex=settings.otp_expires_in,
            )
            pipe.delete(RedisKey.otp_attempts(purpose, email))
            pipe.set(
                RedisKey.otp_cooldown(purpose, email),
                1,
                ex=settings.otp_resend_cooldown,
            )
            pipe.incr(RedisKey.otp_daily_count(purpose, email))
            # NX: window starts at the first OTP of the day, later sends don't extend it
            pipe.expire(
                RedisKey.otp_daily_count(purpose, email), ONE_DAY_SECONDS, nx=True
            )
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

    async def confirm_user(self, email: str, otp: str):
        """
        Verify email OTP and mark user as verified;
        """
        otp_key = RedisKey.otp("verify_email", email)
        attempts_key = RedisKey.otp_attempts("verify_email", email)

        otp_hash = cast(str | None, await redis_client.get(otp_key))
        if not otp_hash:
            raise BadRequestException(
                "Invalid or expired code. Please request a new one"
            )

        async with redis_client.pipeline(transaction=True) as pipe:
            pipe.incr(attempts_key)
            pipe.expire(attempts_key, settings.otp_expires_in)
            attempts, _ = await pipe.execute()

        if attempts > settings.otp_max_attempts:
            await redis_client.delete(otp_key)
            raise BadRequestException(
                "Too many incorrect attempts. Please request a new code"
            )

        if not verify_keyed_hash(otp, otp_hash):
            remaining = settings.otp_max_attempts - attempts
            if remaining:
                raise BadRequestException(f"Invalid code. {remaining} attempt(s) left")

            await redis_client.delete(otp_key)
            raise BadRequestException("Invalid code. Please request a new one")

        user = await UserRepository().verify_user(email=email)

        await redis_client.delete(otp_key, attempts_key)

        if user is None:
            raise NotFoundException("User not found or already verified")

        return user

    async def resend_confirmation_email(self, email: str):
        """
        Resend email verification OTP;
        same response whether or not the account exists, so emails can't be enumerated
        """
        cooldown_key = RedisKey.otp_cooldown("verify_email", email)
        daily_count_key = RedisKey.otp_daily_count("verify_email", email)

        if not await redis_client.set(
            cooldown_key, 1, ex=settings.otp_resend_cooldown, nx=True
        ):
            retry_after = await redis_client.ttl(cooldown_key)
            raise TooManyRequestsException(
                retry_after=max(retry_after, 1),
                message="Please wait before requesting a new code",
            )

        daily_count = cast(str | None, await redis_client.get(daily_count_key))
        if daily_count and int(daily_count) >= settings.otp_daily_limit:
            retry_after = await redis_client.ttl(daily_count_key)
            raise TooManyRequestsException(
                retry_after=max(retry_after, 1),
                message="Daily limit reached. Please try again tomorrow",
            )

        if await UserRepository().get_unverified_user(email=email):
            await self._send_otp(purpose="verify_email", email=email)

        return {
            "message": "If an unverified account exists for this email, we've sent a new code"
        }

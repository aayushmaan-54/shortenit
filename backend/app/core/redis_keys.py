from typing import Literal

# Format: `shortenit:<feature>:<entity>:<id>`
REDIS_KEY_PREFIX = "shortenit"

OtpPurpose = Literal["verify_email", "reset_password"]


class RedisKey:
    """Single source of Redis key names"""

    # --------------- Auth ---------------
    @staticmethod
    def token_family(family_id: str):
        return f"{REDIS_KEY_PREFIX}:auth:family:{family_id}"

    @staticmethod
    def token_grace(jti: str):
        return f"{REDIS_KEY_PREFIX}:auth:grace:{jti}"

    @staticmethod
    def user_families(user_id: str):
        return f"{REDIS_KEY_PREFIX}:auth:user_families:{user_id}"

    # --------------- OTP ---------------
    @staticmethod
    def otp(purpose: OtpPurpose, email: str):
        return f"{REDIS_KEY_PREFIX}:auth:otp:{purpose}:{email}"

    @staticmethod
    def otp_attempts(purpose: OtpPurpose, email: str):
        return f"{REDIS_KEY_PREFIX}:auth:otp_attempts:{purpose}:{email}"

    @staticmethod
    def otp_cooldown(purpose: OtpPurpose, email: str):
        return f"{REDIS_KEY_PREFIX}:auth:otp_cooldown:{purpose}:{email}"

    @staticmethod
    def otp_daily_count(purpose: OtpPurpose, email: str):
        return f"{REDIS_KEY_PREFIX}:auth:otp_daily_count:{purpose}:{email}"

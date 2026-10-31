from .config import settings
from .exception_handlers import (
    app_exception_handler,
    build_error_response,
    exception_handlers,
)
from .exceptions import (
    AppException,
    BadRequestException,
    ConflictException,
    ForbiddenException,
    NotFoundException,
    PayloadTooLargeException,
    TooManyRequestsException,
    UnauthorizedException,
)
from .logger import logger
from .redis_keys import (
    GRACE_TTL,
    OTP_COOLDOWN_TTL,
    OTP_TTL,
    OtpPurpose,
    RedisKey,
)
from .security import (
    create_access_token,
    create_fast_hash,
    create_hardened_hash,
    create_refresh_token,
    decode_access_token,
    decode_refresh_token,
    decrypt_entity,
    encrypt_entity,
    get_current_user_id,
    verify_and_update_hardened_hash,
    verify_fast_hash,
    verify_hardened_hash,
)

# `lifespan` is not re-exported: it imports `app.clients`, which imports `app.core` (circular)

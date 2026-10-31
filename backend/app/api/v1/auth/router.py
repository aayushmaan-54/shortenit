from fastapi import APIRouter, status

from app.api.v1.auth.schema import SignUpRequest, SignUpResponse
from app.api.v1.auth.service import AuthService
from app.schemas.response import ApiResponse

# Prefix: /api/v1/auth/
router = APIRouter()


@router.post(
    "/sign-up",
    response_model=ApiResponse[SignUpResponse],
    status_code=status.HTTP_201_CREATED,
)
async def sign_up(user_data: SignUpRequest):
    """Create User"""
    result = await AuthService().sign_up(
        username=user_data.username, email=user_data.email, password=user_data.password
    )

    return ApiResponse(
        message=result["message"],
        data=SignUpResponse(id=result["user_id"], email=user_data.email),
    )

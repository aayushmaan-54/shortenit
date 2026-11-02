from fastapi import APIRouter, BackgroundTasks, status

from app.api.v1.auth.schema import (
    ConfirmUserRequest,
    ConfirmUserResponse,
    ResendConfirmationEmailRequest,
    SignUpRequest,
    SignUpResponse,
)
from app.api.v1.auth.service import AuthService
from app.schemas.response import ApiResponse
from app.schemas.types import PyObjectId

# Prefix: /api/v1/auth/
router = APIRouter()


@router.post(
    "/sign-up",
    response_model=ApiResponse[SignUpResponse],
    status_code=status.HTTP_201_CREATED,
)
async def sign_up(user_data: SignUpRequest, background_tasks: BackgroundTasks):
    """Create User"""
    result = await AuthService().sign_up(
        username=user_data.username,
        email=user_data.email,
        password=user_data.password,
        background_tasks=background_tasks,
    )

    return ApiResponse(
        message=result["message"],
        data=SignUpResponse(id=PyObjectId(result["user_id"]), email=user_data.email),
    )


@router.post("/user/confirm", response_model=ApiResponse[ConfirmUserResponse])
async def confirm_user(payload: ConfirmUserRequest):
    """Confirm User"""
    user = await AuthService().confirm_user(email=payload.email, otp=payload.otp)

    return ApiResponse(
        message="Email verified successfully",
        data=ConfirmUserResponse.model_validate(user),
    )


@router.post("/user/confirm/resend", response_model=ApiResponse[None])
async def resend_confirmation_email(
    payload: ResendConfirmationEmailRequest, background_tasks: BackgroundTasks
):
    """Resend Confirmation Email"""
    result = await AuthService().resend_confirmation_email(
        email=payload.email, background_tasks=background_tasks
    )

    return ApiResponse(message=result["message"])

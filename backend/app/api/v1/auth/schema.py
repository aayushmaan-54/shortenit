from datetime import datetime

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    ValidationInfo,
    field_validator,
)

from app.schemas.types import PyObjectId


class SignUpRequest(BaseModel):
    """SignUp Request Model"""

    model_config = ConfigDict(extra="forbid")

    username: str = Field(
        ...,
        min_length=3,
        max_length=30,
        pattern=r"^[a-zA-Z0-9_.]+$",
        description="Only alphanumeric characters,  underscores & . allowed.",
    )
    email: EmailStr
    password: str = Field(
        ...,
        min_length=8,
        max_length=64,
        description="Must be between 8 and 64 characters.",
    )

    @field_validator("email", "username", mode="before")
    @classmethod
    def format_string(cls, value: str, info: ValidationInfo):
        if isinstance(value, str):
            value = value.strip()
            if info.field_name == "email":
                value = value.lower()
        return value


class SignUpResponse(BaseModel):
    """SignUp Response Model"""

    id: PyObjectId
    email: str


class ConfirmUserRequest(BaseModel):
    """Confirm User Request Model"""

    model_config = ConfigDict(extra="forbid")

    email: EmailStr
    otp: str = Field(
        ...,
        pattern=r"^\d{6}$",
        description="6-digit One Time Password (OTP) sent to the user's email.",
    )

    @field_validator("email", mode="before")
    @classmethod
    def format_email(cls, value: str):
        if isinstance(value, str):
            value = value.strip().lower()
        return value


class ConfirmUserResponse(BaseModel):
    """Confirm User Response Model"""

    id: PyObjectId = Field(validation_alias="_id")
    email: str
    username: str
    is_verified: bool
    created_at: datetime
    updated_at: datetime


class ResendConfirmationEmailRequest(BaseModel):
    """Resend Confirmation Email Request Model"""

    model_config = ConfigDict(extra="forbid")

    email: EmailStr

    @field_validator("email", mode="before")
    @classmethod
    def format_email(cls, value: str):
        if isinstance(value, str):
            value = value.strip().lower()
        return value

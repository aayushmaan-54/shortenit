from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    ValidationInfo,
    field_validator,
)


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

    id: str
    email: str

from pydantic import BaseModel


class SignUpRequest(BaseModel):
    """SignUp Request Model"""

    username: str
    email: str
    password: str

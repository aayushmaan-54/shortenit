from pydantic import BaseModel


class ApiResponse[T](BaseModel):
    """
    Standard success envelope;
    """

    success: bool = True
    message: str | None = None
    data: T

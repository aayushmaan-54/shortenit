from pydantic import BaseModel, ConfigDict, Field

from .types import PyObjectId


class MongoModel(BaseModel):
    """
    Base model for MongoDB documents;
    maps Mongo `_id` to `id`, accepts either on input
    """

    model_config = ConfigDict(validate_by_name=True, validate_by_alias=True)

    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")

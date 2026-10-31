from typing import Any

from bson import ObjectId
from pydantic import GetJsonSchemaHandler
from pydantic_core import core_schema


class PyObjectId(ObjectId):
    """
    Custom BSON ObjectId type for Pydantic models, providing ObjectId validation,
    string serialization, and JSON Schema support.
    """

    @classmethod
    def __get_pydantic_core_schema__(cls, _source_type: Any, _handler: Any):
        def validate(value: str | ObjectId):
            if not ObjectId.is_valid(value):
                raise ValueError("Invalid ObjectId")
            return ObjectId(value)

        return core_schema.no_info_plain_validator_function(
            function=validate, serialization=core_schema.to_string_ser_schema()
        )

    @classmethod
    def __get_pydantic_json_schema__(
        cls, _core_schema: core_schema.CoreSchema, handler: GetJsonSchemaHandler
    ):
        return handler(core_schema.str_schema())

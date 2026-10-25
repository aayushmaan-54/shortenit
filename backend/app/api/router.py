from fastapi import APIRouter

from .v1 import v1_router

api_router = APIRouter()

# Prefix: /api/v1
api_router.include_router(v1_router, prefix="/v1")

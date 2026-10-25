from fastapi import APIRouter

from .auth import auth_router

v1_router = APIRouter()

# Prefix: /api/v1/auth
v1_router.include_router(auth_router, prefix="/auth", tags=["v1 - Auth"])

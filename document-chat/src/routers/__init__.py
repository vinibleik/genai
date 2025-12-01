from fastapi import APIRouter

from .chat import router as chat_router

api = APIRouter()
api.include_router(chat_router)

__all__ = ["api"]

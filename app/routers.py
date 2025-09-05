from fastapi import APIRouter

from app.api import router as api_router
from app.api.health import router as health_router
from app.web.auth_views import router as web_auth_router
from app.web.notes_views import router as web_notes_router
from app.web.chat_views import router as web_chat_router

root_router = APIRouter()
root_router.include_router(api_router)
root_router.include_router(health_router)
root_router.include_router(web_auth_router)
root_router.include_router(web_notes_router)
root_router.include_router(web_chat_router)

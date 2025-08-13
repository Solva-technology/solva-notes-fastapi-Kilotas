from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware

from app.api import router as api_router
from app.core.config import settings
from app.db.session import init_db
from app.admin import setup_admin

app = FastAPI(title="Note App")
app.add_middleware(SessionMiddleware, secret_key=settings.SECRET_KEY)
setup_admin(app)

@app.get("/ping")
async def ping():
    return {"status": "ok"}

app.include_router(api_router)

@app.on_event("startup")
async def on_startup():
    if settings.APP_DEBUG:
        await init_db()

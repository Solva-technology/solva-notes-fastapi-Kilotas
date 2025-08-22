from contextlib import asynccontextmanager

from fastapi import FastAPI
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from sqladmin.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from starlette.staticfiles import StaticFiles

from app.admin import setup_admin
from app.api import router as api_router
from app.api.health import router as health_router
from app.core.config import settings
from app.core.limiting import limiter
from app.db.session import engine, init_db
from app.web.auth_views import router as web_auth_router
from app.web.notes_views import router as web_notes_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    if settings.APP_DEBUG:
        await init_db()

    yield

    await engine.dispose()


app = FastAPI(title="Note App", lifespan=lifespan)
app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")

app.add_middleware(SessionMiddleware, secret_key=settings.SECRET_KEY)
setup_admin(app)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

app.include_router(api_router)
app.include_router(health_router)
app.include_router(web_auth_router)
app.include_router(web_notes_router)

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.templating import Jinja2Templates
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from starlette.middleware.sessions import SessionMiddleware
from starlette.staticfiles import StaticFiles

from app.admin import setup_admin
from app.api import router as api_router
from app.api.health import router as health_router
from app.chat.redis_client import redis_client
from app.core.config import settings
from app.core.limiting import limiter
from app.db.session import engine, init_db, logger
from app.web.auth_views import router as web_auth_router
from app.web.chat_views import router as web_chat_router
from app.web.notes_views import router as web_notes_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    if settings.APP_DEBUG:
        await init_db()

    try:
        await redis_client.connect()
        logger.info("✅ Redis connected successfully")
        app.state.redis_available = True
    except Exception as e:
        logger.error(f"❌ Redis connection failed: {e}")
        logger.warning("Continuing without Redis - using in-memory storage")
        app.state.redis_available = False

    yield

    try:
        await engine.dispose()
        logger.info("Database engine disposed")
    except Exception as e:
        logger.error(f"Error disposing database engine: {e}")

    if hasattr(app.state, "redis_available") and app.state.redis_available:
        try:
            await redis_client.disconnect()
            logger.info("✅ Redis disconnected successfully")
        except Exception as e:
            logger.error(f"❌ Redis disconnection error: {e}")

    yield

    await engine.dispose()


app = FastAPI(title="Note App", lifespan=lifespan)


APP_DIR = Path(__file__).resolve().parent
ROOT_DIR = APP_DIR.parent
STATIC_DIR = ROOT_DIR / "static"

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

templates = Jinja2Templates(directory="app/templates")

app.add_middleware(SessionMiddleware, secret_key=settings.SECRET_KEY)
setup_admin(app)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

app.include_router(api_router)
app.include_router(health_router)
app.include_router(web_auth_router)
app.include_router(web_notes_router)
app.include_router(web_chat_router)

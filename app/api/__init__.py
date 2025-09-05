from fastapi import APIRouter

from .auth import router as auth_router
from .categories import router as categories_router
from .notes import router as notes_router

router = APIRouter(prefix="/api/v1")


routes = [
    (auth_router, "/auth", ["auth"]),
    (categories_router, "/categories", ["categories"]),
    (notes_router, "/notes", ["notes"]),
]

for r, prefix, tags in routes:
    router.include_router(r, prefix=prefix, tags=tags)

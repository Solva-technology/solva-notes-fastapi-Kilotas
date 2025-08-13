from fastapi import APIRouter
from .auth import router as auth_router
from .categories import router as categories_router
from .notes import router as notes_router

router = APIRouter(prefix="/api/v1")
router.include_router(auth_router)
router.include_router(categories_router)
router.include_router(notes_router)

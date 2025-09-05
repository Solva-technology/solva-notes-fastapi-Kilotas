from typing import TypeVar, Type, Callable, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from app.db.base import Base

ModelT = TypeVar("ModelT", bound=Base)


async def get_obj_or_404(
    session: AsyncSession,
    model: Type[ModelT],
    obj_id: int,
    *,
    id_field: str = "id",
    allow: Optional[Callable[[ModelT], bool]] = None,
    not_found_msg: Optional[str] = None,
) -> ModelT:
    res = await session.execute(select(model).where(getattr(model, id_field) == obj_id))
    obj = res.scalar_one_or_none()
    if obj is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=not_found_msg or f"{model.__name__} not found",
        )
    if allow is not None and not allow(obj):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    return obj


async def ensure_exists_or_400(
    session: AsyncSession,
    model: Type[ModelT],
    value: int,
    *,
    field: str = "id",
    message: Optional[str] = None,
) -> ModelT:
    res = await session.execute(select(model).where(getattr(model, field) == value))
    obj = res.scalar_one_or_none()
    if obj is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message or f"{model.__name__} does not exist",
        )
    return obj

from fastapi import Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.models import Category, Note, User
from app.db.session import get_session


async def get_category_or_404(
    category_id: int,
    session: AsyncSession = Depends(get_session),
) -> Category:
    res = await session.execute(select(Category).where(Category.id == category_id))
    category = res.scalar_one_or_none()
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Category not found"
        )
    return category


async def get_note_or_404(
    note_id: int,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> Note:
    res = await session.execute(select(Note).where(Note.id == note_id))
    note = res.scalar_one_or_none()
    if not note or not (note.owner_id == user.id or user.is_admin):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Note not found"
        )
    return note


async def get_category_or_400(
    category_id: int,
    session: AsyncSession = Depends(get_session),
) -> Category:
    """Проверяет, что категория с таким id существует.
    Если нет — выбрасывает 400 Bad Request.
    """
    res = await session.execute(select(Category).where(Category.id == category_id))
    category = res.scalar_one_or_none()
    if category is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Category does not exist",
        )
    return category

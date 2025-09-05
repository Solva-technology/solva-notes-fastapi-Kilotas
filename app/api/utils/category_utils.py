from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_current_user
from app.db.session import get_session
from app.db.models import Category, Note, User
from app.api.utils.db_utils import get_obj_or_404, ensure_exists_or_400


async def get_category_or_404(
    category_id: int,
    session: AsyncSession = Depends(get_session),
) -> Category:
    return await get_obj_or_404(
        session, Category, category_id, not_found_msg="Category not found"
    )


async def get_note_or_404(
    note_id: int,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> Note:
    return await get_obj_or_404(
        session,
        Note,
        note_id,
        not_found_msg="Note not found",
        allow=lambda n: (n.owner_id == user.id) or user.is_admin,
    )


async def get_category_or_400(
    category_id: int,
    session: AsyncSession = Depends(get_session),
) -> Category:
    return await ensure_exists_or_400(
        session, Category, category_id, message="Category does not exist"
    )

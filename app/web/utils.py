import logging

from fastapi import HTTPException, Request, status
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Category, Note, User

logger = logging.getLogger(__name__)


async def get_current_user(request: Request, session: AsyncSession) -> User | None:
    """Получить текущего пользователя из сессии"""
    uid = request.session.get("user_id")
    if uid:
        user = await session.get(User, uid)
        if user:
            logger.debug(f"User found: {user.id}, {user.email}")
        else:
            logger.warning(f"User not found for ID: {uid}")
        return user
    logger.debug("No user_id in session")
    return None


async def require_authenticated_user(user: User | None) -> User:
    """Проверить аутентификацию пользователя"""
    if not user:
        logger.warning("Unauthorized access attempt")
        raise HTTPException(
            status_code=status.HTTP_302_FOUND, headers={"Location": "/login-html"}
        )
    logger.debug(f"User authenticated: {user.id}")
    return user


async def get_user_note(note_id: int, user: User, session: AsyncSession) -> Note | None:
    """Получить заметку пользователя или None если нет прав"""
    note = await session.get(Note, note_id)
    if note:
        if note.owner_id == user.id:
            logger.debug(f"Note accessed: {note_id} by user: {user.id}")
            return note
        else:
            logger.warning(f"Access denied to note: {note_id} by user: {user.id}")
    else:
        logger.warning(f"Note not found: {note_id}")
    return None


def require_note_access(note: Note | None) -> RedirectResponse | None:
    """Проверить доступ к заметке и вернуть редирект если нет прав"""
    if not note:
        logger.warning("Note access denied - redirecting to notes list")
        return RedirectResponse("/ui/notes", status_code=status.HTTP_302_FOUND)
    logger.debug("Note access granted")
    return None


async def get_all_categories(session: AsyncSession) -> list[Category]:
    """Получить все категории"""
    result = await session.execute(select(Category))
    categories = result.scalars().all()
    logger.debug(f"Loaded {len(categories)} categories")
    return categories

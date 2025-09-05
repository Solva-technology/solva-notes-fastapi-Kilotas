from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import User


def normalize_email(email: str) -> str:
    return (email or "").strip().lower()


async def get_user_by_email(session: AsyncSession, email: str) -> Optional[User]:
    email = normalize_email(email)
    res = await session.execute(select(User).where(User.email == email))
    return res.scalar_one_or_none()
from __future__ import annotations

from sqlalchemy import Boolean, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.constants import USER_EMAIL_MAX_LENGTH, USER_PASSWORD_MAX_LENGTH
from app.db.base import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(
        String(USER_EMAIL_MAX_LENGTH), unique=True, index=True, nullable=False
    )
    hashed_password: Mapped[str] = mapped_column(
        String(USER_PASSWORD_MAX_LENGTH), nullable=False
    )
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)

    # строковые аннотации или __future__ спасают от цикличности
    notes: Mapped[list["Note"]] = relationship(
        back_populates="owner", cascade="all, delete-orphan"
    )

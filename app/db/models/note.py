from __future__ import annotations

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.constants import NOTE_TITLE_MAX_LENGTH
from app.db.base import Base


class Note(Base):
    __tablename__ = "notes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(NOTE_TITLE_MAX_LENGTH), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)

    owner_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    category_id: Mapped[int] = mapped_column(
        ForeignKey("categories.id"), index=True, nullable=False
    )

    owner: Mapped["User"] = relationship(back_populates="notes")
    category: Mapped["Category"] = relationship(back_populates="notes")

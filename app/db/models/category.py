from __future__ import annotations

from sqlalchemy import Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.constants import CATEGORY_NAME_MAX_LENGTH
from app.db.base import Base


class Category(Base):
    __tablename__ = "categories"
    __table_args__ = (UniqueConstraint("name", name="uq_categories_name"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(
        String(CATEGORY_NAME_MAX_LENGTH), index=True, nullable=False
    )

    notes: Mapped[list["Note"]] = relationship(back_populates="category")

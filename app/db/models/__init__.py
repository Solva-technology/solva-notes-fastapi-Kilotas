from app.db.base import Base

from .category import Category
from .note import Note
from .user import User

__all__ = ["Base", "User", "Category", "Note"]
metadata = Base.metadata

from typing import Optional

from pydantic import BaseModel, ConfigDict


class NoteBase(BaseModel):
    title: str
    content: str
    category_id: int


class NoteCreate(NoteBase):
    pass


class NoteUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    category_id: Optional[int] = None


class NoteOut(NoteBase):
    id: int
    owner_id: int
    model_config = ConfigDict(from_attributes=True)

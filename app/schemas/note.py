from pydantic import BaseModel, ConfigDict
from typing import Optional

class NoteCreate(BaseModel):
    title: str
    content: str
    category_id: int

class NoteUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    category_id: Optional[int] = None

class NoteOut(BaseModel):
    id: int
    title: str
    content: str
    owner_id: int
    category_id: int
    model_config = ConfigDict(from_attributes=True)

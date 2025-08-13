from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import get_session
from app.db.models import Note, Category, User
from app.schemas.note import NoteCreate, NoteUpdate, NoteOut
from app.api.deps import get_current_user

router = APIRouter(prefix="/notes", tags=["notes"])


def can_access(note: Note, user: User) -> bool:
    return note.owner_id == user.id or user.is_admin


@router.get("/", response_model=list[NoteOut])
async def list_notes(
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    stmt = select(Note)
    if not user.is_admin:
        stmt = stmt.where(Note.owner_id == user.id)
    res = await session.execute(stmt.order_by(Note.id.desc()))
    return res.scalars().all()


@router.get("/{note_id}", response_model=NoteOut)
async def get_note(
    note_id: int,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    res = await session.execute(select(Note).where(Note.id == note_id))
    note = res.scalar_one_or_none()
    if not note or not can_access(note, user):
        raise HTTPException(status_code=404, detail="Note not found")
    return note


@router.post("/", response_model=NoteOut, status_code=201)
async def create_note(
    data: NoteCreate,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    # категория должна существовать
    r = await session.execute(select(Category).where(Category.id == data.category_id))
    if not r.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Category does not exist")

    note = Note(
        title=data.title,
        content=data.content,
        category_id=data.category_id,
        owner_id=user.id,
    )
    session.add(note)
    await session.commit()
    await session.refresh(note)
    return note


@router.put("/{note_id}", response_model=NoteOut)
async def update_note(
    note_id: int,
    data: NoteUpdate,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    res = await session.execute(select(Note).where(Note.id == note_id))
    note = res.scalar_one_or_none()
    if not note or not can_access(note, user):
        raise HTTPException(status_code=404, detail="Note not found")

    if data.title is not None:
        note.title = data.title
    if data.content is not None:
        note.content = data.content
    if data.category_id is not None:
        r = await session.execute(
            select(Category).where(Category.id == data.category_id)
        )
        if not r.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Category does not exist")
        note.category_id = data.category_id

    await session.commit()
    await session.refresh(note)
    return note


@router.delete("/{note_id}", status_code=204)
async def delete_note(
    note_id: int,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    res = await session.execute(select(Note).where(Note.id == note_id))
    note = res.scalar_one_or_none()
    if not note or not can_access(note, user):
        raise HTTPException(status_code=404, detail="Note not found")
    await session.delete(note)
    await session.commit()
    return None

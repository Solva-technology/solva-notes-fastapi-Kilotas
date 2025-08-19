from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from app.api.deps import get_current_user
from app.api.utils.category_utils import get_category_or_400, get_note_or_404
from app.db.models import Category, Note, User
from app.db.session import get_session, logger
from app.schemas.note import NoteCreate, NoteOut, NoteUpdate

router = APIRouter(prefix="/notes", tags=["notes"])


@router.post("/", response_model=NoteOut, status_code=status.HTTP_201_CREATED)
async def create_note(
    data: NoteCreate,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    await get_category_or_400(data.category_id, session)

    note = Note(
        title=data.title,
        content=data.content,
        category_id=data.category_id,
        owner_id=user.id,
    )
    session.add(note)
    await session.commit()
    await session.refresh(note)

    logger.info(
        "create_note_ok",
        extra={"note_id": note.id, "user_id": user.id, "category_id": note.category_id},
    )
    return note


@router.get("/{note_id}", response_model=NoteOut)
async def get_note(note: Note = Depends(get_note_or_404)):
    logger.info("get_note_ok", extra={"note_id": note.id, "owner_id": note.owner_id})
    return note


@router.put("/{note_id}", response_model=NoteOut)
async def update_note(
    data: NoteUpdate,
    note: Note = Depends(get_note_or_404),
    session: AsyncSession = Depends(get_session),
):
    if data.title is not None:
        note.title = data.title
    if data.content is not None:
        note.content = data.content
    if data.category_id is not None:
        r = await session.execute(
            select(Category).where(Category.id == data.category_id)
        )
        if not r.scalar_one_or_none():
            logger.warning(
                "update_note_bad_category",
                extra={
                    "note_id": note.id,
                    "user_id": note.owner_id,
                    "category_id": data.category_id,
                },
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Category does not exist",
            )
        note.category_id = data.category_id

    await session.commit()
    await session.refresh(note)

    logger.info("update_note_ok", extra={"note_id": note.id, "user_id": note.owner_id})
    return note


@router.delete("/{note_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_note(
    note: Note = Depends(get_note_or_404),
    session: AsyncSession = Depends(get_session),
):
    await session.delete(note)
    await session.commit()

    logger.info("delete_note_ok", extra={"note_id": note.id, "user_id": note.owner_id})
    return None

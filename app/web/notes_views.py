from fastapi import APIRouter, Depends, Form, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.templates import templates
from app.db.models import Category, Note, User
from app.db.session import get_session
from app.web.utils import (
    get_all_categories,
    get_current_user,
    get_user_note,
    logger,
    require_authenticated_user,
    require_note_access,
)

router = APIRouter(prefix="/ui")


async def current_user_dependency(
    request: Request, session: AsyncSession = Depends(get_session)
) -> User | None:
    return await get_current_user(request, session)


@router.get("/", response_class=HTMLResponse)
async def index(request: Request, user: User | None = Depends(current_user_dependency)):
    return templates.TemplateResponse("index.html", {"request": request, "user": user})


@router.get("/notes", response_class=HTMLResponse)
async def notes_list(
    request: Request,
    user: User | None = Depends(current_user_dependency),
    session: AsyncSession = Depends(get_session),
):
    user = await require_authenticated_user(user)

    notes_stmt = select(Note).where(Note.owner_id == user.id)
    result = await session.execute(notes_stmt)
    notes = result.scalars().all()

    logger.debug(f"User {user.id} has {len(notes)} notes")

    return templates.TemplateResponse(
        "notes_list.html", {"request": request, "notes": notes, "user": user}
    )


@router.get("/notes/new", response_class=HTMLResponse)
async def notes_new_page(
    request: Request,
    user: User | None = Depends(current_user_dependency),
    session: AsyncSession = Depends(get_session),
):
    user = await require_authenticated_user(user)
    categories = await get_all_categories(session)

    return templates.TemplateResponse(
        "notes_new.html", {"request": request, "user": user, "categories": categories}
    )


@router.post("/notes/new")
async def notes_new_submit(
    request: Request,
    title: str = Form(...),
    content: str = Form(...),
    category_id: int = Form(...),
    session: AsyncSession = Depends(get_session),
    user: User = Depends(current_user_dependency),
):
    user = await require_authenticated_user(user)

    note = Note(title=title, content=content, category_id=category_id, owner_id=user.id)

    session.add(note)
    await session.commit()
    await session.refresh(note)

    logger.info(f"New note created: {note.id} by user: {user.id}")

    return RedirectResponse(f"/ui/notes/{note.id}", status_code=status.HTTP_302_FOUND)


@router.get("/notes/{note_id}", response_class=HTMLResponse)
async def notes_detail(
    note_id: int,
    request: Request,
    user: User | None = Depends(current_user_dependency),
    session: AsyncSession = Depends(get_session),
):
    user = await require_authenticated_user(user)
    note = await get_user_note(note_id, user, session)

    redirect = require_note_access(note)
    if redirect:
        return redirect

    return templates.TemplateResponse(
        "note_detail.html", {"request": request, "user": user, "note": note}
    )


@router.get("/notes/{note_id}/edit", response_class=HTMLResponse)
async def notes_edit_page(
    note_id: int,
    request: Request,
    user: User | None = Depends(current_user_dependency),
    session: AsyncSession = Depends(get_session),
):
    user = await require_authenticated_user(user)
    note = await get_user_note(note_id, user, session)

    redirect = require_note_access(note)
    if redirect:
        return redirect

    categories = await get_all_categories(session)

    return templates.TemplateResponse(
        "notes_edit.html",
        {"request": request, "user": user, "note": note, "categories": categories},
    )


@router.post("/notes/{note_id}/edit")
async def notes_edit_submit(
    note_id: int,
    request: Request,
    title: str = Form(...),
    content: str = Form(...),
    category_id: int = Form(...),
    session: AsyncSession = Depends(get_session),
    user: User = Depends(current_user_dependency),
):
    user = await require_authenticated_user(user)
    note = await get_user_note(note_id, user, session)

    redirect = require_note_access(note)
    if redirect:
        return redirect

    note.title = title
    note.content = content
    note.category_id = category_id

    await session.commit()
    await session.refresh(note)

    logger.info(f"Note updated: {note.id} by user: {user.id}")

    return RedirectResponse(f"/ui/notes/{note.id}", status_code=status.HTTP_302_FOUND)


@router.post("/notes/{note_id}/delete")
async def notes_delete(
    note_id: int,
    request: Request,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(current_user_dependency),
):
    user = await require_authenticated_user(user)
    note = await get_user_note(note_id, user, session)

    redirect = require_note_access(note)
    if redirect:
        return redirect

    await session.delete(note)
    await session.commit()

    logger.info(f"Note deleted: {note_id} by user: {user.id}")

    return RedirectResponse("/ui/notes", status_code=status.HTTP_302_FOUND)

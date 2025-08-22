from fastapi import APIRouter, Request, Depends, Form, status
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import get_session
from app.db.models import User, Note, Category
from app.core.templates import templates
from fastapi import Form

router = APIRouter(prefix="/ui")

async def current_user(request: Request, session: AsyncSession = Depends(get_session)) -> User | None:
    uid = request.session.get("user_id")
    if uid:
        user = await session.get(User, uid)
        return user
    return None

@router.get("/notes", response_class=HTMLResponse)
async def notes_list(request: Request, user: User | None = Depends(current_user),
                     session: AsyncSession = Depends(get_session)):
    if not user:
        return RedirectResponse("/login-html", status_code=status.HTTP_302_FOUND)
    notes_stmt = select(Note).where(Note.owner_id == user.id)
    result = await session.execute(notes_stmt)
    notes = result.scalars().all()

    return templates.TemplateResponse("notes_list.html", {"request": request, "user": user, "notes": notes})

@router.get("/notes/new", response_class=HTMLResponse)
async def notes_new_page(request: Request, user: User | None = Depends(current_user),
                         session: AsyncSession = Depends(get_session)):
    print(f"user: {user}, type: {type(user)}")
    if not user:
        return RedirectResponse("/login-html", status_code=status.HTTP_302_FOUND)
    print("Rendering notes_new.html")
    cats = (await session.execute(select(Category))).scalars().all()
    return templates.TemplateResponse("notes_new.html", {"request": request, "user": user, "categories": cats})


@router.post("/notes/new")
async def notes_new_submit(
    request: Request,
    title: str = Form(...),
    content: str = Form(...),
    category_id: int = Form(...),
    session: AsyncSession = Depends(get_session),
    user: User = Depends(current_user),
):
    if not user:
        return RedirectResponse("/login-html", status_code=status.HTTP_302_FOUND)

    note = Note(
        title=title,
        content=content,
        category_id=category_id,
        owner_id=user.id
    )
    session.add(note)
    await session.commit()
    await session.refresh(note)

    return RedirectResponse(f"/ui/notes/{note.id}", status_code=status.HTTP_302_FOUND)


@router.get("/notes/{note_id}", response_class=HTMLResponse)
async def notes_detail(note_id: int, request: Request, user: User | None = Depends(current_user),
                       session: AsyncSession = Depends(get_session)):
    if not user:
        return RedirectResponse("/login-html", status_code=status.HTTP_302_FOUND)
    print("Rendering notes_new.html")
    note = await session.get(Note, note_id)
    if not note or note.owner_id != user.id:
        return RedirectResponse("/ui/notes", status_code=status.HTTP_302_FOUND)

    return templates.TemplateResponse("note_detail.html", {"request": request, "user": user, "note": note})



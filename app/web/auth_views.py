import logging

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from app.api.auth import get_user_by_email
from app.api.utils.user_utils import normalize_email
from app.core.limiting import limiter
from app.core.security import hash_password, verify_password
from app.db.models import User
from app.db.session import get_session

logger = logging.getLogger(__name__)
router = APIRouter()

templates = Jinja2Templates(directory="templates")


async def current_user(
    request: Request, session: AsyncSession = Depends(get_session)
) -> User | None:
    uid = request.session.get("user_id")
    return await session.get(User, uid) if uid else None


@router.get("/login-html", response_class=HTMLResponse)
async def login_page(request: Request, user: User | None = Depends(current_user)):
    logger.info("Login page accessed")
    return templates.TemplateResponse("login.html", {"request": request, "user": user})


@router.post("/login-html")
async def login_submit(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    session: AsyncSession = Depends(get_session),
):
    user = await get_user_by_email(session, normalize_email(email))
    if not user or not verify_password(password, user.hashed_password):
        logger.warning("Login failed for email: %s", email)
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "user": None, "error": "Неверный email или пароль"},
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    request.session["user_id"] = user.id
    logger.info("Login successful for user: %s", user.id)
    return RedirectResponse("/", status_code=status.HTTP_302_FOUND)


@router.get("/register-html", response_class=HTMLResponse)
async def register_page(request: Request, user: User | None = Depends(current_user)):
    logger.info("Register page accessed")
    return templates.TemplateResponse(
        "register.html", {"request": request, "user": user}
    )


@router.post("/register-html")
async def register_submit(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    session: AsyncSession = Depends(get_session),
):
    email = normalize_email(email)
    if await get_user_by_email(session, email):
        logger.warning("Registration failed - email already exists: %s", email)
        return templates.TemplateResponse(
            "register.html",
            {"request": request, "user": None, "error": "Email уже зарегистрирован"},
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    user = User(email=email, hashed_password=hash_password(password), is_admin=False)
    session.add(user)
    await session.commit()
    await session.refresh(user)

    request.session["user_id"] = user.id
    logger.info("Registration successful for user: %s", user.id)
    return RedirectResponse("/", status_code=status.HTTP_302_FOUND)


@router.get("/logout")
async def logout(request: Request):
    request.session.pop("user_id", None)
    logger.info("User logged out")
    return RedirectResponse("/login-html", status_code=status.HTTP_302_FOUND)

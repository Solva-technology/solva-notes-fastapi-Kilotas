from sqlite3 import IntegrityError
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from sqladmin.authentication import AuthenticationBackend
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.api.utils.user_utils import get_user_by_email, normalize_email
from app.core.antibrute import log
from app.core.config import settings
from app.core.limiting import limiter
from app.core.security import (create_access_token, hash_password,
                               verify_password)
from app.db.models import User
from app.db.session import AsyncSessionLocal, get_session, logger
from app.schemas.auth import RegisterIn, TokenOut
from app.schemas.user import UserOut

router = APIRouter()


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
@limiter.limit("5/minute")
async def register(
    request: Request, data: RegisterIn, session: AsyncSession = Depends(get_session)
):
    email = normalize_email(data.email)
    logger.info("register attempt email=%s", email)

    if await get_user_by_email(session, email):
        logger.warning("register failed: email already registered email=%s", email)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered"
        )

    user = User(
        email=email, hashed_password=hash_password(data.password), is_admin=False
    )

    try:
        session.add(user)
        await session.commit()
        await session.refresh(user)
        logger.info("register success user_id=%s email=%s", user.id, user.email)
        return user
    except IntegrityError:
        await session.rollback()
        logger.warning("register conflict (db unique) email=%s", email)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered"
        )
    except Exception:
        await session.rollback()
        logger.exception("register error email=%s", email)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed",
        )


@router.post("/login", response_model=TokenOut)
@limiter.limit("5/minute")
async def login(
    request: Request,
    form: OAuth2PasswordRequestForm = Depends(),
    session: AsyncSession = Depends(get_session),
):
    email = normalize_email(form.username)
    logger.info("login attempt email=%s", email)

    user = await get_user_by_email(session, email)
    if not user:
        logger.warning("login failed: user not found email=%s", email)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials"
        )

    if not verify_password(form.password, user.hashed_password):
        logger.warning("login failed: bad password user_id=%s", user.id)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials"
        )

    token = create_access_token(sub=user.id)
    logger.info("login success user_id=%s", user.id)

    return {"access_token": token, "token_type": "bearer"}


class AdminAuth(AuthenticationBackend):
    def __init__(self, secret_key: str):
        super().__init__(secret_key=secret_key)

    @limiter.limit("5/minute")
    async def login(self, request: Request) -> bool:
        form = await request.form()
        email = (form.get("username") or "").strip()
        password = (form.get("password") or "").strip()

        logger.info(f"Попытка входа: email={email}")

        try:
            async with AsyncSessionLocal() as session:
                user = (
                    await session.execute(select(User).where(User.email == email))
                ).scalar_one_or_none()

            if not user:
                logger.warning(f"Вход отклонён: пользователь {email} не найден")
                return False

            if not user.is_admin:
                logger.warning(f"Вход отклонён: {email} не админ")
                return False

            if not verify_password(password, user.hashed_password):
                logger.warning(f"Вход отклонён: неверный пароль для {email}")
                return False

            request.session[settings.ADMIN_SESSION_KEY] = user.id
            logger.info(f"Успешный вход: {email}")
            return True

        except Exception as e:
            logger.error(f"Ошибка при входе {email}: {e}", exc_info=True)
            return False

    async def logout(self, request: Request) -> bool:
        user_id = request.session.pop(settings.ADMIN_SESSION_KEY, None)
        logger.info(f"Админ {user_id} вышел из системы")
        return True

    @limiter.limit("5/minute")
    async def authenticate(self, request: Request) -> bool:
        uid: Optional[int] = request.session.get(settings.ADMIN_SESSION_KEY)
        if not uid:
            return False
        async with AsyncSessionLocal() as session:
            user = await session.get(User, uid)
        ok = bool(user and user.is_admin)
        log.debug("admin_auth: authenticate user_id=%s ok=%s", uid, ok)
        return ok


@router.get("/me", response_model=UserOut)
async def me(user: User = Depends(get_current_user)):
    return user

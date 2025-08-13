from typing import Optional
from urllib.request import Request

from sqladmin.authentication import AuthenticationBackend
from sqlalchemy import select
from sqladmin import Admin, ModelView

from app.core.config import settings
from app.core.security import verify_password
from app.db.models import User, Category, Note  # твои модели
from app.db.session import engine, AsyncSessionLocal

SESSION_KEY = "admin_user_id"

class AdminAuth(AuthenticationBackend):
    def __init__(self, secret_key: str):
        super().__init__(secret_key=secret_key)

    async def login(self, request: Request) -> bool:
        form = await request.form()
        email = (form.get("username") or "").strip()
        password = (form.get("password") or "").strip()

        async with AsyncSessionLocal() as session:
            user = (await session.execute(select(User).where(User.email == email))).scalar_one_or_none()

        if not user or not user.is_admin:
            return False
        if not verify_password(password, user.hashed_password):
            return False

        request.session[SESSION_KEY] = user.id
        return True

    async def logout(self, request: Request) -> bool:
        request.session.pop(SESSION_KEY, None)
        return True

    async def authenticate(self, request: Request) -> bool:
        uid: Optional[int] = request.session.get(SESSION_KEY)
        if not uid:
            return False
        async with AsyncSessionLocal() as session:
            user = await session.get(User, uid)
        return bool(user and user.is_admin)

class UserAdmin(ModelView, model=User):
    column_list = [User.id, User.email, User.is_admin]

class CategoryAdmin(ModelView, model=Category):
    column_list = [Category.id, Category.name]

class NoteAdmin(ModelView, model=Note):
    column_list = [Note.id, Note.title, Note.owner_id, Note.category_id]

def setup_admin(app):
    admin = Admin(app, engine, authentication_backend=AdminAuth(secret_key=settings.SECRET_KEY))
    admin.add_view(UserAdmin)
    admin.add_view(CategoryAdmin)
    admin.add_view(NoteAdmin)
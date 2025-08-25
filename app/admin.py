from sqladmin import Admin, ModelView

from app.api.auth import AdminAuth
from app.core.config import settings
from app.db.models import Category, Note, User
from app.db.session import AsyncSessionLocal, engine


class UserAdmin(ModelView, model=User):
    column_list = [User.id, User.email, User.is_admin]


class CategoryAdmin(ModelView, model=Category):
    column_list = [Category.id, Category.name]


class NoteAdmin(ModelView, model=Note):
    column_list = [Note.id, Note.owner_id, Note.category_id]


def setup_admin(app):
    admin = Admin(
        app, engine, authentication_backend=AdminAuth(secret_key=settings.SECRET_KEY)
    )
    admin.add_view(UserAdmin)
    admin.add_view(CategoryAdmin)
    admin.add_view(NoteAdmin)

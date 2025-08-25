from sqlite3 import IntegrityError

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from app.api.deps import require_admin
from app.api.utils.category_utils import get_category_or_404
from app.db.models import Category
from app.db.session import get_session, logger
from app.schemas.category import CategoryCreate, CategoryOut, CategoryUpdate

router = APIRouter(prefix="/categories", tags=["categories"])


@router.get("/", response_model=list[CategoryOut])
async def list_categories(session: AsyncSession = Depends(get_session)):
    res = await session.execute(select(Category).order_by(Category.name))
    return res.scalars().all()


@router.post("/", response_model=CategoryOut, status_code=status.HTTP_201_CREATED)
async def create_category(
    data: CategoryCreate,
    admin=Depends(require_admin),
    session: AsyncSession = Depends(get_session),
):
    name = (data.name or "").strip()

    exists = await session.execute(select(Category.id).where(Category.name == name))
    if exists.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Category with this name already exists",
        )

    category = Category(name=name)
    session.add(category)
    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Category with this name already exists",
        )

    await session.refresh(category)
    logger.info(
        "admin_created_category",
        extra={"admin_id": admin.id, "category_id": category.id, "name": category.name},
    )

    return category


router.put("/{category_id}", response_model=CategoryOut)


async def update_category(
    data: CategoryUpdate,
    admin=Depends(require_admin),
    session: AsyncSession = Depends(get_session),
    category: Category = Depends(get_category_or_404),
):
    old_name = category.name

    if data.name is not None:
        category.name = data.name

    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Category name already exists",
        )

    await session.refresh(category)

    logger.info(
        "admin_updated_category",
        extra={
            "admin_id": admin.id,
            "category_id": category.id,
            "old_name": old_name,
            "new_name": category.name,
        },
    )

    return category


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_category(
    admin=Depends(require_admin),
    session: AsyncSession = Depends(get_session),
    category: Category = Depends(get_category_or_404),
):

    category_id = category.id
    category_name = category.name

    try:
        await session.delete(category)
        await session.commit()
    except IntegrityError:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Category is in use"
        )
    except SQLAlchemyError:
        await session.rollback()
        logger.exception(
            "DB error while deleting category",
            extra={"admin_id": admin.id, "category_id": category_id},
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete category",
        )

    logger.info(
        "admin_deleted_category",
        extra={"admin_id": admin.id, "category_id": category_id, "name": category_name},
    )
    return None

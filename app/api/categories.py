from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import get_session
from app.db.models import Category
from app.schemas.category import CategoryCreate, CategoryUpdate, CategoryOut
from app.api.deps import require_admin

router = APIRouter(prefix="/categories", tags=["categories"])


@router.get("/", response_model=list[CategoryOut])
async def list_categories(session: AsyncSession = Depends(get_session)):
    res = await session.execute(select(Category).order_by(Category.name))
    return res.scalars().all()


@router.post("/", response_model=CategoryOut, status_code=201)
async def create_category(
    data: CategoryCreate,
    admin=Depends(require_admin),
    session: AsyncSession = Depends(get_session),
):
    c = Category(name=data.name)
    session.add(c)
    await session.commit()
    await session.refresh(c)
    return c


@router.put("/{category_id}", response_model=CategoryOut)
async def update_category(
    category_id: int,
    data: CategoryUpdate,
    admin=Depends(require_admin),
    session: AsyncSession = Depends(get_session),
):
    res = await session.execute(select(Category).where(Category.id == category_id))
    c = res.scalar_one_or_none()
    if not c:
        raise HTTPException(status_code=404, detail="Category not found")
    c.name = data.name
    await session.commit()
    await session.refresh(c)
    return c


@router.delete("/{category_id}", status_code=204)
async def delete_category(
    category_id: int,
    admin=Depends(require_admin),
    session: AsyncSession = Depends(get_session),
):
    res = await session.execute(select(Category).where(Category.id == category_id))
    c = res.scalar_one_or_none()
    if not c:
        raise HTTPException(status_code=404, detail="Category not found")
    await session.delete(c)
    try:
        await session.commit()
    except Exception:
        await session.rollback()
        raise HTTPException(status_code=409, detail="Category is in use")
    return None

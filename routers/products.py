from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models import Product
from schemas import ProductCreateIn, ProductOut, ProductUpdateIn
from security import verify_admin_access

router = APIRouter(prefix="/api/products", tags=["products"], dependencies=[Depends(verify_admin_access)])


@router.get("", response_model=list[ProductOut])
async def list_products(active: bool | None = None, db: AsyncSession = Depends(get_db)) -> list[ProductOut]:
    query = select(Product).order_by(Product.sort_order, Product.stars_amount)
    if active is not None:
        query = query.where(Product.is_active == active)
    result = await db.execute(query)
    return list(result.scalars().all())


@router.post("", response_model=ProductOut)
async def create_product(payload: ProductCreateIn, db: AsyncSession = Depends(get_db)) -> ProductOut:
    product = Product(**payload.model_dump())
    db.add(product)
    await db.commit()
    await db.refresh(product)
    return product


@router.patch("/{product_id}", response_model=ProductOut)
async def update_product(product_id: int, payload: ProductUpdateIn, db: AsyncSession = Depends(get_db)) -> ProductOut:
    product = await db.get(Product, product_id)
    if product is None:
        raise HTTPException(status_code=404, detail="Mahsulot topilmadi")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(product, field, value)

    await db.commit()
    await db.refresh(product)
    return product


@router.delete("/{product_id}")
async def delete_product(product_id: int, db: AsyncSession = Depends(get_db)) -> dict:
    product = await db.get(Product, product_id)
    if product is None:
        raise HTTPException(status_code=404, detail="Mahsulot topilmadi")
    product.is_active = False  # Hard delete o'rniga faollikni o'chirish — buyurtma tarixi buzilmasligi uchun
    await db.commit()
    return {"ok": True}

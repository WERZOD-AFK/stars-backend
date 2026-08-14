from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models import Order, OrderStatus, User
from schemas import OrderCreateIn, OrderMarkPaidIn, OrderOut
from security import verify_internal_secret
from services import create_order_for_user

router = APIRouter(prefix="/api/orders", tags=["orders"], dependencies=[Depends(verify_internal_secret)])


@router.post("", response_model=OrderOut)
async def create_order(payload: OrderCreateIn, db: AsyncSession = Depends(get_db)) -> OrderOut:
    user_result = await db.execute(select(User).where(User.tg_user_id == payload.tg_user_id))
    user = user_result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=404, detail="Foydalanuvchi topilmadi")

    return await create_order_for_user(db, user, payload.product_id, payload.promo_code)


@router.get("", response_model=list[OrderOut])
async def list_orders(tg_user_id: int, limit: int = 20, db: AsyncSession = Depends(get_db)) -> list[OrderOut]:
    user_result = await db.execute(select(User).where(User.tg_user_id == tg_user_id))
    user = user_result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=404, detail="Foydalanuvchi topilmadi")

    result = await db.execute(
        select(Order).where(Order.user_id == user.id).order_by(Order.created_at.desc()).limit(limit)
    )
    return list(result.scalars().all())


@router.get("/{order_id}", response_model=OrderOut)
async def get_order(order_id: int, db: AsyncSession = Depends(get_db)) -> OrderOut:
    order = await db.get(Order, order_id)
    if order is None:
        raise HTTPException(status_code=404, detail="Buyurtma topilmadi")
    return order


@router.post("/{order_id}/mark-paid", response_model=OrderOut)
async def mark_order_paid(order_id: int, payload: OrderMarkPaidIn, db: AsyncSession = Depends(get_db)) -> OrderOut:
    """
    Faqat Telegram'dan kelgan haqiqiy successful_payment eventidan keyin bot
    tomonidan chaqiriladi. Bu yerda ikkilamchi himoya sifatida buyurtma allaqachon
    to'langan bo'lsa, xatolik qaytariladi (duplicate payment himoyasi).
    """
    order = await db.get(Order, order_id)
    if order is None:
        raise HTTPException(status_code=404, detail="Buyurtma topilmadi")
    if order.status != OrderStatus.pending:
        raise HTTPException(status_code=409, detail=f"Buyurtma allaqachon '{order.status.value}' holatida")

    order.status = OrderStatus.paid
    order.telegram_payment_charge_id = payload.telegram_payment_charge_id
    order.paid_at = datetime.now(timezone.utc)

    # NOTE: Stars'ni haqiqatda yetkazib berish (masalan Fragment API orqali)
    # shu yerda yoki alohida background worker'da amalga oshiriladi. Hozircha
    # buyurtma "paid" holatiga o'tadi, admin panel orqali "completed"ga o'tkaziladi.

    await db.commit()
    await db.refresh(order)
    return order

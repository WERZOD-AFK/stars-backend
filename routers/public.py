"""
Bu router internal secret o'rniga Telegram WebApp initData bilan himoyalangan —
faqat Telegram ichida ochilgan Mini App'dan kelgan so'rovlar qabul qilinadi.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models import Order, Product, SupportTicket
from schemas import (
    OrderOut,
    ProductOut,
    PublicSupportTicketIn,
    SupportTicketOut,
    UserOut,
)
from security import verify_webapp_user
from services import create_order_for_user, get_or_create_user, to_user_out
from telegram_api import TelegramApiError, create_invoice_link

router = APIRouter(prefix="/api/public", tags=["public"])


async def _current_user(
    webapp_user: dict = Depends(verify_webapp_user), db: AsyncSession = Depends(get_db)
):
    return await get_or_create_user(
        db,
        tg_user_id=webapp_user["id"],
        username=webapp_user.get("username"),
        full_name=f"{webapp_user.get('first_name', '')} {webapp_user.get('last_name', '')}".strip(),
    )


@router.get("/products", response_model=list[ProductOut])
async def list_products(db: AsyncSession = Depends(get_db)) -> list[ProductOut]:
    result = await db.execute(
        select(Product).where(Product.is_active == True).order_by(Product.sort_order, Product.stars_amount)  # noqa: E712
    )
    return list(result.scalars().all())


@router.get("/me", response_model=UserOut)
async def me(user=Depends(_current_user), db: AsyncSession = Depends(get_db)) -> UserOut:
    return await to_user_out(db, user)


@router.get("/orders", response_model=list[OrderOut])
async def my_orders(user=Depends(_current_user), db: AsyncSession = Depends(get_db)) -> list[OrderOut]:
    result = await db.execute(
        select(Order).where(Order.user_id == user.id).order_by(Order.created_at.desc()).limit(20)
    )
    return list(result.scalars().all())


@router.get("/orders/{order_id}", response_model=OrderOut)
async def order_status(order_id: int, user=Depends(_current_user), db: AsyncSession = Depends(get_db)) -> OrderOut:
    order = await db.get(Order, order_id)
    if order is None or order.user_id != user.id:
        raise HTTPException(status_code=404, detail="Buyurtma topilmadi")
    return order


@router.post("/orders")
async def create_order_with_invoice(
    product_id: int, promo_code: str | None = None, user=Depends(_current_user), db: AsyncSession = Depends(get_db)
) -> dict:
    order = await create_order_for_user(db, user, product_id, promo_code)

    try:
        invoice_link = await create_invoice_link(
            title=f"{order.stars_amount} ⭐ Stars",
            description=f"Stars Shop — buyurtma #{order.id}",
            payload=f"order:{order.id}",
            stars_amount=order.price_stars,
        )
    except TelegramApiError as exc:
        raise HTTPException(status_code=502, detail=f"To'lov havolasini yaratib bo'lmadi: {exc}") from exc

    return {"order": OrderOut.model_validate(order), "invoice_link": invoice_link}


@router.post("/support/tickets", response_model=SupportTicketOut)
async def create_ticket(
    payload: PublicSupportTicketIn, user=Depends(_current_user), db: AsyncSession = Depends(get_db)
) -> SupportTicketOut:
    ticket = SupportTicket(user_id=user.id, message=payload.message)
    db.add(ticket)
    await db.commit()
    await db.refresh(ticket)
    return ticket

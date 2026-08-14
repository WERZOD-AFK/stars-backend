from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from database import get_db
from models import AdminLog, Order, OrderStatus, PromoCode, Product, SupportTicket, User
from schemas import AdminStatsOut
from security import verify_admin_access

router = APIRouter(prefix="/api/admin", tags=["admin"], dependencies=[Depends(verify_admin_access)])


async def _log(db: AsyncSession, action: str, details: str | None = None) -> None:
    db.add(AdminLog(action=action, details=details))


@router.get("/stats", response_model=AdminStatsOut)
async def stats(db: AsyncSession = Depends(get_db)) -> AdminStatsOut:
    users_count = (await db.execute(select(func.count(User.id)))).scalar_one()
    orders_count = (await db.execute(select(func.count(Order.id)))).scalar_one()
    paid_statuses = [OrderStatus.paid, OrderStatus.completed]
    stars_sold = (
        await db.execute(select(func.coalesce(func.sum(Order.stars_amount), 0)).where(Order.status.in_(paid_statuses)))
    ).scalar_one()
    revenue = (
        await db.execute(select(func.coalesce(func.sum(Order.price_stars), 0)).where(Order.status.in_(paid_statuses)))
    ).scalar_one()

    return AdminStatsOut(users_count=users_count, orders_count=orders_count, stars_sold=stars_sold, revenue=revenue)


@router.get("/user-ids", response_model=list[int])
async def user_ids(only_active: bool = True, db: AsyncSession = Depends(get_db)) -> list[int]:
    query = select(User.tg_user_id)
    if only_active:
        query = query.where(User.is_blocked == False)  # noqa: E712
    result = await db.execute(query)
    return list(result.scalars().all())


@router.get("/users")
async def list_users(search: str | None = None, limit: int = 50, db: AsyncSession = Depends(get_db)) -> list[dict]:
    query = select(User).order_by(User.created_at.desc()).limit(limit)
    if search:
        like = f"%{search}%"
        query = select(User).where(
            (User.username.ilike(like)) | (User.full_name.ilike(like))
        ).order_by(User.created_at.desc()).limit(limit)
    result = await db.execute(query)
    users = result.scalars().all()
    return [
        {
            "tg_user_id": u.tg_user_id,
            "username": u.username,
            "full_name": u.full_name,
            "bonus_balance": u.bonus_balance,
            "is_blocked": u.is_blocked,
            "created_at": u.created_at,
        }
        for u in users
    ]


@router.post("/users/{tg_user_id}/block")
async def block_user(tg_user_id: int, db: AsyncSession = Depends(get_db)) -> dict:
    result = await db.execute(select(User).where(User.tg_user_id == tg_user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=404, detail="Foydalanuvchi topilmadi")
    user.is_blocked = True
    await _log(db, "block_user", details=f"tg_user_id={tg_user_id}")
    await db.commit()
    return {"ok": True}


@router.post("/users/{tg_user_id}/unblock")
async def unblock_user(tg_user_id: int, db: AsyncSession = Depends(get_db)) -> dict:
    result = await db.execute(select(User).where(User.tg_user_id == tg_user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=404, detail="Foydalanuvchi topilmadi")
    user.is_blocked = False
    await _log(db, "unblock_user", details=f"tg_user_id={tg_user_id}")
    await db.commit()
    return {"ok": True}


@router.get("/orders")
async def list_orders(status_filter: str | None = None, limit: int = 50, db: AsyncSession = Depends(get_db)) -> list[dict]:
    query = select(Order).order_by(Order.created_at.desc()).limit(limit)
    if status_filter:
        query = query.where(Order.status == OrderStatus(status_filter))
    result = await db.execute(query)
    orders = result.scalars().all()
    return [
        {
            "id": o.id,
            "user_id": o.user_id,
            "stars_amount": o.stars_amount,
            "price_stars": o.price_stars,
            "status": o.status.value,
            "promo_code": o.promo_code,
            "created_at": o.created_at,
            "paid_at": o.paid_at,
        }
        for o in orders
    ]


@router.post("/orders/{order_id}/complete")
async def complete_order(order_id: int, db: AsyncSession = Depends(get_db)) -> dict:
    """
    Stars real yetkazilgach, admin buyurtmani yopadi. Agar bu foydalanuvchining
    birinchi yakunlangan buyurtmasi bo'lsa va u referal orqali kelgan bo'lsa,
    referrerga bonus yoziladi.
    """
    order = await db.get(Order, order_id)
    if order is None:
        raise HTTPException(status_code=404, detail="Buyurtma topilmadi")
    if order.status != OrderStatus.paid:
        raise HTTPException(status_code=409, detail="Faqat 'paid' holatidagi buyurtmalarni yopish mumkin")

    order.status = OrderStatus.completed

    if settings.referral_bonus_stars > 0:
        buyer = await db.get(User, order.user_id)
        if buyer and buyer.referred_by_id:
            prior_completed = await db.execute(
                select(func.count(Order.id)).where(
                    Order.user_id == buyer.id, Order.status == OrderStatus.completed, Order.id != order.id
                )
            )
            is_first_completed = prior_completed.scalar_one() == 0
            if is_first_completed:
                referrer = await db.get(User, buyer.referred_by_id)
                if referrer:
                    referrer.bonus_balance += settings.referral_bonus_stars
                    await _log(
                        db, "referral_bonus",
                        details=f"referrer={referrer.tg_user_id} +{settings.referral_bonus_stars} (order #{order.id})",
                    )

    await _log(db, "complete_order", details=f"order_id={order_id}")
    await db.commit()
    return {"ok": True}


@router.get("/promo-codes")
async def list_promo_codes(db: AsyncSession = Depends(get_db)) -> list[dict]:
    result = await db.execute(select(PromoCode).order_by(PromoCode.created_at.desc()))
    codes = result.scalars().all()
    return [
        {
            "id": p.id,
            "code": p.code,
            "discount_percent": p.discount_percent,
            "max_uses": p.max_uses,
            "used_count": p.used_count,
            "is_active": p.is_active,
        }
        for p in codes
    ]


@router.post("/promo-codes")
async def create_promo_code(
    code: str, discount_percent: int, max_uses: int, db: AsyncSession = Depends(get_db)
) -> dict:
    promo = PromoCode(code=code, discount_percent=discount_percent, max_uses=max_uses)
    db.add(promo)
    await _log(db, "create_promo_code", details=code)
    await db.commit()
    return {"ok": True, "code": code}


@router.post("/promo-codes/{promo_id}/deactivate")
async def deactivate_promo_code(promo_id: int, db: AsyncSession = Depends(get_db)) -> dict:
    promo = await db.get(PromoCode, promo_id)
    if promo is None:
        raise HTTPException(status_code=404, detail="Promo kod topilmadi")
    promo.is_active = False
    await db.commit()
    return {"ok": True}


@router.get("/support/tickets")
async def list_support_tickets(answered: bool | None = None, db: AsyncSession = Depends(get_db)) -> list[dict]:
    query = select(SupportTicket).order_by(SupportTicket.created_at.desc())
    if answered is not None:
        query = query.where(SupportTicket.is_answered == answered)
    result = await db.execute(query)
    tickets = result.scalars().all()
    return [
        {"id": t.id, "user_id": t.user_id, "message": t.message, "answer": t.answer,
         "is_answered": t.is_answered, "created_at": t.created_at}
        for t in tickets
    ]

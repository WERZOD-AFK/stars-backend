from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from models import Order, OrderStatus, PromoCode, Product, User
from schemas import UserOut


async def get_or_create_user(
    db: AsyncSession, tg_user_id: int, username: str | None, full_name: str, ref_code: str | None = None
) -> User:
    result = await db.execute(select(User).where(User.tg_user_id == tg_user_id))
    user = result.scalar_one_or_none()

    if user is None:
        referred_by_id = None
        if ref_code and ref_code.isdigit():
            ref_result = await db.execute(select(User).where(User.tg_user_id == int(ref_code)))
            referrer = ref_result.scalar_one_or_none()
            if referrer and referrer.tg_user_id != tg_user_id:
                referred_by_id = referrer.id

        user = User(
            tg_user_id=tg_user_id,
            username=username,
            full_name=full_name,
            referred_by_id=referred_by_id,
        )
        db.add(user)
    else:
        user.username = username
        user.full_name = full_name

    await db.commit()
    await db.refresh(user)
    return user


async def to_user_out(db: AsyncSession, user: User) -> UserOut:
    stats = await db.execute(
        select(
            func.coalesce(func.sum(Order.stars_amount), 0),
            func.count(Order.id),
        ).where(Order.user_id == user.id, Order.status == OrderStatus.completed)
    )
    total_stars, orders_count = stats.one()

    return UserOut(
        tg_user_id=user.tg_user_id,
        username=user.username,
        full_name=user.full_name,
        bonus_balance=user.bonus_balance,
        is_blocked=user.is_blocked,
        total_stars_purchased=total_stars,
        orders_count=orders_count,
    )


async def create_order_for_user(
    db: AsyncSession, user: User, product_id: int, promo_code: str | None
) -> Order:
    if user.is_blocked:
        raise HTTPException(status_code=403, detail="Foydalanuvchi bloklangan")

    product = await db.get(Product, product_id)
    if product is None or not product.is_active:
        raise HTTPException(status_code=404, detail="Mahsulot topilmadi yoki faol emas")

    price_stars = product.price_stars
    applied_promo = None
    if promo_code:
        promo_result = await db.execute(
            select(PromoCode).where(PromoCode.code == promo_code, PromoCode.is_active == True)  # noqa: E712
        )
        promo = promo_result.scalar_one_or_none()
        if promo is None:
            raise HTTPException(status_code=400, detail="Promo kod topilmadi yoki faol emas")
        if promo.used_count >= promo.max_uses:
            raise HTTPException(status_code=400, detail="Promo kod limiti tugagan")

        price_stars = max(1, round(price_stars * (100 - promo.discount_percent) / 100))
        applied_promo = promo

    order = Order(
        user_id=user.id,
        product_id=product.id,
        stars_amount=product.stars_amount,
        price_stars=price_stars,
        promo_code=promo_code if applied_promo else None,
    )
    db.add(order)

    if applied_promo:
        applied_promo.used_count += 1

    await db.commit()
    await db.refresh(order)
    return order

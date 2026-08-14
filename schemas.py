from datetime import datetime

from pydantic import BaseModel, ConfigDict

from models import OrderStatus


# ---- Users ---------------------------------------------------------------

class UserUpsertIn(BaseModel):
    tg_user_id: int
    username: str | None = None
    full_name: str
    ref_code: str | None = None


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    tg_user_id: int
    username: str | None
    full_name: str
    bonus_balance: int
    is_blocked: bool
    total_stars_purchased: int = 0
    orders_count: int = 0


# ---- Products --------------------------------------------------------------

class ProductOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    stars_amount: int
    price_stars: int
    is_active: bool
    is_popular: bool


class ProductCreateIn(BaseModel):
    name: str
    stars_amount: int
    price_stars: int
    is_popular: bool = False
    sort_order: int = 0


class ProductUpdateIn(BaseModel):
    name: str | None = None
    stars_amount: int | None = None
    price_stars: int | None = None
    is_active: bool | None = None
    is_popular: bool | None = None
    sort_order: int | None = None


# ---- Orders --------------------------------------------------------------

class OrderCreateIn(BaseModel):
    tg_user_id: int
    product_id: int
    promo_code: str | None = None


class OrderOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    stars_amount: int
    price_stars: int
    status: OrderStatus
    promo_code: str | None
    created_at: datetime
    paid_at: datetime | None


class OrderMarkPaidIn(BaseModel):
    telegram_payment_charge_id: str


# ---- Support ---------------------------------------------------------------

class SupportTicketIn(BaseModel):
    tg_user_id: int
    message: str


class PublicSupportTicketIn(BaseModel):
    """Mini App uchun — foydalanuvchi initData orqali aniqlanadi, alohida tg_user_id kerak emas."""
    message: str


class SupportTicketOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    message: str
    answer: str | None
    is_answered: bool
    created_at: datetime


# ---- Admin ----------------------------------------------------------------

class AdminStatsOut(BaseModel):
    users_count: int
    orders_count: int
    stars_sold: int
    revenue: int


class BroadcastResultOut(BaseModel):
    user_ids: list[int]


class AdminUserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    tg_user_id: int
    username: str | None
    full_name: str
    bonus_balance: int
    is_blocked: bool
    created_at: datetime
    total_stars_purchased: int = 0
    orders_count: int = 0


class AdminOrderOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    stars_amount: int
    price_stars: int
    status: OrderStatus
    promo_code: str | None
    created_at: datetime
    paid_at: datetime | None
    user_tg_id: int
    user_full_name: str


class PromoCodeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    discount_percent: int
    max_uses: int
    used_count: int
    is_active: bool
    created_at: datetime


class PromoCodeCreateIn(BaseModel):
    code: str
    discount_percent: int
    max_uses: int


class SupportTicketAnswerIn(BaseModel):
    answer: str


class AdminSupportTicketOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    message: str
    answer: str | None
    is_answered: bool
    created_at: datetime
    user_tg_id: int
    user_full_name: str


class BroadcastIn(BaseModel):
    message: str
    only_active: bool = True


class BroadcastResultCountOut(BaseModel):
    sent: int
    failed: int
    total: int


class AdminUsersPage(BaseModel):
    items: list[AdminUserOut]
    total: int
    page: int
    page_size: int


class AdminOrdersPage(BaseModel):
    items: list[AdminOrderOut]
    total: int
    page: int
    page_size: int

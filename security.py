import json

from fastapi import Header, HTTPException, status

from config import settings
from telegram_auth import verify_telegram_init_data


async def verify_internal_secret(x_internal_secret: str = Header(default="")) -> None:
    """
    Faqat bot (yoki admin panel) shu maxfiy kalit bilan so'rov yuborsa,
    API'ga kirishga ruxsat beriladi. Bu kalit hech qachon frontendga
    (Mini App'ga) chiqarilmasligi kerak — u faqat server-server muloqoti uchun.
    """
    if not x_internal_secret or x_internal_secret != settings.internal_secret:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Ruxsat yo'q")


async def verify_admin_access(
    x_internal_secret: str = Header(default=""), x_admin_password: str = Header(default="")
) -> None:
    """
    /api/admin/* endpointlariga ikkita yo'l bilan kirish mumkin:
    1) Bot — X-Internal-Secret orqali (masalan /stats, /broadcast komandalar)
    2) Veb Admin Panel — X-Admin-Password orqali (brauzerda ishlatiladi,
       shuning uchun bot kalitidan alohida, o'zgartirish/almashtirish osonroq)
    """
    if x_internal_secret and x_internal_secret == settings.internal_secret:
        return
    if x_admin_password and x_admin_password == settings.admin_panel_password:
        return
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Ruxsat yo'q")


async def verify_webapp_user(x_telegram_init_data: str = Header(default="")) -> dict:
    """
    Mini App har bir so'rovda Telegram.WebApp.initData'ni shu header orqali
    yuboradi. Bu yerda uning haqiqiyligi (Telegram tomonidan imzolanganligi)
    tekshiriladi va ichidagi foydalanuvchi ma'lumotlari qaytariladi.
    """
    if not x_telegram_init_data:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="initData topilmadi")

    try:
        parsed = verify_telegram_init_data(x_telegram_init_data, settings.bot_token)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc

    user_raw = parsed.get("user")
    if not user_raw:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Foydalanuvchi ma'lumoti topilmadi")

    try:
        return json.loads(user_raw)
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Foydalanuvchi ma'lumoti noto'g'ri") from exc

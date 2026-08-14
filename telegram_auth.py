"""
Mini App to'g'ridan-to'g'ri backendga so'rov yuborganda (masalan mahsulotlar
ro'yxatini olish), uni Telegram yuborganini tasdiqlash kerak. Buning uchun
Telegram WebApp `initData`sini quyidagi algoritm bilan tekshiramiz:
https://core.telegram.org/bots/webapps#validating-data-received-via-the-mini-app

Bu funksiya hozircha frontend bosqichida ishlatiladi (routers/public.py kabi),
lekin tayyor turishi uchun shu yerga qo'yildi.
"""
import hashlib
import hmac
from urllib.parse import parse_qsl


def verify_telegram_init_data(init_data: str, bot_token: str, max_age_seconds: int = 86400) -> dict:
    """
    init_data haqiqiy va eskirmagan bo'lsa, undan olingan parametrlar (dict) qaytariladi.
    Aks holda ValueError ko'tariladi.
    """
    parsed = dict(parse_qsl(init_data, strict_parsing=True))
    received_hash = parsed.pop("hash", None)
    if not received_hash:
        raise ValueError("hash topilmadi")

    data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(parsed.items()))

    secret_key = hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()
    computed_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()

    if not hmac.compare_digest(computed_hash, received_hash):
        raise ValueError("hash mos kelmadi — ma'lumot Telegram'dan kelmagan bo'lishi mumkin")

    auth_date = int(parsed.get("auth_date", "0"))
    import time
    if time.time() - auth_date > max_age_seconds:
        raise ValueError("initData eskirgan")

    return parsed

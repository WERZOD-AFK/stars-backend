import os
from dataclasses import dataclass, field

from dotenv import load_dotenv

load_dotenv()


def _get_env(name: str, required: bool = True, default: str | None = None) -> str:
    value = os.getenv(name, default)
    if required and not value:
        raise RuntimeError(f"Environment variable '{name}' o'rnatilmagan (.env faylini tekshiring)")
    return value


@dataclass(frozen=True)
class Settings:
    # Masalan: postgresql+asyncpg://user:pass@host:5432/dbname
    database_url: str = field(default_factory=lambda: _get_env("DATABASE_URL"))

    # Faqat bot shu kalit bilan so'rov yuborsa ruxsat beriladi
    internal_secret: str = field(default_factory=lambda: _get_env("API_INTERNAL_SECRET"))

    # Veb Admin Panel shu parol bilan kiradi (bot kalitidan alohida — brauzerda ishlatilgani uchun)
    admin_panel_password: str = field(default_factory=lambda: _get_env("ADMIN_PANEL_PASSWORD"))

    # Referal bonusi (Stars birligida) — referal orqali kelgan foydalanuvchi birinchi
    # marta buyurtmasini yakunlaganda referrerga shuncha bonus yoziladi
    referral_bonus_stars: int = field(default_factory=lambda: int(os.getenv("REFERRAL_BONUS_STARS", "0")))

    # Mini App'dan kelgan initData'ni tekshirish va Stars invoice link yaratish uchun
    # (stars-bot loyihasidagi BOT_TOKEN bilan bir xil bo'lishi kerak)
    bot_token: str = field(default_factory=lambda: _get_env("BOT_TOKEN"))

    # CORS — Mini App frontend manzili (masalan https://your-mini-app.example.com)
    frontend_origin: str = field(default_factory=lambda: _get_env("FRONTEND_ORIGIN", required=False, default="*"))
    # CORS — Admin panel manzili
    admin_panel_origin: str = field(default_factory=lambda: _get_env("ADMIN_PANEL_ORIGIN", required=False, default="*"))

    port: int = field(default_factory=lambda: int(os.getenv("PORT", "8000")))

    # Click.uz to'lov integratsiyasi (hozircha bo'sh qoldirilsa ham ilova ishlayveradi,
    # faqat /api/click/* endpointlar Click'dan haqiqiy so'rov kelganda ishlatiladi)
    click_service_id: str = field(default_factory=lambda: _get_env("CLICK_SERVICE_ID", required=False, default=""))
    click_merchant_id: str = field(default_factory=lambda: _get_env("CLICK_MERCHANT_ID", required=False, default=""))
    click_secret_key: str = field(default_factory=lambda: _get_env("CLICK_SECRET_KEY", required=False, default=""))


settings = Settings()

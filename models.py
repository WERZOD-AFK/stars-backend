import os
from dataclasses import dataclass, field

from dotenv import load_dotenv


load_dotenv()


def _get_env(
    name: str,
    required: bool = True,
    default: str | None = None,
) -> str:
    value = os.getenv(name, default)

    if required and not value:
        raise RuntimeError(
            f"Environment variable '{name}' o'rnatilmagan "
            "(.env faylini tekshiring)"
        )

    return value


@dataclass(frozen=True)
class Settings:
    # =========================
    # DATABASE
    # =========================

    database_url: str = field(
        default_factory=lambda: _get_env("DATABASE_URL")
    )

    # =========================
    # INTERNAL API
    # =========================

    internal_secret: str = field(
        default_factory=lambda: _get_env("API_INTERNAL_SECRET")
    )

    # =========================
    # ADMIN PANEL
    # =========================

    admin_panel_password: str = field(
        default_factory=lambda: _get_env("ADMIN_PANEL_PASSWORD")
    )

    # =========================
    # TELEGRAM
    # =========================

    bot_token: str = field(
        default_factory=lambda: _get_env("BOT_TOKEN")
    )

    # =========================
    # REFERRAL
    # =========================

    referral_bonus_stars: int = field(
        default_factory=lambda: int(
            os.getenv("REFERRAL_BONUS_STARS", "0")
        )
    )

    # =========================
    # CORS
    # =========================

    frontend_origin: str = field(
        default_factory=lambda: _get_env(
            "FRONTEND_ORIGIN",
            required=False,
            default="*",
        )
    )

    admin_panel_origin: str = field(
        default_factory=lambda: _get_env(
            "ADMIN_PANEL_ORIGIN",
            required=False,
            default="*",
        )
    )

    # =========================
    # SERVER
    # =========================

    port: int = field(
        default_factory=lambda: int(
            os.getenv("PORT", "8000")
        )
    )

    # =========================
    # CLICK
    # =========================

    # Click Business tomonidan beriladi
    click_service_id: str = field(
        default_factory=lambda: _get_env(
            "CLICK_SERVICE_ID",
            required=False,
            default="",
        )
    )

    # Click Merchant ID
    click_merchant_id: str = field(
        default_factory=lambda: _get_env(
            "CLICK_MERCHANT_ID",
            required=False,
            default="",
        )
    )

    # Click SECRET KEY
    # MUHIM: bu qiymatni frontendga chiqarmang!
    click_secret_key: str = field(
        default_factory=lambda: _get_env(
            "CLICK_SECRET_KEY",
            required=False,
            default="",
        )
    )


settings = Settings()

import httpx

from config import settings


class TelegramApiError(Exception):
    pass


async def create_invoice_link(title: str, description: str, payload: str, stars_amount: int) -> str:
    """
    Stars uchun to'lov havolasi yaratadi. Mini App shu havolani
    Telegram.WebApp.openInvoice() orqali ochadi — foydalanuvchi
    Mini App'dan chiqmasdan to'laydi.
    https://core.telegram.org/bots/api#createinvoicelink
    """
    url = f"https://api.telegram.org/bot{settings.bot_token}/createInvoiceLink"
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.post(
            url,
            json={
                "title": title,
                "description": description,
                "payload": payload,
                "provider_token": "",
                "currency": "XTR",
                "prices": [{"label": title, "amount": stars_amount}],
            },
        )
        data = resp.json()
        if not data.get("ok"):
            raise TelegramApiError(data.get("description", "Noma'lum xatolik"))
        return data["result"]


async def send_message(chat_id: int, text: str) -> bool:
    """Broadcast va support javoblari uchun. Xatolik bo'lsa False qaytaradi (masalan foydalanuvchi botni bloklagan)."""
    url = f"https://api.telegram.org/bot{settings.bot_token}/sendMessage"
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.post(url, json={"chat_id": chat_id, "text": text, "parse_mode": "HTML"})
        data = resp.json()
        return bool(data.get("ok"))

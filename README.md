# Stars Shop — Backend API (FastAPI)

Bu loyihaning **backend** qismi. Bot va (keyinchalik) Mini App shu API orqali
foydalanuvchi, mahsulot, buyurtma va support ma'lumotlari bilan ishlaydi.
Barcha ma'lumotlar PostgreSQL'da saqlanadi.

## Loyiha tuzilishi

```
stars-backend/
├── main.py                # FastAPI ilova, router'larni ulash, jadval yaratish
├── config.py               # .env dan o'qiladigan sozlamalar
├── database.py              # Async SQLAlchemy engine/session
├── models.py                # Jadvallar: User, Product, Order, PromoCode, SupportTicket, AdminLog
├── schemas.py                # Pydantic request/response sxemalari
├── security.py                # Ichki so'rovlarni (bot -> backend) tasdiqlash
├── telegram_auth.py            # Telegram WebApp initData tekshirish (Mini App bosqichi uchun tayyor)
├── routers/
│   ├── users.py               # upsert, profil
│   ├── products.py             # Stars paketlari CRUD
│   ├── orders.py                # Buyurtma yaratish, to'lovni belgilash
│   ├── support.py                # Support ticketlar
│   └── admin.py                   # Statistika, block/unblock, promo kod, order completion
├── requirements.txt
├── .env.example
├── Dockerfile
└── README.md
```

## Autentifikatsiya modeli

Hozircha barcha `/api/*` endpointlar **faqat bot** tomonidan chaqiriladi va
`X-Internal-Secret` header orqali tasdiqlanadi (`security.py`). Bu kalit
`stars-bot`dagi `API_INTERNAL_SECRET` bilan bir xil bo'lishi kerak va u hech
qachon Mini App frontendga chiqarilmaydi.

Mini App esa `routers/public.py`dagi `/api/public/*` endpointlarni chaqiradi —
bular `X-Telegram-Init-Data` header orqali Telegram WebApp `initData`sini
tekshiradi (`telegram_auth.py` + `security.verify_webapp_user`), shu asosda
foydalanuvchini avtomatik topadi/yaratadi. Bu yerda `BOT_TOKEN` kerak bo'ladi
(initData imzosini tekshirish va Stars invoice link yaratish uchun) — u
`stars-bot`dagi token bilan bir xil bo'lishi kerak.

`/api/public/orders` chaqirilganda backend `createInvoiceLink` orqali Telegram'dan
to'lov havolasi oladi va uni frontendga qaytaradi; Mini App shu havolani
`Telegram.WebApp.openInvoice()` bilan ochadi — foydalanuvchi ilovadan chiqmasdan
to'laydi.

## Mahalliy ishga tushirish

1. PostgreSQL o'rnatilgan/ishga tushirilgan bo'lsin (yoki Docker orqali):
   ```bash
   docker run --name stars-db -e POSTGRES_PASSWORD=password -e POSTGRES_DB=stars_shop -p 5432:5432 -d postgres:16
   ```
2. Virtual environment va kutubxonalar:
   ```bash
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```
3. `.env.example`dan nusxa oling:
   ```bash
   cp .env.example .env
   ```
   `DATABASE_URL`ni o'z PostgreSQL ma'lumotlaringizga moslang, `API_INTERNAL_SECRET`ni
   bot loyihasidagi bilan bir xil qiling.
4. Ishga tushiring:
   ```bash
   uvicorn main:app --reload
   ```
   Ishga tushganda jadvallar avtomatik yaratiladi (`create_all`). Swagger UI:
   `http://localhost:8000/docs`.

## Test qilish

Swagger UI orqali (`/docs`) yoki curl bilan:

```bash
# Foydalanuvchi yaratish
curl -X POST http://localhost:8000/api/users/upsert \
  -H "Content-Type: application/json" \
  -H "X-Internal-Secret: your-secret" \
  -d '{"tg_user_id": 111, "username": "test", "full_name": "Test User"}'

# Mahsulot qo'shish
curl -X POST http://localhost:8000/api/products \
  -H "Content-Type: application/json" \
  -H "X-Internal-Secret: your-secret" \
  -d '{"name": "1000 Stars", "stars_amount": 1000, "price_stars": 1000}'
```

## Railway'ga deploy qilish

1. Railway loyihasiga **PostgreSQL** plugin qo'shing — u avtomatik `DATABASE_URL`
   beradi, lekin diqqat: Railway odatda `postgresql://` formatida beradi,
   siz uni `postgresql+asyncpg://` ga o'zgartirishingiz kerak (asyncpg drayveri uchun).
2. Backend uchun alohida service yarating (**Deploy from GitHub repo**), Railway
   `Dockerfile`ni avtomatik topadi.
3. Variables bo'limida `.env.example`dagi barcha o'zgaruvchilarni kiriting.
4. Deploy tugagach, backend manzilini (`https://your-backend.up.railway.app`)
   bot loyihasidagi `API_BASE_URL`ga qo'ying.

## Xavfsizlik eslatmalari

- `API_INTERNAL_SECRET` bot va backendda bir xil, lekin hech qachon Mini App
  frontend kodiga yozilmaydi.
- Har bir yozuv operatsiyasi (order, promo, block) `AdminLog` orqali audit
  qilinadi (hozircha faqat admin harakatlari uchun asosiy holatlar qo'shilgan).
- Duplicate to'lovlarning oldini olish: `mark-paid` faqat `pending` holatidagi
  buyurtmalarga ishlaydi, aks holda 409 xatolik qaytaradi.
- Production'da `create_all()` o'rniga **Alembic** migratsiyalariga o'tish tavsiya
  etiladi — hozirgi holat tezkor boshlash uchun soddalashtirilgan.

## Keyingi qadam

Endi Mini App (React frontend) qurish mumkin — u shu backend'dagi mahsulotlar
ro'yxatini ko'rsatadi va buyurtma yaratish so'rovini yuboradi (yoki to'g'ridan-to'g'ri
botga signal beradi). Davom etishni xohlasangiz, ayting.

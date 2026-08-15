import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import settings
from database import Base, engine
from routers import admin, click, orders, products, public, support, users


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    # Eslatma: production'da jadvallarni Alembic migratsiyalari
    # orqali boshqarish tavsiya etiladi.
    # Hozircha loyiha ishga tushishi uchun create_all ishlatilmoqda.
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    logger.info("Database jadvallari tayyor")

    yield


app = FastAPI(
    title="Stars Shop API",
    lifespan=lifespan,
)


origins = ["*"]

if (
    settings.frontend_origin != "*"
    or settings.admin_panel_origin != "*"
):
    origins = [
        origin
        for origin in [
            settings.frontend_origin,
            settings.admin_panel_origin,
        ]
        if origin != "*"
    ]


app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Routers
app.include_router(users.router)
app.include_router(products.router)
app.include_router(orders.router)
app.include_router(support.router)
app.include_router(admin.router)
app.include_router(public.router)

# Click API
app.include_router(click.router)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}

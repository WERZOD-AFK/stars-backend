from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models import User
from schemas import UserOut, UserUpsertIn
from security import verify_internal_secret
from services import get_or_create_user, to_user_out

router = APIRouter(prefix="/api/users", tags=["users"], dependencies=[Depends(verify_internal_secret)])


@router.post("/upsert", response_model=UserOut)
async def upsert_user(payload: UserUpsertIn, db: AsyncSession = Depends(get_db)) -> UserOut:
    user = await get_or_create_user(db, payload.tg_user_id, payload.username, payload.full_name, payload.ref_code)
    return await to_user_out(db, user)


@router.get("/{tg_user_id}", response_model=UserOut)
async def get_user(tg_user_id: int, db: AsyncSession = Depends(get_db)) -> UserOut:
    result = await db.execute(select(User).where(User.tg_user_id == tg_user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=404, detail="Foydalanuvchi topilmadi")
    return await to_user_out(db, user)

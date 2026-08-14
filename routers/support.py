from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models import SupportTicket, User
from schemas import SupportTicketIn, SupportTicketOut
from security import verify_internal_secret

router = APIRouter(prefix="/api/support", tags=["support"], dependencies=[Depends(verify_internal_secret)])


@router.post("/tickets", response_model=SupportTicketOut)
async def create_ticket(payload: SupportTicketIn, db: AsyncSession = Depends(get_db)) -> SupportTicketOut:
    user_result = await db.execute(select(User).where(User.tg_user_id == payload.tg_user_id))
    user = user_result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=404, detail="Foydalanuvchi topilmadi")

    ticket = SupportTicket(user_id=user.id, message=payload.message)
    db.add(ticket)
    await db.commit()
    await db.refresh(ticket)
    return ticket


@router.get("/tickets", response_model=list[SupportTicketOut])
async def list_tickets(answered: bool | None = None, db: AsyncSession = Depends(get_db)) -> list[SupportTicketOut]:
    query = select(SupportTicket).order_by(SupportTicket.created_at.desc())
    if answered is not None:
        query = query.where(SupportTicket.is_answered == answered)
    result = await db.execute(query)
    return list(result.scalars().all())

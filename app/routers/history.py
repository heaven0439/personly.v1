# backend/app/routers/history.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import or_, desc

from ..db.database import get_db
from ..db.models import User, Contact, CallRecord
from ..utils.security import verify_firebase_token
from ..schemas.history import CallRecordCreate, CallRecordResponse

router = APIRouter(prefix="/api/history", tags=["Call History"])

@router.post("/")
async def log_call(req: CallRecordCreate, db: AsyncSession = Depends(get_db), token: dict = Depends(verify_firebase_token)):
    owner_uid = token.get("uid")
    user_query = await db.execute(select(User).where(User.firebase_uid == owner_uid))
    user = user_query.scalars().first()
    
    if not user: raise HTTPException(status_code=404, detail="User not found.")

    if req.is_caller:
        caller_id = user.personly_id
        receiver_id = req.target_personly_id
    else:
        caller_id = req.target_personly_id
        receiver_id = user.personly_id
        
    record = CallRecord(
        caller_personly_id=caller_id,
        receiver_personly_id=receiver_id,
        call_type=req.call_type,
        status=req.status,
        duration_seconds=req.duration_seconds
    )
    db.add(record)
    await db.commit()
    return {"message": "Call logged successfully"}

@router.get("/", response_model=list[CallRecordResponse])
async def get_history(db: AsyncSession = Depends(get_db), token: dict = Depends(verify_firebase_token)):
    owner_uid = token.get("uid")
    user_query = await db.execute(select(User).where(User.firebase_uid == owner_uid))
    user = user_query.scalars().first()
    
    query = select(CallRecord).where(
        or_(CallRecord.caller_personly_id == user.personly_id, CallRecord.receiver_personly_id == user.personly_id)
    ).order_by(desc(CallRecord.created_at))
    
    records = (await db.execute(query)).scalars().all()
    
    history_list = []
    for r in records:
        is_incoming = r.receiver_personly_id == user.personly_id
        other_party_id = r.caller_personly_id if is_incoming else r.receiver_personly_id
        
        contact_query = await db.execute(select(Contact).where(Contact.owner_uid == owner_uid, Contact.contact_personly_id == other_party_id))
        contact = contact_query.scalars().first()
        
        other_party_name = contact.custom_label if contact else f"ID: {other_party_id}"
            
        history_list.append(CallRecordResponse(
            id=r.id, other_party_id=other_party_id, other_party_name=other_party_name,
            call_type=r.call_type, status=r.status, duration_seconds=r.duration_seconds,
            is_incoming=is_incoming, created_at=r.created_at
        ))
        
    return history_list
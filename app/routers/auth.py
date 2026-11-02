# backend/app/routers/auth.py
from fastapi import APIRouter, HTTPException, BackgroundTasks, status, Depends
from datetime import datetime, timedelta, timezone
import firebase_admin.auth as firebase_auth
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from ..schemas.auth import RegisterOTPRequest, VerifyOTPRequest, ChangeIdRequest
from ..utils.security import encrypt_password, decrypt_password, generate_otp, generate_unique_personly_id, verify_firebase_token
from ..utils.email import send_otp_email
from ..db.database import get_db
from ..db.models import User

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

PENDING_REGISTRATIONS = {}

@router.post("/register/request-otp")
async def request_otp(req: RegisterOTPRequest, background_tasks: BackgroundTasks):
    try:
        firebase_auth.get_user_by_email(req.email)
        raise HTTPException(status_code=400, detail="An account with this email already exists.")
    except firebase_auth.UserNotFoundError:
        pass 

    otp = generate_otp()
    encrypted_pw = encrypt_password(req.password)
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=10)

    PENDING_REGISTRATIONS[req.email] = {
        "full_name": req.full_name,
        "encrypted_password": encrypted_pw,
        "otp": otp,
        "expires_at": expires_at
    }

    background_tasks.add_task(send_otp_email, req.email, otp)
    return {"message": "Verification code sent to your email."}

@router.post("/register/verify-otp")
async def verify_otp(req: VerifyOTPRequest, db: AsyncSession = Depends(get_db)):
    record = PENDING_REGISTRATIONS.get(req.email)
    
    if not record: raise HTTPException(status_code=400, detail="No pending registration found for this email.")
    if datetime.now(timezone.utc) > record["expires_at"]:
        del PENDING_REGISTRATIONS[req.email]
        raise HTTPException(status_code=400, detail="Verification code has expired.")
    if record["otp"] != req.otp: raise HTTPException(status_code=400, detail="Invalid verification code.")
    
    try:
        plain_password = decrypt_password(record["encrypted_password"])
        firebase_user = firebase_auth.create_user(email=req.email, password=plain_password, display_name=record["full_name"], email_verified=True)
        
        personly_id = await generate_unique_personly_id(db)
        new_user = User(firebase_uid=firebase_user.uid, personly_id=personly_id, email=req.email, display_name=record["full_name"])
        db.add(new_user)
        await db.commit()
        
        custom_token = firebase_auth.create_custom_token(firebase_user.uid)
        del PENDING_REGISTRATIONS[req.email]

        return {"message": "Account created successfully.", "custom_token": custom_token.decode('utf-8')}
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create account: {str(e)}")

@router.post("/sync")
async def sync_user(db: AsyncSession = Depends(get_db), decoded_token: dict = Depends(verify_firebase_token)):
    firebase_uid = decoded_token.get("uid")
    email = decoded_token.get("email")
    display_name = decoded_token.get("name") or decoded_token.get("email").split("@")[0]
    photo_url = decoded_token.get("picture")

    result = await db.execute(select(User).where(User.firebase_uid == firebase_uid))
    user = result.scalars().first()

    if not user:
        personly_id = await generate_unique_personly_id(db)
        user = User(firebase_uid=firebase_uid, personly_id=personly_id, email=email, display_name=display_name, photo_url=photo_url)
        db.add(user)
        await db.commit()
        await db.refresh(user)

    return {"personly_id": user.personly_id, "display_name": user.display_name, "email": user.email, "photo_url": user.photo_url}

@router.put("/change-id")
async def change_personly_id(req: ChangeIdRequest, db: AsyncSession = Depends(get_db), token: dict = Depends(verify_firebase_token)):
    owner_uid = token.get("uid")
    
    # 1. Check if requested ID is vacant
    existing = await db.execute(select(User).where(User.personly_id == req.new_personly_id))
    if existing.scalars().first():
        raise HTTPException(status_code=400, detail="This Personly ID is already taken. Try another.")
        
    # 2. Update the user's ID
    user_query = await db.execute(select(User).where(User.firebase_uid == owner_uid))
    user = user_query.scalars().first()
    if not user: raise HTTPException(status_code=404, detail="User not found.")
        
    user.personly_id = req.new_personly_id
    await db.commit()
    return {"message": "Personly ID claimed successfully!", "new_id": user.personly_id}
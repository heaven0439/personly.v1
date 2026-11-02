# backend/app/utils/security.py
import os
import random
import string
from cryptography.fernet import Fernet
from fastapi import HTTPException, Security, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import firebase_admin.auth as auth
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from ..db.models import User

security = HTTPBearer()

def get_cipher():
    key = os.getenv("ENCRYPTION_KEY")
    if not key:
        raise ValueError("ENCRYPTION_KEY environment variable is not set")
    return Fernet(key.encode())

def encrypt_password(password: str) -> str:
    cipher_suite = get_cipher()
    return cipher_suite.encrypt(password.encode()).decode()

def decrypt_password(encrypted_password: str) -> str:
    cipher_suite = get_cipher()
    return cipher_suite.decrypt(encrypted_password.encode()).decode()

def generate_otp(length: int = 6) -> str:
    return ''.join(random.SystemRandom().choices(string.digits, k=length))

async def generate_unique_personly_id(db: AsyncSession) -> int:
    """Generates a random 5-digit ID and ensures it doesn't already exist in the database."""
    while True:
        candidate_id = random.randint(10000, 99999)
        result = await db.execute(select(User).where(User.personly_id == candidate_id))
        if not result.scalars().first():
            return candidate_id

def verify_firebase_token(credentials: HTTPAuthorizationCredentials = Security(security)):
    """Validates the Firebase Bearer token and returns the decoded user payload."""
    token = credentials.credentials
    try:
        decoded_token = auth.verify_id_token(token)
        return decoded_token
    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid authentication token")
# backend/app/db/models.py
from sqlalchemy import Column, String, Integer, DateTime
from sqlalchemy.sql import func
import uuid
from .database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    firebase_uid = Column(String, unique=True, index=True, nullable=False)
    personly_id = Column(Integer, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    display_name = Column(String, nullable=False)
    photo_url = Column(String, nullable=True)
    theme_preference = Column(String, default="light")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Contact(Base):
    __tablename__ = "contacts"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    owner_uid = Column(String, index=True, nullable=False) 
    contact_personly_id = Column(Integer, index=True, nullable=False)
    custom_label = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class CallRecord(Base):
    __tablename__ = "call_history"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    caller_personly_id = Column(Integer, index=True, nullable=False)
    receiver_personly_id = Column(Integer, index=True, nullable=False)
    call_type = Column(String, nullable=False) 
    status = Column(String, nullable=False) 
    duration_seconds = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
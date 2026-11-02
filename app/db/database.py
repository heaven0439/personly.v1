# backend/app/db/database.py
import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base

# Define the database URL (SQLite for local development)
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./personly.db")

# Create the async engine with the concurrency/locking fix
engine = create_async_engine(
    SQLALCHEMY_DATABASE_URL,
    echo=False,
    connect_args={"check_same_thread": False, "timeout": 15}
)

# Create the session factory
SessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# Base class for SQLAlchemy models
Base = declarative_base()

# Dependency to get the DB session for our routers
async def get_db():
    async with SessionLocal() as session:
        yield session
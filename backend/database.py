from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker


# --------------------------------------------------
# DATABASE FILE LOCATION
# --------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent

DATABASE_DIR = PROJECT_ROOT / "database"

DATABASE_DIR.mkdir(
    exist_ok=True
)

DATABASE_PATH = DATABASE_DIR / "payment_verification.db"

DATABASE_URL = (
    "sqlite:///" + DATABASE_PATH.as_posix()
)


# --------------------------------------------------
# DATABASE ENGINE
# --------------------------------------------------

engine = create_engine(
    DATABASE_URL,
    connect_args={
        "check_same_thread": False
    }
)


# --------------------------------------------------
# DATABASE SESSION
# --------------------------------------------------

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False
)


# --------------------------------------------------
# BASE MODEL CLASS
# --------------------------------------------------

class Base(DeclarativeBase):
    pass
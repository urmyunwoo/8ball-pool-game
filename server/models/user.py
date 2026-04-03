from datetime import datetime
from sqlalchemy import Integer, String, DateTime
from sqlalchemy.orm import Mapped, mapped_column
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from database import Base


class User(Base):
    __tablename__ = "users"

    id            : Mapped[int]      = mapped_column(Integer, primary_key=True, autoincrement=True)
    email         : Mapped[str]      = mapped_column(String(255), unique=True, nullable=False)
    nickname      : Mapped[str]      = mapped_column(String(50), nullable=False)
    password_hash : Mapped[str]      = mapped_column(String(255), nullable=False)
    created_at    : Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

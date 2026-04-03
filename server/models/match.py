from datetime import datetime
from typing import Optional
from sqlalchemy import Integer, String, DateTime, ForeignKey, Enum
from sqlalchemy.orm import Mapped, mapped_column
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from database import Base


class Match(Base):
    __tablename__ = "matches"

    id              : Mapped[int]           = mapped_column(Integer, primary_key=True, autoincrement=True)
    player1_id      : Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)
    player2_id      : Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)
    winner_id       : Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)
    game_mode       : Mapped[str]           = mapped_column(
        Enum("local", "online", "practice", name="game_mode_enum"),
        default="local",
    )
    duration_seconds: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    played_at       : Mapped[datetime]      = mapped_column(DateTime, default=datetime.utcnow)

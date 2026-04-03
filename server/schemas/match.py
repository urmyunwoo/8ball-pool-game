from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class MatchCreate(BaseModel):
    winner_id:        Optional[int] = None
    loser_id:         Optional[int] = None
    game_mode:        str           = "local"
    duration_seconds: Optional[int] = None


class MatchRecord(BaseModel):
    id:              int
    game_mode:       str
    won:             bool
    opponent_name:   Optional[str]
    played_at:       datetime

    class Config:
        from_attributes = True


class MyRecordsResponse(BaseModel):
    stats:   dict
    history: list[MatchRecord]


class LeaderboardEntry(BaseModel):
    rank:      int
    user_id:   int
    nickname:  str
    wins:      int
    losses:    int
    win_rate:  float


class LeaderboardResponse(BaseModel):
    rankings: list[LeaderboardEntry]

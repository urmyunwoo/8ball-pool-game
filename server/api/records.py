"""
전적 API: 경기 저장, 내 기록 조회, 리더보드.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from database import get_db
from models.user  import User
from models.match import Match
from schemas.match import MatchCreate, MyRecordsResponse, LeaderboardResponse, LeaderboardEntry
from api.deps import get_current_user

router = APIRouter(prefix="/records", tags=["records"])


@router.post("/match", status_code=201)
async def save_match(
    req:          MatchCreate,
    db:           AsyncSession = Depends(get_db),
    current_user: User         = Depends(get_current_user),
):
    match = Match(
        player1_id       = current_user.id,
        player2_id       = req.loser_id,
        winner_id        = current_user.id if req.winner_id == current_user.id else req.loser_id,
        game_mode        = req.game_mode,
        duration_seconds = req.duration_seconds,
    )
    db.add(match)
    await db.commit()
    return {"message": "저장 완료"}


@router.get("/me")
async def my_records(
    db:           AsyncSession = Depends(get_db),
    current_user: User         = Depends(get_current_user),
):
    uid = current_user.id

    # 전체 통계
    result = await db.execute(
        select(Match).where(
            (Match.player1_id == uid) | (Match.player2_id == uid)
        ).order_by(Match.played_at.desc()).limit(20)
    )
    matches = result.scalars().all()

    wins   = sum(1 for m in matches if m.winner_id == uid)
    losses = len(matches) - wins

    history = []
    for m in matches:
        opp_id = m.player2_id if m.player1_id == uid else m.player1_id
        opp_name = None
        if opp_id:
            r2 = await db.execute(select(User).where(User.id == opp_id))
            opp = r2.scalar_one_or_none()
            opp_name = opp.nickname if opp else None

        history.append({
            "id":            m.id,
            "game_mode":     m.game_mode,
            "won":           m.winner_id == uid,
            "opponent_name": opp_name,
            "played_at":     m.played_at.isoformat(),
        })

    return {
        "stats":   {"wins": wins, "losses": losses},
        "history": history,
    }


@router.get("/leaderboard")
async def leaderboard(db: AsyncSession = Depends(get_db)):
    # 전체 승리 횟수 기준 상위 10명
    result = await db.execute(
        select(
            User.id,
            User.nickname,
            func.count(Match.id).label("wins"),
        )
        .join(Match, Match.winner_id == User.id)
        .group_by(User.id, User.nickname)
        .order_by(func.count(Match.id).desc())
        .limit(10)
    )
    rows = result.all()

    rankings = []
    for rank, row in enumerate(rows, 1):
        # 총 경기 수
        total_r = await db.execute(
            select(func.count(Match.id)).where(
                (Match.player1_id == row.id) | (Match.player2_id == row.id)
            )
        )
        total = total_r.scalar() or 0
        rate  = round(row.wins / total * 100, 1) if total else 0.0
        rankings.append({
            "rank":     rank,
            "user_id":  row.id,
            "nickname": row.nickname,
            "wins":     row.wins,
            "losses":   total - row.wins,
            "win_rate": rate,
        })

    return {"rankings": rankings}

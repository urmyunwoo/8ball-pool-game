"""
인증 API: 회원가입, 로그인, 내 정보 조회.
"""
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from passlib.context import CryptContext
from jose import jwt
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from database import get_db
from models.user import User
from schemas.auth import RegisterRequest, LoginRequest, TokenResponse, UserInfo
from config import JWT_SECRET, JWT_ALGORITHM, JWT_EXPIRE_HOURS
from api.deps import get_current_user

router = APIRouter(prefix="/auth", tags=["auth"])
pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")


def _make_token(user_id: int, nickname: str) -> str:
    expire = datetime.utcnow() + timedelta(hours=JWT_EXPIRE_HOURS)
    return jwt.encode(
        {"sub": str(user_id), "nickname": nickname, "exp": expire},
        JWT_SECRET, algorithm=JWT_ALGORITHM,
    )


@router.post("/register", status_code=201)
async def register(req: RegisterRequest, db: AsyncSession = Depends(get_db)):
    # 이메일 중복 체크
    result = await db.execute(select(User).where(User.email == req.email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="이미 사용 중인 이메일입니다")

    user = User(
        email         = req.email,
        nickname      = req.nickname,
        password_hash = pwd_ctx.hash(req.password),
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return {"message": "가입 완료", "user_id": user.id}


@router.post("/login", response_model=TokenResponse)
async def login(req: LoginRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == req.email))
    user   = result.scalar_one_or_none()
    if not user or not pwd_ctx.verify(req.password, user.password_hash):
        raise HTTPException(status_code=401, detail="이메일 또는 비밀번호가 틀렸습니다")

    token = _make_token(user.id, user.nickname)
    return TokenResponse(access_token=token, nickname=user.nickname, user_id=user.id)


@router.get("/me", response_model=UserInfo)
async def get_me(current_user: User = Depends(get_current_user)):
    return UserInfo(id=current_user.id, email=current_user.email, nickname=current_user.nickname)

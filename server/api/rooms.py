"""
방 REST API: 방 생성, 입장, 조회.
"""
from fastapi import APIRouter, Depends, HTTPException
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from rooms import room_manager
from api.deps import get_current_user, get_optional_user
from models.user import User

router = APIRouter(prefix="/rooms", tags=["rooms"])


@router.post("/create", status_code=201)
async def create_room(current_user: User = Depends(get_current_user)):
    room = room_manager.create_room(host_user_id=current_user.id)
    return {
        "room_id":   room.room_id,
        "room_code": room.room_code,
        "status":    room.status,
    }


@router.post("/join")
async def join_room(body: dict, current_user: User = Depends(get_current_user)):
    code = body.get("room_code", "").upper()
    room = room_manager.get_by_code(code)
    if not room:
        raise HTTPException(status_code=404, detail="방을 찾을 수 없습니다")
    if room.status != "waiting":
        raise HTTPException(status_code=400, detail="이미 시작된 방입니다")
    room.guest_id = current_user.id
    return {
        "room_id":   room.room_id,
        "room_code": room.room_code,
        "status":    room.status,
    }


@router.get("/{room_id}")
async def get_room(room_id: str, current_user: User = Depends(get_current_user)):
    room = room_manager.get_by_id(room_id)
    if not room:
        raise HTTPException(status_code=404, detail="방을 찾을 수 없습니다")
    return room_manager.to_dict(room)

"""
인메모리 방(Room) 관리자.
WebSocket 연결은 각 방에 최대 2개.
"""
import random
import string
from dataclasses import dataclass, field
from typing import Optional
from fastapi import WebSocket


def _gen_code(length: int = 6) -> str:
    return "".join(random.choices(string.ascii_uppercase + string.digits, k=length))


@dataclass
class Room:
    room_id:   str
    room_code: str
    host_id:   Optional[int]     = None
    guest_id:  Optional[int]     = None
    host_ws:   Optional[WebSocket] = None
    guest_ws:  Optional[WebSocket] = None
    status:    str               = "waiting"  # waiting | playing | finished
    game_state: dict             = field(default_factory=dict)

    @property
    def is_full(self) -> bool:
        return self.host_ws is not None and self.guest_ws is not None

    async def broadcast(self, msg: dict, exclude: Optional[WebSocket] = None):
        import json
        data = json.dumps(msg, ensure_ascii=False)
        for ws in (self.host_ws, self.guest_ws):
            if ws and ws != exclude:
                try:
                    await ws.send_text(data)
                except Exception:
                    pass

    async def send_to(self, ws: WebSocket, msg: dict):
        import json
        try:
            await ws.send_text(json.dumps(msg, ensure_ascii=False))
        except Exception:
            pass


class RoomManager:
    def __init__(self):
        self._rooms: dict[str, Room] = {}   # room_id → Room
        self._code_map: dict[str, str] = {} # room_code → room_id

    def create_room(self, host_user_id: Optional[int] = None) -> Room:
        import uuid
        room_id   = str(uuid.uuid4())
        room_code = _gen_code()
        while room_code in self._code_map:
            room_code = _gen_code()

        room = Room(room_id=room_id, room_code=room_code, host_id=host_user_id)
        self._rooms[room_id]       = room
        self._code_map[room_code]  = room_id
        return room

    def get_by_id(self, room_id: str) -> Optional[Room]:
        return self._rooms.get(room_id)

    def get_by_code(self, room_code: str) -> Optional[Room]:
        room_id = self._code_map.get(room_code.upper())
        return self._rooms.get(room_id) if room_id else None

    def remove(self, room_id: str):
        room = self._rooms.pop(room_id, None)
        if room:
            self._code_map.pop(room.room_code, None)

    def to_dict(self, room: Room) -> dict:
        return {
            "room_id":   room.room_id,
            "room_code": room.room_code,
            "status":    room.status,
        }


# 앱 전체에서 공유하는 싱글톤
room_manager = RoomManager()

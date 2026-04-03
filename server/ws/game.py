"""
WebSocket 게임 핸들러.
각 방마다 host / guest 두 연결을 관리하고 메시지를 중계한다.
"""
import json
import math
from fastapi import WebSocket, WebSocketDisconnect, Query
from jose import jwt, JWTError
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from rooms import room_manager, Room
from config import JWT_SECRET, JWT_ALGORITHM


def _decode_token(token: str) -> dict | None:
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except JWTError:
        return None


async def game_ws_endpoint(websocket: WebSocket, room_id: str, token: str = Query("")):
    """
    /ws/game/{room_id}?token=...
    """
    await websocket.accept()

    room = room_manager.get_by_id(room_id)
    if room is None:
        await websocket.send_text(json.dumps({"type": "error", "message": "방이 존재하지 않습니다"}))
        await websocket.close()
        return

    # 토큰으로 역할 결정
    payload   = _decode_token(token) if token else None
    user_id   = int(payload["sub"]) if payload else None
    nickname  = payload.get("nickname", "플레이어") if payload else "플레이어"

    # host vs guest 배정
    is_host = (room.host_ws is None)
    if is_host:
        room.host_ws = websocket
    else:
        if room.guest_ws is not None:
            await websocket.send_text(json.dumps({"type": "error", "message": "방이 가득 찼습니다"}))
            await websocket.close()
            return
        room.guest_ws = websocket

    role = "host" if is_host else "guest"
    await room.send_to(websocket, {"type": "joined", "role": role, "your_turn": is_host})
    await room.broadcast({"type": "opponent_name", "name": nickname}, exclude=websocket)

    # 방이 꽉 차면 게임 시작
    if room.is_full:
        room.status = "playing"
        init_state  = _build_initial_state()
        room.game_state = init_state
        await room.broadcast({"type": "init", "balls": init_state["balls"]})

    try:
        while True:
            raw = await websocket.receive_text()
            msg = json.loads(raw)
            msg_type = msg.get("type")

            if msg_type == "shot":
                # 상대방에게 샷 정보 전달
                await room.broadcast(
                    {"type": "opponent_shot", "angle": msg["angle"], "power": msg["power"]},
                    exclude=websocket,
                )

            elif msg_type == "turn_end":
                # 턴 종료 → 턴 교대
                your_turn_for_opponent = True
                await room.broadcast(
                    {"type": "turn_switch", "your_turn": your_turn_for_opponent},
                    exclude=websocket,
                )
                # 현재 플레이어는 상대 턴
                await room.send_to(websocket, {"type": "turn_switch", "your_turn": False})

            elif msg_type == "ball_in_hand":
                await room.broadcast(msg, exclude=websocket)

            elif msg_type == "chat":
                await room.broadcast(
                    {"type": "chat", "sender": nickname, "message": msg.get("message", "")},
                    exclude=websocket,
                )

            elif msg_type == "game_over":
                await room.broadcast({"type": "game_over", "winner": msg.get("winner", "")})
                room.status = "finished"

    except WebSocketDisconnect:
        # 연결 해제
        if is_host:
            room.host_ws = None
        else:
            room.guest_ws = None
        await room.broadcast({"type": "error", "message": "상대방이 연결을 끊었습니다"})


def _build_initial_state() -> dict:
    """초기 공 배치 (서버에서 계산해서 양쪽에 동일하게 전달)."""
    import uuid

    TABLE_X, TABLE_Y = 80, 100
    TABLE_W, TABLE_H = 1240, 620
    BALL_R = 14

    # 큐볼
    cue_x = TABLE_X + TABLE_W * 0.25
    cue_y = TABLE_Y + TABLE_H * 0.50

    # 랙
    apex_x = TABLE_X + TABLE_W * 0.70
    apex_y = TABLE_Y + TABLE_H * 0.50
    r = BALL_R * 2 + 1

    order = [
        [1],
        [2, 9],
        [3, 8, 10],
        [4, 11, 7, 12],
        [5, 13, 6, 14, 15],
    ]

    balls = [{"n": 0, "x": round(cue_x, 2), "y": round(cue_y, 2), "vx": 0, "vy": 0, "pocketed": False}]
    for row_i, row in enumerate(order):
        row_x = apex_x + row_i * r * math.cos(math.radians(30))
        for col_j, num in enumerate(row):
            offset = col_j - (len(row) - 1) / 2
            row_y  = apex_y + row_i * r * 0.5 + offset * r
            balls.append({
                "n": num, "x": round(row_x, 2), "y": round(row_y, 2),
                "vx": 0, "vy": 0, "pocketed": False,
            })

    return {"balls": balls}

# -*- coding: utf-8 -*-
"""
FastAPI 서버 진입점.
실행: uvicorn main:app --reload --host 0.0.0.0 --port 8000
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from database import create_tables
from api.auth    import router as auth_router
from api.records import router as records_router
from api.rooms   import router as rooms_router
from ws.game     import game_ws_endpoint
from config import SERVER_HOST, SERVER_PORT

app = FastAPI(title="Pool Game API", version="1.0.0")

# CORS (개발 중 전체 허용)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록
app.include_router(auth_router)
app.include_router(records_router)
app.include_router(rooms_router)

# WebSocket
app.add_api_websocket_route("/ws/game/{room_id}", game_ws_endpoint)

# 정적 파일 (웹 게임)
static_dir = os.path.join(os.path.dirname(__file__), "static")
app.mount("/static", StaticFiles(directory=static_dir), name="static")


@app.get("/play")
async def play():
    """브라우저에서 게임 플레이."""
    return FileResponse(os.path.join(static_dir, "index.html"))


@app.on_event("startup")
async def startup():
    await create_tables()
    print("=" * 50)
    print("🎱 Pool Game API Server 시작")
    print(f"   http://{SERVER_HOST}:{SERVER_PORT}/docs  (Swagger UI)")
    print(f"   http://{SERVER_HOST}:{SERVER_PORT}/play  (웹 게임)")
    print("=" * 50)


@app.get("/")
async def root():
    return {"message": "Pool Game API", "version": "1.0.0"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host=SERVER_HOST, port=SERVER_PORT, reload=True)

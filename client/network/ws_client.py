"""
WebSocket 클라이언트 (별도 스레드에서 asyncio 루프 실행).
"""
import asyncio
import json
import threading
try:
    import websockets
except ImportError:
    websockets = None
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from config import WS_URL


class WsClient:
    """
    별도 데몬 스레드에서 asyncio WebSocket 연결을 유지한다.
    메인 스레드에서 send()를 호출하면 비동기 큐에 전달되어 전송된다.
    수신 메시지는 on_message(dict) 콜백으로 전달된다.
    """

    def __init__(self, base_url: str, room_id: str, token: str = ""):
        self._url    = f"{base_url}/ws/game/{room_id}"
        self._token  = token
        self._loop: asyncio.AbstractEventLoop | None = None
        self._ws     = None
        self._queue: asyncio.Queue | None = None
        self._running = True
        self.on_message = None   # callback(dict)

    def run(self):
        """스레드 메인 함수."""
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        self._loop.run_until_complete(self._main())

    async def _main(self):
        self._queue = asyncio.Queue()
        uri = self._url
        if self._token:
            uri += f"?token={self._token}"
        try:
            async with websockets.connect(uri) as ws:
                self._ws = ws
                await asyncio.gather(
                    self._recv_loop(ws),
                    self._send_loop(ws),
                )
        except Exception as e:
            print(f"[WS] 연결 오류: {e}")

    async def _recv_loop(self, ws):
        async for raw in ws:
            try:
                msg = json.loads(raw)
                if self.on_message:
                    self.on_message(msg)
            except Exception:
                pass
            if not self._running:
                break

    async def _send_loop(self, ws):
        while self._running:
            try:
                msg = await asyncio.wait_for(self._queue.get(), timeout=0.1)
                await ws.send(json.dumps(msg))
            except asyncio.TimeoutError:
                pass
            except Exception:
                break

    def send(self, data: dict):
        """메인 스레드에서 호출 — 비동기 큐에 메시지 추가."""
        if self._loop and self._queue:
            asyncio.run_coroutine_threadsafe(
                self._queue.put(data), self._loop
            )

    def close(self):
        self._running = False
        if self._loop:
            self._loop.call_soon_threadsafe(self._loop.stop)

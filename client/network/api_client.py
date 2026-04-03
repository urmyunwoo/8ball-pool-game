"""
FastAPI 서버 REST 호출 클라이언트.
서버가 없어도 로컬 2인 / 연습은 동작하도록 예외 처리.
"""
try:
    import requests
except ImportError:
    requests = None
import json
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from config import SERVER_URL, TOKEN_FILE


class ApiClient:

    def __init__(self, base_url: str = SERVER_URL):
        self._base = base_url.rstrip("/")
        self._token: str | None = self._load_token()

    # ── token ────────────────────────────────────────

    def _load_token(self) -> str | None:
        try:
            with open(TOKEN_FILE, "r") as f:
                return json.load(f).get("token")
        except Exception:
            return None

    def _save_token(self, token: str):
        self._token = token
        try:
            with open(TOKEN_FILE, "w") as f:
                json.dump({"token": token}, f)
        except Exception:
            pass

    def clear_token(self):
        self._token = None
        try:
            os.remove(TOKEN_FILE)
        except Exception:
            pass

    def _headers(self) -> dict:
        h = {"Content-Type": "application/json"}
        if self._token:
            h["Authorization"] = f"Bearer {self._token}"
        return h

    # ── auth ─────────────────────────────────────────

    def register(self, email: str, password: str, nickname: str) -> tuple[bool, dict]:
        try:
            r = requests.post(
                f"{self._base}/auth/register",
                json={"email": email, "password": password, "nickname": nickname},
                timeout=8,
            )
            return r.status_code == 201, r.json()
        except Exception as e:
            return False, {"detail": str(e)}

    def login(self, email: str, password: str) -> tuple[bool, dict]:
        try:
            r = requests.post(
                f"{self._base}/auth/login",
                json={"email": email, "password": password},
                timeout=8,
            )
            if r.status_code == 200:
                data = r.json()
                self._save_token(data["access_token"])
                return True, data
            return False, r.json()
        except Exception as e:
            return False, {"detail": str(e)}

    def get_me(self) -> tuple[bool, dict]:
        try:
            r = requests.get(
                f"{self._base}/auth/me",
                headers=self._headers(),
                timeout=8,
            )
            return r.status_code == 200, r.json()
        except Exception as e:
            return False, {"detail": str(e)}

    # ── records ──────────────────────────────────────

    def save_match(self, winner_id, loser_id, game_mode: str = "local") -> tuple[bool, dict]:
        try:
            r = requests.post(
                f"{self._base}/records/match",
                json={
                    "winner_id": winner_id,
                    "loser_id":  loser_id,
                    "game_mode": game_mode,
                },
                headers=self._headers(),
                timeout=8,
            )
            return r.status_code == 201, r.json()
        except Exception as e:
            return False, {"detail": str(e)}

    def get_my_records(self) -> tuple[bool, dict]:
        try:
            r = requests.get(
                f"{self._base}/records/me",
                headers=self._headers(),
                timeout=8,
            )
            return r.status_code == 200, r.json()
        except Exception as e:
            return False, {"detail": str(e)}

    def get_leaderboard(self) -> tuple[bool, dict]:
        try:
            r = requests.get(
                f"{self._base}/records/leaderboard",
                headers=self._headers(),
                timeout=8,
            )
            return r.status_code == 200, r.json()
        except Exception as e:
            return False, {"detail": str(e)}

    # ── rooms ─────────────────────────────────────────

    def create_room(self) -> tuple[bool, dict]:
        try:
            r = requests.post(
                f"{self._base}/rooms/create",
                headers=self._headers(),
                timeout=8,
            )
            return r.status_code == 201, r.json()
        except Exception as e:
            return False, {"detail": str(e)}

    def join_room(self, room_code: str) -> tuple[bool, dict]:
        try:
            r = requests.post(
                f"{self._base}/rooms/join",
                json={"room_code": room_code},
                headers=self._headers(),
                timeout=8,
            )
            return r.status_code == 200, r.json()
        except Exception as e:
            return False, {"detail": str(e)}

    def get_room(self, room_id: str) -> tuple[bool, dict]:
        try:
            r = requests.get(
                f"{self._base}/rooms/{room_id}",
                headers=self._headers(),
                timeout=8,
            )
            return r.status_code == 200, r.json()
        except Exception as e:
            return False, {"detail": str(e)}

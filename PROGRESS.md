# 포켓볼 게임 구현 진행상황

## 기술 스택
| 항목 | 선택 |
|------|------|
| 클라이언트 | Python + Pygame (데스크톱 앱) |
| 백엔드 | Python + FastAPI |
| DB | MySQL (학원 서버 / Oracle Cloud 배포) |
| 실시간 | WebSocket |
| 인증 | JWT + bcrypt |
| 웹 버전 | HTML5 Canvas (deploy/ 및 server/static/) |

---

## Phase 1 — 프로젝트 세팅 ✅
- [x] `client/` / `server/` / `deploy/` 폴더 구조 생성
- [x] `client/requirements.txt` / `server/requirements.txt`
- [x] `client/.env` / `server/.env.example`
- [x] `install.bat` / `run_game.bat` / `run_server.bat`
- [x] `.gitignore` 설정

---

## Phase 2 — 게임 엔진 ✅
- [x] `client/game/physics.py` — 공 이동, 충돌, 마찰, 포켓 감지 (커스텀 물리)
- [x] `client/game/table.py` — 당구대 렌더링 (우드 레일, 펠트, 포켓, 공 그리기)
- [x] `client/game/cue.py` — 큐대 조준 / 파워 차징 / 렌더링
- [x] `client/game/game_logic.py` — 8볼 규칙 엔진 (상태머신: BREAK→PLAYING→FINISH)
- [x] `client/game/carom_logic.py` — 3구/4구 캐롬 당구 규칙 엔진
- [x] `client/game/sound.py` — 효과음 (합성음 자동 생성, .wav 파일 있으면 교체 가능)
- [x] `client/game/replay.py` — 리플레이 기능

---

## Phase 3 — UI & 씬 ✅
- [x] `client/main.py` — SceneManager + 게임 루프
- [x] `client/config.py` — 모든 상수 / 색상 / 설정
- [x] `client/ui/button.py` — 공통 버튼 (hover/press 효과, 골드 테두리)
- [x] `client/ui/text_input.py` — 텍스트 입력창 (커서 깜빡임, 비밀번호 마스킹)
- [x] `client/ui/dialog.py` — 팝업 다이얼로그 (AI 준비중, 게임결과 등)
- [x] `client/ui/chat_box.py` — 인게임 채팅 UI
- [x] `client/ui/game_hud.py` — 게임 HUD
- [x] `client/scenes/menu_scene.py` — 메인 메뉴
- [x] `client/scenes/auth_scene.py` — 로그인 / 회원가입 탭
- [x] `client/scenes/local_game_scene.py` — 로컬 2인 게임
- [x] `client/scenes/practice_scene.py` — 혼자 연습 모드
- [x] `client/scenes/carom_game_scene.py` — 캐롬 당구 (3구/4구)
- [x] `client/scenes/lobby_scene.py` — 원격 대결 대기실
- [x] `client/scenes/online_game_scene.py` — 원격 게임 (WebSocket 동기화 + 채팅)
- [x] `client/scenes/records_scene.py` — 전적 보기

---

## Phase 4 — 서버 ✅
- [x] `server/main.py` — FastAPI 앱 + CORS + 웹 게임(/play) + 시작 시 테이블 자동 생성
- [x] `server/config.py` — 환경변수 로드 (DB, JWT, 서버 포트)
- [x] `server/database.py` — SQLAlchemy 비동기 엔진 + 세션
- [x] `server/models/user.py` — users 테이블
- [x] `server/models/match.py` — matches 테이블
- [x] `server/api/auth.py` — POST /auth/register, POST /auth/login, GET /auth/me
- [x] `server/api/deps.py` — JWT 인증 의존성
- [x] `server/api/records.py` — POST /records/match, GET /records/me, GET /records/leaderboard
- [x] `server/api/rooms.py` — POST /rooms/create, POST /rooms/join, GET /rooms/{id}
- [x] `server/rooms.py` — 방 인메모리 관리 (RoomManager)
- [x] `server/ws/game.py` — WebSocket /ws/game/{room_id}
- [x] `server/static/index.html` — 웹 브라우저용 게임 (HTML5 Canvas)

---

## Phase 5 — 네트워크 연동 ✅
- [x] `client/network/api_client.py` — REST 클라이언트 (로그인/가입/전적/방)
- [x] `client/network/ws_client.py` — WebSocket 클라이언트 (별도 스레드 asyncio)

---

## Phase 6 — 웹 배포 ✅
- [x] `deploy/index.html` — Netlify 배포용 웹 게임
- [x] `deploy/package.json` / `.gitignore`

---

## 남은 작업
- [ ] **서버 .env 설정** — MySQL 정보 입력 (`server/.env`)
- [ ] **효과음 파일 추가** (선택) — `client/assets/sounds/` 에 .wav 파일 넣으면 자동 적용
- [ ] **AI 모드 구현** — 현재 "준비중" 다이얼로그, 추후 확장
- [ ] **Oracle Cloud 배포** — 완성 후 서버 URL을 `client/.env`에 업데이트

---

## 실행 방법

### 간편 실행 (Windows)
```
install.bat      → 패키지 설치 (처음 한 번)
run_game.bat     → 게임 실행
run_server.bat   → 서버 실행
```

### 수동 실행
```bash
# 패키지 설치
pip install -r requirements.txt

# 게임 실행 (서버 없이도 연습/로컬 2인 가능)
cd client
python main.py

# 서버 실행 (원격 대결 / 전적 저장, 별도 터미널)
cd server
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

## DB 연결 방법
`server/.env` 파일 생성 후 수정:
```
DB_HOST=서버주소
DB_PORT=3306
DB_USER=아이디
DB_PASSWORD=비밀번호
DB_NAME=poolgame
JWT_SECRET=아무문자나랜덤으로
```

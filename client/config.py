import os
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# ── Window ─────────────────────────────────────────────
WIN_W  = 1920
WIN_H  = 1080
FPS    = 120
TITLE  = "8 Ball Pool"

# ── Sidebar ────────────────────────────────────────────
SIDEBAR_W = 300

# ── Table geometry ──────────────────────────────────────
TABLE_W       = 1200
TABLE_H       = 600
TABLE_X       = SIDEBAR_W + (WIN_W - SIDEBAR_W - TABLE_W) // 2   # 가운데 정렬
TABLE_Y       = 220
CUSHION_SIZE  = 34
POCKET_RADIUS = 25

# Pocket positions (cx, cy)
POCKETS = [
    (TABLE_X,                TABLE_Y),
    (TABLE_X + TABLE_W // 2, TABLE_Y - 6),
    (TABLE_X + TABLE_W,      TABLE_Y),
    (TABLE_X,                TABLE_Y + TABLE_H),
    (TABLE_X + TABLE_W // 2, TABLE_Y + TABLE_H + 6),
    (TABLE_X + TABLE_W,      TABLE_Y + TABLE_H),
]

# ── Ball ────────────────────────────────────────────────
BALL_RADIUS = 16

# ── Physics (웹 풀 게임 스타일 — 빠르고 경쾌한 아케이드 느낌) ──
FRICTION_DAMPING    = 0.986      # 높은 마찰 → 빠르게 감속 (고속 출발 + 깔끔한 정지)
CUSHION_RESTITUTION = 0.83       # 탄력적인 쿠션 반발
BALL_RESTITUTION    = 0.97       # 공끼리 에너지 전달 잘됨
MIN_SPEED           = 0.5        # 저속에서 즉시 정지 (질질 끌리지 않음)
PHYSICS_SUBSTEPS    = 12         # 서브스텝 (충분히 정밀)

# ── Shot ────────────────────────────────────────────────
MAX_POWER   = 1100.0             # 강한 샷 파워 (빠른 공 이동)
POWER_SCALE = 0.35

# ── Colors ──────────────────────────────────────────────
C_BG         = (15, 10, 8)
C_WOOD       = (60, 32, 16)
C_WOOD_LIGHT = (80, 48, 24)
C_FELT       = (22, 90, 30)
C_FELT_DARK  = (18, 72, 24)
C_POCKET     = (6, 6, 6)
C_GOLD       = (184, 134, 11)
C_GOLD_LIGHT = (220, 168, 40)
C_TEXT       = (230, 230, 230)
C_TEXT_DIM   = (140, 140, 140)
C_WHITE      = (255, 255, 255)
C_BLACK      = (10, 10, 10)
C_RED        = (200, 40, 40)
C_GREEN_BTN  = (30, 140, 50)
C_OVERLAY    = (0, 0, 0, 160)

# ── Sidebar / HUD Colors ──────────────────────────────
C_SIDEBAR_BG     = (28, 32, 45)
C_SIDEBAR_LIGHT  = (38, 44, 60)
C_SIDEBAR_BORDER = (48, 54, 70)
C_BTN_GREEN      = (40, 167, 70)
C_BTN_ORANGE     = (235, 145, 25)
C_BTN_BLUE       = (50, 135, 210)
C_BTN_DARK       = (45, 50, 62)
C_ACCENT_BLUE    = (60, 140, 200)

# Ball colors (number → RGB)
BALL_COLORS = {
    0:  (248, 248, 248),
    1:  (240, 190, 0),
    2:  (20,  50,  210),
    3:  (210, 30,  30),
    4:  (130, 0,   145),
    5:  (240, 110, 0),
    6:  (0,   155, 35),
    7:  (145, 20,  20),
    8:  (18,  18,  18),
    9:  (240, 190, 0),
    10: (20,  50,  210),
    11: (210, 30,  30),
    12: (130, 0,   145),
    13: (240, 110, 0),
    14: (0,   155, 35),
    15: (145, 20,  20),
}

# ── Network ─────────────────────────────────────────────
SERVER_URL = os.getenv("SERVER_URL", "http://localhost:8000")
WS_URL     = os.getenv("WS_URL",     "ws://localhost:8000")
TOKEN_FILE = os.path.join(os.path.dirname(__file__), "token.json")

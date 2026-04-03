"""
게임 HUD 컴포넌트: 사이드바, 볼 상태 바, 턴 표시.
모든 게임 씬에서 공유하는 UI 요소.
"""
import pygame
import math
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from config import (
    WIN_W, WIN_H, SIDEBAR_W, BALL_RADIUS, BALL_COLORS,
    TABLE_X, TABLE_Y, TABLE_W, TABLE_H,
    C_SIDEBAR_BG, C_SIDEBAR_LIGHT, C_SIDEBAR_BORDER,
    C_ACCENT_BLUE, C_GOLD, C_GOLD_LIGHT, C_TEXT, C_TEXT_DIM, C_RED,
)

# 폰트 캐시
_font_cache = {}

def _font(name, size, bold=False):
    key = (name, size, bold)
    if key not in _font_cache:
        _font_cache[key] = pygame.font.SysFont(name, size, bold=bold)
    return _font_cache[key]


# ── 사이드바 ─────────────────────────────────────────────

def draw_sidebar(screen, user=None, players=None, current_turn=0):
    """왼쪽 사이드바 렌더링."""
    # 배경
    pygame.draw.rect(screen, C_SIDEBAR_BG, (0, 0, SIDEBAR_W, WIN_H))
    pygame.draw.line(screen, C_SIDEBAR_BORDER,
                     (SIDEBAR_W - 1, 0), (SIDEBAR_W - 1, WIN_H), 2)

    y = 20

    # ── 유저 프로필 ──
    if user:
        y = _draw_user_profile(screen, user, y)
    else:
        # 비로그인 상태
        guest_s = _font("malgunGothic", 20).render("Guest", True, C_TEXT_DIM)
        screen.blit(guest_s, (20, y))
        y += 40

    # 구분선
    pygame.draw.line(screen, C_SIDEBAR_BORDER, (15, y), (SIDEBAR_W - 15, y), 1)
    y += 15

    # ── 플레이어 섹션 ──
    if players:
        header_s = _font("malgunGothic", 18).render("플레이어", True, C_TEXT_DIM)
        screen.blit(header_s, (15, y))
        y += 28

        for i, player in enumerate(players):
            active = (i == current_turn)
            y = _draw_player_card(screen, player, i, active, y)
            y += 8

    # ── 하단 툴바 ──
    _draw_bottom_toolbar(screen)


def _draw_user_profile(screen, user, y):
    """유저 아바타 + 이름 + 레벨."""
    # 아바타 원
    ar = 28
    acx, acy = 42, y + ar
    pygame.draw.circle(screen, C_ACCENT_BLUE, (acx, acy), ar)
    pygame.draw.circle(screen, (80, 170, 230), (acx, acy), ar, 2)

    # 간단한 이모지 얼굴
    eye_c = (35, 90, 160)
    pygame.draw.ellipse(screen, eye_c, (acx - 12, acy - 8, 8, 10))
    pygame.draw.ellipse(screen, eye_c, (acx + 4,  acy - 8, 8, 10))
    # 입 (웃는 호)
    pygame.draw.arc(screen, eye_c,
                    pygame.Rect(acx - 10, acy - 2, 20, 14), 3.4, 6.1, 2)

    # 이름
    nick = user.get("nickname", "Player") if isinstance(user, dict) else str(user)
    name_s = _font("malgunGothic", 22, bold=True).render(nick, True, C_TEXT)
    screen.blit(name_s, (acx + ar + 14, y + 4))

    # 랭크
    rank_s = _font("malgunGothic", 16).render("루키", True, C_TEXT_DIM)
    screen.blit(rank_s, (acx + ar + 14, y + 26))

    # 레벨 바
    bar_x = acx + ar + 14
    bar_y = y + 46
    bar_w = SIDEBAR_W - bar_x - 60
    bar_h = 6
    pygame.draw.rect(screen, (20, 25, 35), (bar_x, bar_y, bar_w, bar_h),
                     border_radius=3)
    pygame.draw.rect(screen, C_ACCENT_BLUE,
                     (bar_x, bar_y, int(bar_w * 0.3), bar_h), border_radius=3)

    lvl_s = _font("malgunGothic", 14).render("LVL 2", True, C_TEXT_DIM)
    screen.blit(lvl_s, (SIDEBAR_W - 52, y + 40))

    return y + 70


def _draw_player_card(screen, player, index, active, y):
    """사이드바 내 플레이어 카드."""
    card = pygame.Rect(10, y, SIDEBAR_W - 20, 52)

    # 배경 + 테두리
    bg = C_SIDEBAR_LIGHT if active else C_SIDEBAR_BG
    pygame.draw.rect(screen, bg, card, border_radius=8)
    border_c = C_GOLD if active else C_SIDEBAR_BORDER
    pygame.draw.rect(screen, border_c, card, 2, border_radius=8)

    # 아이콘
    icon_r = 16
    icon_cx = card.x + 26
    icon_cy = card.centery
    color = C_ACCENT_BLUE if index == 0 else (120, 125, 140)
    pygame.draw.circle(screen, color, (icon_cx, icon_cy), icon_r)
    # 간단한 눈
    ec = tuple(max(0, c - 50) for c in color)
    pygame.draw.circle(screen, ec, (icon_cx - 5, icon_cy - 3), 3)
    pygame.draw.circle(screen, ec, (icon_cx + 5, icon_cy - 3), 3)

    # 턴 표시 왕관
    if active:
        crown_s = _font("malgunGothic", 14).render("♛", True, C_GOLD)
        screen.blit(crown_s, (icon_cx - 5, icon_cy - icon_r - 12))

    # 이름
    name = player.name if hasattr(player, "name") else str(player)
    name_s = _font("malgunGothic", 18, bold=True).render(name, True, C_TEXT)
    screen.blit(name_s, (icon_cx + icon_r + 10, card.y + 8))

    # 그룹
    if hasattr(player, "group") and player.group:
        g_label = "● 솔리드 (1-7)" if player.group == "solid" else "◎ 스트라이프 (9-15)"
        g_s = _font("malgunGothic", 14).render(g_label, True, C_TEXT_DIM)
        screen.blit(g_s, (icon_cx + icon_r + 10, card.y + 28))

    return y + card.height


def _draw_bottom_toolbar(screen):
    """하단 아이콘 툴바."""
    ty = WIN_H - 48
    pygame.draw.line(screen, C_SIDEBAR_BORDER, (0, ty), (SIDEBAR_W, ty), 1)

    icons = ["🔊", "📋", "🎱", "⚙"]
    iw = SIDEBAR_W // len(icons)
    f = _font("segoeUIEmoji", 20)
    for i, icon in enumerate(icons):
        try:
            s = f.render(icon, True, C_TEXT_DIM)
            screen.blit(s, s.get_rect(centerx=i * iw + iw // 2, centery=ty + 24))
        except Exception:
            pass


# ── 볼 상태 바 ───────────────────────────────────────────

def draw_ball_status_bar(screen, balls, player1=None, player2=None):
    """테이블 위 볼 상태 표시 바."""
    bar_h = 46
    bar_y = TABLE_Y - bar_h - 8
    bar_x = TABLE_X
    bar_w = TABLE_W

    # 배경
    bg = pygame.Rect(bar_x, bar_y, bar_w, bar_h)
    pygame.draw.rect(screen, (30, 35, 48), bg, border_radius=10)
    pygame.draw.rect(screen, C_SIDEBAR_BORDER, bg, 1, border_radius=10)

    cx = bar_x + bar_w // 2
    cy = bar_y + bar_h // 2

    # 중앙: 큐볼
    pygame.draw.circle(screen, (240, 240, 240), (cx, cy), 15)
    pygame.draw.circle(screen, (200, 200, 200), (cx, cy), 15, 1)
    pygame.draw.circle(screen, (220, 50, 50), (cx + 2, cy - 2), 3)

    # 구분선
    pygame.draw.line(screen, C_SIDEBAR_BORDER,
                     (cx - 30, bar_y + 6), (cx - 30, bar_y + bar_h - 6), 1)
    pygame.draw.line(screen, C_SIDEBAR_BORDER,
                     (cx + 30, bar_y + 6), (cx + 30, bar_y + bar_h - 6), 1)

    pocketed_set = {b.number for b in balls if b.pocketed and b.number != 0}

    # 왼쪽: P1 그룹 공
    if player1 and hasattr(player1, "group") and player1.group:
        nums = list(range(1, 8)) if player1.group == "solid" else list(range(9, 16))
        _draw_ball_row(screen, nums, pocketed_set, cx - 50, cy, direction=-1)
        # P1 아바타
        _draw_tiny_avatar(screen, bar_x + 20, cy, C_ACCENT_BLUE)
    else:
        # 그룹 미배정 시 솔리드 전부
        _draw_ball_row(screen, list(range(1, 8)), pocketed_set, cx - 50, cy, direction=-1)

    # 오른쪽: P2 그룹 공
    if player2 and hasattr(player2, "group") and player2.group:
        nums = list(range(1, 8)) if player2.group == "solid" else list(range(9, 16))
        _draw_ball_row(screen, nums, pocketed_set, cx + 50, cy, direction=1)
        _draw_tiny_avatar(screen, bar_x + bar_w - 20, cy, (120, 125, 140))
    else:
        _draw_ball_row(screen, list(range(9, 16)), pocketed_set, cx + 50, cy, direction=1)


def _draw_ball_row(screen, nums, pocketed_set, start_x, cy, direction=1):
    """작은 공 아이콘 행."""
    r = 11
    spacing = 25
    for i, num in enumerate(nums):
        x = start_x + direction * i * spacing
        color = BALL_COLORS.get(num, (200, 200, 200))
        is_stripe = 9 <= num <= 15
        is_pocketed = num in pocketed_set

        if is_pocketed:
            # 포켓된 공: 어둡게
            pygame.draw.circle(screen, (45, 48, 58), (x, cy), r)
            pygame.draw.circle(screen, (55, 58, 68), (x, cy), r, 1)
            continue

        if is_stripe:
            pygame.draw.circle(screen, (240, 240, 240), (x, cy), r)
            band_rect = pygame.Rect(x - r, cy - 4, r * 2, 8)
            pygame.draw.rect(screen, color, band_rect)
        else:
            pygame.draw.circle(screen, color, (x, cy), r)

        # 번호
        f = _font("arial", 12, bold=True)
        tc = (20, 20, 20) if (is_stripe or num in (1, 9)) else (255, 255, 255)
        ns = f.render(str(num), True, tc)
        screen.blit(ns, ns.get_rect(center=(x, cy)))

        # 테두리
        pygame.draw.circle(screen, (80, 85, 95), (x, cy), r, 1)


def _draw_tiny_avatar(screen, cx, cy, color):
    """미니 아바타."""
    r = 15
    pygame.draw.circle(screen, color, (cx, cy), r)
    ec = tuple(max(0, c - 50) for c in color)
    pygame.draw.circle(screen, ec, (cx - 4, cy - 3), 2)
    pygame.draw.circle(screen, ec, (cx + 4, cy - 3), 2)


# ── 턴 표시 헤더 ─────────────────────────────────────────

def draw_turn_header(screen, text, highlight=True):
    """테이블 상단 턴 표시."""
    f = _font("malgunGothic", 20, bold=True)
    color = C_GOLD_LIGHT if highlight else C_TEXT_DIM
    ts = f.render(text, True, color)
    tx = TABLE_X + TABLE_W // 2
    ty = TABLE_Y - 80
    screen.blit(ts, ts.get_rect(centerx=tx, y=ty))


# ── 메뉴용 사이드바 ──────────────────────────────────────

def draw_menu_sidebar(screen, user=None):
    """메뉴 화면 전용 사이드바."""
    # 배경
    pygame.draw.rect(screen, C_SIDEBAR_BG, (0, 0, SIDEBAR_W, WIN_H))
    pygame.draw.line(screen, C_SIDEBAR_BORDER,
                     (SIDEBAR_W - 1, 0), (SIDEBAR_W - 1, WIN_H), 2)

    y = 25

    # 유저 프로필
    if user:
        y = _draw_user_profile(screen, user, y)
    else:
        ar = 28
        acx, acy = 42, y + ar
        pygame.draw.circle(screen, (80, 85, 100), (acx, acy), ar)
        pygame.draw.circle(screen, (100, 105, 120), (acx, acy), ar, 2)
        # ? 마크
        q = _font("malgunGothic", 28, bold=True).render("?", True, C_TEXT_DIM)
        screen.blit(q, q.get_rect(center=(acx, acy)))
        login_s = _font("malgunGothic", 20).render("로그인하기", True, C_TEXT_DIM)
        screen.blit(login_s, (acx + ar + 14, y + 12))
        y += 70

    # 구분선
    pygame.draw.line(screen, C_SIDEBAR_BORDER, (15, y), (SIDEBAR_W - 15, y), 1)
    y += 15

    # 빈 공간 (메뉴에서는 플레이어 목록 없음)

    # 하단 툴바
    _draw_bottom_toolbar(screen)

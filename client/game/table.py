"""
당구대 렌더링: 우드 레일, 펠트, 포켓, 공 그리기.
3D 구체 매핑으로 사실적인 공 회전 구현.
"""
import pygame
import pygame.gfxdraw
import numpy as np
import math
import random
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from config import (
    TABLE_X, TABLE_Y, TABLE_W, TABLE_H,
    CUSHION_SIZE, POCKETS, POCKET_RADIUS,
    BALL_COLORS, BALL_RADIUS,
    C_WOOD, C_WOOD_LIGHT, C_FELT, C_FELT_DARK, C_POCKET, C_WHITE,
    C_GOLD, C_GOLD_LIGHT,
)

# ── 3D 구체 매핑 공 렌더링 ───────────────────────────────
_SCALE = 4          # 하이라이트/그림자용 (기존)
_RS = 2             # 구체 렌더링 슈퍼샘플링 배율
_ball_highlight: pygame.Surface | None = None
_ball_shadow: pygame.Surface | None = None
_table_cache: pygame.Surface | None = None
_sphere_data = None
_num_font = None
_num_text_cache: dict[int, pygame.Surface] = {}


def _shade(base_color, factor):
    return (max(0, min(255, int(base_color[0] * factor))),
            max(0, min(255, int(base_color[1] * factor))),
            max(0, min(255, int(base_color[2] * factor))))


def _init_sphere():
    """구체 법선벡터, 셰이딩, 알파 마스크 사전 계산."""
    global _sphere_data
    if _sphere_data is not None:
        return
    r = BALL_RADIUS * _RS
    d = r * 2
    y_arr, x_arr = np.mgrid[0:d, 0:d]
    nx = (x_arr - r + 0.5) / r
    ny = (y_arr - r + 0.5) / r
    dist_sq = nx * nx + ny * ny
    mask = dist_sq < 1.0
    nz = np.where(mask, np.sqrt(np.maximum(0, 1.0 - dist_sq)), 0.0)
    normals_flat = np.stack([nx.ravel(), ny.ravel(), nz.ravel()], axis=1).astype(np.float64)

    # 고정 조명 셰이딩
    dist = np.sqrt(np.clip(dist_sq, 0, 1))
    fresnel = 1.0 - dist ** 3 * 0.6
    diffuse = np.maximum(0, -nx * 0.3 - ny * 0.5) * 0.45
    shade = np.clip(fresnel + diffuse, 0.35, 1.35)

    # 가장자리 안티앨리어싱 알파
    edge_dist = (1.0 - np.sqrt(np.clip(dist_sq, 0, 4))) * r
    alpha = np.zeros((d, d), dtype=np.uint8)
    alpha[mask] = np.clip(
        np.where(edge_dist[mask] < _RS, edge_dist[mask] / _RS * 255, 255),
        0, 255
    ).astype(np.uint8)

    _sphere_data = dict(
        r=r, d=d,
        normals_flat=normals_flat,
        mask=mask, shade=shade, alpha=alpha,
        final=BALL_RADIUS * 2,
    )


def _get_num_text(number):
    """숫자 텍스트 서피스 (캐시)."""
    global _num_font
    if _num_font is None:
        _num_font = pygame.font.SysFont("arial", max(10, BALL_RADIUS - 3) * _RS, bold=True)
    if number not in _num_text_cache:
        _num_text_cache[number] = _num_font.render(str(number), True, (20, 20, 20))
    return _num_text_cache[number]


def _render_ball_sphere(number, rot_x, rot_y, show_number=True, color_override=None):
    """3D 구체 매핑으로 공 렌더링 (numpy 벡터 연산)."""
    _init_sphere()
    sp = _sphere_data
    r, d = sp['r'], sp['d']
    mask = sp['mask']

    # 역회전 행렬: R_inv = (Ry · Rx)^T
    cx, sx = math.cos(rot_x), math.sin(rot_x)
    cy, sy = math.cos(rot_y), math.sin(rot_y)
    rot_inv = np.array([
        [cy,      0.0,   -sy],
        [sx*sy,   cx,     sx*cy],
        [cx*sy,  -sx,     cx*cy],
    ])

    # 뷰 법선 → 텍스처 좌표 변환
    tex = sp['normals_flat'] @ rot_inv.T
    tnz = tex[:, 2].reshape(d, d)
    tny = tex[:, 1].reshape(d, d)

    # 색상 결정
    if color_override is not None:
        color = np.array(color_override, dtype=np.float64)
    else:
        color = np.array(BALL_COLORS.get(number, (200, 200, 200)), dtype=np.float64)
    is_stripe = 9 <= number <= 15
    rgb = np.zeros((d, d, 3), dtype=np.float64)

    if number == 0:
        rgb[mask] = [248, 248, 248]
    elif is_stripe:
        stripe = mask & (np.abs(tnz) < 0.55)
        rgb[stripe] = color
        rgb[mask & ~stripe] = [240, 240, 240]
    else:
        rgb[mask] = color

    # 흰색 숫자 원 (북극 영역)
    if number != 0 and show_number:
        white_spot = mask & (tnz > 0.70)
        rgb[white_spot] = [255, 255, 255]

    # 셰이딩 적용
    shade = sp['shade']
    for c in range(3):
        rgb[:, :, c] *= shade
    np.clip(rgb, 0, 255, out=rgb)

    # pygame Surface 생성
    surf = pygame.Surface((d, d), pygame.SRCALPHA)
    px3 = pygame.surfarray.pixels3d(surf)
    px3[:] = rgb.astype(np.uint8).transpose(1, 0, 2)
    del px3
    pxa = pygame.surfarray.pixels_alpha(surf)
    pxa[:] = sp['alpha'].T
    del pxa

    # 숫자 텍스트 (보이는 면에만)
    if number != 0 and show_number:
        pole_x = cx * sy
        pole_y = -sx
        pole_z = cx * cy
        if pole_z > 0.15:
            px_x = int(r + pole_x * r * 0.82)
            px_y = int(r + pole_y * r * 0.82)
            ns = _get_num_text(number)
            surf.blit(ns, ns.get_rect(center=(px_x, px_y)))
            # 알파 마스크 재적용 (숫자가 공 밖으로 넘치지 않게)
            pxa2 = pygame.surfarray.pixels_alpha(surf)
            np.minimum(pxa2, sp['alpha'].T, out=pxa2)
            del pxa2

    pygame.gfxdraw.aacircle(surf, r, r, r - 1, (0, 0, 0, 40))
    return pygame.transform.smoothscale(surf, (sp['final'], sp['final']))


def _get_highlight() -> pygame.Surface:
    global _ball_highlight
    if _ball_highlight is None:
        r = BALL_RADIUS * _SCALE
        size = r * 2
        big = pygame.Surface((size, size), pygame.SRCALPHA)
        big.fill((0, 0, 0, 0))
        hl_cx = r - r // 3
        hl_cy = r - r // 3
        hl_r = max(r // 2, 5)
        for px in range(size):
            for py in range(size):
                d = math.hypot(px - hl_cx, py - hl_cy)
                if d < hl_r:
                    t = 1.0 - d / hl_r
                    a = int(200 * t * t * t)
                    big.set_at((px, py), (255, 255, 255, a))
        hl2_cx = hl_cx - r // 8
        hl2_cy = hl_cy - r // 8
        hl2_r = max(r // 5, 3)
        for px in range(max(0, hl2_cx - hl2_r), min(size, hl2_cx + hl2_r + 1)):
            for py in range(max(0, hl2_cy - hl2_r), min(size, hl2_cy + hl2_r + 1)):
                d = math.hypot(px - hl2_cx, py - hl2_cy)
                if d < hl2_r:
                    t = 1.0 - d / hl2_r
                    a = int(120 * t * t)
                    old = big.get_at((px, py))
                    new_a = min(255, old[3] + a)
                    big.set_at((px, py), (255, 255, 255, new_a))

        final = BALL_RADIUS * 2
        _ball_highlight = pygame.transform.smoothscale(big, (final, final))
    return _ball_highlight


def _get_shadow() -> pygame.Surface:
    global _ball_shadow
    if _ball_shadow is None:
        r = BALL_RADIUS * _SCALE
        pad = 5 * _SCALE
        w = (r + pad) * 2
        h = int((r + pad) * 1.6)
        big = pygame.Surface((w, h), pygame.SRCALPHA)
        big.fill((0, 0, 0, 0))
        cx, cy = w // 2 + 2 * _SCALE, h // 2 + 2 * _SCALE
        rx, ry = r + _SCALE, int(r * 0.7)
        for px in range(w):
            for py in range(h):
                dx = (px - cx) / rx
                dy = (py - cy) / ry
                d = math.sqrt(dx * dx + dy * dy)
                if d < 1.0:
                    a = int(50 * (1.0 - d) ** 1.2)
                    big.set_at((px, py), (0, 0, 0, a))
        fw = (BALL_RADIUS + 5) * 2
        fh = int((BALL_RADIUS + 5) * 1.6)
        _ball_shadow = pygame.transform.smoothscale(big, (fw, fh))
    return _ball_shadow


def get_ball_pattern(number: int) -> pygame.Surface:
    """(하위 호환용) HUD 등에서 사용할 수 있는 기본 공 패턴."""
    return _render_ball_sphere(number, 0.0, 0.0)


# ── 테이블 렌더링 (캐시) ───────────────────────────────────

def _draw_diamond(surf, cx, cy, size=5):
    points = [
        (cx, cy - size),
        (cx + size, cy),
        (cx, cy + size),
        (cx - size, cy),
    ]
    pygame.draw.polygon(surf, C_GOLD, points)
    pygame.draw.polygon(surf, C_GOLD_LIGHT, points, 1)


def _build_table_surface(width, height, pocketless=False) -> pygame.Surface:
    surf = pygame.Surface((width, height), pygame.SRCALPHA)
    surf.fill((0, 0, 0, 0))
    cs = CUSHION_SIZE

    # 우드 레일
    wood_rect = pygame.Rect(
        TABLE_X - cs, TABLE_Y - cs,
        TABLE_W + cs * 2, TABLE_H + cs * 2,
    )
    pygame.draw.rect(surf, (45, 24, 10), wood_rect, border_radius=16)
    inner1 = wood_rect.inflate(-4, -4)
    pygame.draw.rect(surf, C_WOOD, inner1, border_radius=14)
    inner2 = inner1.inflate(-4, -4)
    pygame.draw.rect(surf, C_WOOD_LIGHT, inner2, 2, border_radius=12)

    # 펠트
    felt_rect = pygame.Rect(TABLE_X, TABLE_Y, TABLE_W, TABLE_H)
    pygame.draw.rect(surf, C_FELT, felt_rect)

    # 펠트 텍스처
    for i in range(0, TABLE_H, 4):
        shade = 1.0 + math.sin(i * 0.05) * 0.015
        c = _shade(C_FELT, shade)
        pygame.draw.line(surf, c,
                         (TABLE_X, TABLE_Y + i),
                         (TABLE_X + TABLE_W, TABLE_Y + i), 1)

    # 쿠션 경사면
    cushion_dark = _shade(C_FELT, 0.7)
    pygame.draw.rect(surf, cushion_dark, (TABLE_X, TABLE_Y, TABLE_W, 3))
    pygame.draw.rect(surf, _shade(C_FELT, 1.15),
                     (TABLE_X, TABLE_Y + TABLE_H - 3, TABLE_W, 3))
    pygame.draw.rect(surf, cushion_dark, (TABLE_X, TABLE_Y, 3, TABLE_H))
    pygame.draw.rect(surf, _shade(C_FELT, 1.15),
                     (TABLE_X + TABLE_W - 3, TABLE_Y, 3, TABLE_H))

    # 중앙선
    mid_x = TABLE_X + TABLE_W // 2
    pygame.draw.line(surf, C_FELT_DARK,
                     (mid_x, TABLE_Y + 8), (mid_x, TABLE_Y + TABLE_H - 8), 1)

    # 헤드스팟 (안티앨리어싱)
    head_x = TABLE_X + TABLE_W // 4
    pygame.gfxdraw.aacircle(surf, head_x, TABLE_Y + TABLE_H // 2, 3, C_FELT_DARK)
    pygame.gfxdraw.filled_circle(surf, head_x, TABLE_Y + TABLE_H // 2, 3, C_FELT_DARK)

    # 다이아몬드 마커
    half_w = TABLE_W // 2
    rail_y_top = TABLE_Y - cs // 2
    rail_y_bot = TABLE_Y + TABLE_H + cs // 2
    for i in range(1, 4):
        fx  = TABLE_X + half_w * i / 4
        fx2 = TABLE_X + half_w + half_w * i / 4
        _draw_diamond(surf, int(fx),  rail_y_top)
        _draw_diamond(surf, int(fx2), rail_y_top)
        _draw_diamond(surf, int(fx),  rail_y_bot)
        _draw_diamond(surf, int(fx2), rail_y_bot)
    rail_x_left  = TABLE_X - cs // 2
    rail_x_right = TABLE_X + TABLE_W + cs // 2
    for i in range(1, 4):
        fy = TABLE_Y + TABLE_H * i / 4
        _draw_diamond(surf, rail_x_left, int(fy))
        _draw_diamond(surf, rail_x_right, int(fy))

    # 포켓 (안티앨리어싱) — 캐롬 모드에서는 생략
    if not pocketless:
        for px, py in POCKETS:
            pr = POCKET_RADIUS
            # 금색 장식 링 (포켓 테두리)
            pygame.gfxdraw.filled_circle(surf, px, py, pr + 10, (100, 70, 8))
            pygame.gfxdraw.filled_circle(surf, px, py, pr + 9, (160, 115, 10))
            pygame.gfxdraw.filled_circle(surf, px, py, pr + 8, C_GOLD_LIGHT)
            pygame.gfxdraw.aacircle(surf, px, py, pr + 10, (80, 55, 5))
            pygame.gfxdraw.aacircle(surf, px, py, pr + 7, (120, 85, 10))
            # 포켓 홀
            pygame.gfxdraw.aacircle(surf, px, py, pr + 6, (2, 2, 2))
            pygame.gfxdraw.filled_circle(surf, px, py, pr + 6, (2, 2, 2))
            for ri in range(pr + 4, 0, -1):
                t = ri / (pr + 4)
                c = int(8 * t)
                pygame.gfxdraw.aacircle(surf, px, py, ri, (c, c, c))
                pygame.gfxdraw.filled_circle(surf, px, py, ri, (c, c, c))
            pygame.gfxdraw.aacircle(surf, px, py, pr + 5, (30, 18, 8))
            pygame.gfxdraw.aacircle(surf, px, py, pr + 4, (30, 18, 8))

    return surf


_table_cache_carom: pygame.Surface | None = None

def draw_table(screen: pygame.Surface, pocketless=False):
    global _table_cache, _table_cache_carom
    from config import WIN_W, WIN_H
    if pocketless:
        if _table_cache_carom is None:
            _table_cache_carom = _build_table_surface(WIN_W, WIN_H, pocketless=True)
        screen.blit(_table_cache_carom, (0, 0))
    else:
        if _table_cache is None:
            _table_cache = _build_table_surface(WIN_W, WIN_H)
        screen.blit(_table_cache, (0, 0))


# ── 공 그리기 ──────────────────────────────────────────────

def draw_ball(screen: pygame.Surface, ball):
    """3D 구체 매핑 회전 + 그림자 + 하이라이트."""
    if ball.pocketed:
        return
    x, y = round(ball.x), round(ball.y)
    r = ball.radius

    # 그림자
    shadow = _get_shadow()
    sw, sh = shadow.get_size()
    screen.blit(shadow, (x - sw // 2, y - sh // 2 + 2))

    # 3D 구체 렌더링 (회전이 바뀔 때만 재렌더)
    rot_x = getattr(ball, 'rot_x', 0.0)
    rot_y = getattr(ball, 'rot_y', 0.0)
    show_num = getattr(ball, 'show_number', True)
    ball_color = getattr(ball, '_color', None)
    _Q = 0.04  # ~2.3도 단위 캐시
    cache_key = (ball.number, round(rot_x / _Q), round(rot_y / _Q), show_num, ball_color)
    if not hasattr(ball, '_surf_cache') or ball._surf_cache[0] != cache_key:
        ball._surf_cache = (cache_key, _render_ball_sphere(
            ball.number, rot_x, rot_y, show_number=show_num, color_override=ball_color))
    surf = ball._surf_cache[1]
    rect = surf.get_rect(center=(x, y))
    screen.blit(surf, rect)

    # 하이라이트
    screen.blit(_get_highlight(), (x - r, y - r))


def draw_balls(screen: pygame.Surface, balls):
    for b in balls:
        draw_ball(screen, b)


def draw_guide_line(screen: pygame.Surface, ball, angle_rad: float,
                    length: int = 600, other_balls=None):
    """가이드라인 + 충돌 시 큐볼/목적구 예측 방향."""
    if ball.pocketed:
        return
    x, y = ball.x, ball.y
    dx = math.cos(angle_rad)
    dy = math.sin(angle_rad)
    r = ball.radius

    # ── 충돌 감지: 가이드라인 위에서 가장 가까운 공 찾기 ──
    hit_ball = None
    hit_dist = length
    hit_cx, hit_cy = 0.0, 0.0

    if other_balls:
        for ob in other_balls:
            if ob.pocketed or ob.number == ball.number:
                continue
            # 큐볼 중심→목적구 중심 벡터
            ox = ob.x - x
            oy = ob.y - y
            # 가이드 방향에 대한 정사영
            proj = ox * dx + oy * dy
            if proj < r:
                continue  # 뒤쪽에 있는 공은 무시
            # 가이드 라인까지의 수직 거리
            perp = abs(ox * (-dy) + oy * dx)
            min_d = r + ob.radius
            if perp < min_d and proj < hit_dist:
                # 실제 접촉 지점 계산 (큐볼 중심이 닿는 위치)
                # 큐볼 중심에서 목적구 중심까지 거리에서 접촉 오프셋 뺀 값
                d_center = math.sqrt(ox * ox + oy * oy)
                # 정확한 접촉점: proj - sqrt(min_d^2 - perp^2)
                inside = min_d * min_d - perp * perp
                if inside > 0:
                    contact_dist = proj - math.sqrt(inside)
                    if contact_dist > r and contact_dist < hit_dist:
                        hit_dist = contact_dist
                        hit_ball = ob
                        hit_cx = x + dx * contact_dist
                        hit_cy = y + dy * contact_dist

    # ── 가이드라인 색상 ──
    #   흰공 경로:     흰색
    #   목적구 경로:   노란색
    #   흰공 반사:     하늘색
    COLOR_CUE_GUIDE = (255, 255, 255)       # 흰색
    COLOR_OBJ_GUIDE = (255, 210, 50)        # 노란색
    COLOR_CUE_REFLECT = (80, 200, 255)      # 하늘색

    # ── 큐볼 가이드라인 그리기 (충돌 지점까지) ──
    guide_end = hit_dist if hit_ball else length
    step = 12
    drawn = r + 4
    while drawn < guide_end:
        sx = x + dx * drawn
        sy = y + dy * drawn
        seg_end = min(drawn + 7, guide_end)
        ex = x + dx * seg_end
        ey = y + dy * seg_end
        t = drawn / length
        fade = max(0.35, 1.0 - t * 0.7)
        c = (max(60, int(COLOR_CUE_GUIDE[0] * fade)),
             max(60, int(COLOR_CUE_GUIDE[1] * fade)),
             max(60, int(COLOR_CUE_GUIDE[2] * fade)))
        pygame.draw.line(screen, c, (int(sx), int(sy)), (int(ex), int(ey)), 2)
        drawn += step

    if hit_ball:
        # ── 충돌 지점에 큐볼 고스트 원 (안티앨리어싱) ──
        ghost_x, ghost_y = int(hit_cx), int(hit_cy)
        pygame.gfxdraw.aacircle(screen, ghost_x, ghost_y, r, COLOR_CUE_GUIDE)

        # ── 목적구 진행 방향 (큐볼→목적구 법선) ──
        nx = hit_ball.x - hit_cx
        ny = hit_ball.y - hit_cy
        n_len = math.hypot(nx, ny)
        if n_len > 0.01:
            nx /= n_len
            ny /= n_len

            # 목적구 진행 방향선 (노란색)
            obj_len = 140
            obj_ex = hit_ball.x + nx * obj_len
            obj_ey = hit_ball.y + ny * obj_len
            _draw_predict_line(screen, hit_ball.x, hit_ball.y,
                               obj_ex, obj_ey, COLOR_OBJ_GUIDE, obj_len)

            # ── 큐볼 반사 방향 (하늘색) ──
            dot = dx * nx + dy * ny
            ref_dx = dx - dot * nx
            ref_dy = dy - dot * ny
            ref_len_v = math.hypot(ref_dx, ref_dy)
            if ref_len_v > 0.01:
                ref_dx /= ref_len_v
                ref_dy /= ref_len_v
                cue_len = 100
                cue_ex = hit_cx + ref_dx * cue_len
                cue_ey = hit_cy + ref_dy * cue_len
                _draw_predict_line(screen, hit_cx, hit_cy,
                                   cue_ex, cue_ey, COLOR_CUE_REFLECT, cue_len)

        # 충돌 지점 타겟 표시 (안티앨리어싱)
        pygame.gfxdraw.aacircle(screen, ghost_x, ghost_y, r + 2, COLOR_OBJ_GUIDE)
    else:
        # 충돌 없으면 끝에 타겟 원 표시 (안티앨리어싱)
        end_x = int(x + dx * length)
        end_y = int(y + dy * length)
        pygame.gfxdraw.aacircle(screen, end_x, end_y, r + 2, (180, 180, 180))
        cr = 5
        pygame.draw.aaline(screen, (160, 160, 160),
                           (end_x - cr, end_y), (end_x + cr, end_y))
        pygame.draw.aaline(screen, (160, 160, 160),
                           (end_x, end_y - cr), (end_x, end_y + cr))


def _draw_predict_line(screen, sx, sy, ex, ey, color, length):
    """예측 방향 점선 (페이드아웃, 색상 유지)."""
    dx = ex - sx
    dy = ey - sy
    d = math.hypot(dx, dy)
    if d < 1:
        return
    ux, uy = dx / d, dy / d
    step = 10
    drawn = 0
    while drawn < d:
        lsx = sx + ux * drawn
        lsy = sy + uy * drawn
        seg_end = min(drawn + 6, d)
        lex = sx + ux * seg_end
        ley = sy + uy * seg_end
        t = drawn / max(1, d)
        fade = max(0.3, 1.0 - t * 0.7)
        c = (max(40, int(color[0] * fade)),
             max(40, int(color[1] * fade)),
             max(40, int(color[2] * fade)))
        pygame.draw.line(screen, c, (int(lsx), int(lsy)), (int(lex), int(ley)), 2)
        drawn += step


# ── 포켓 폭죽 이펙트 ─────────────────────────────────────

class PocketEffects:
    """공이 포켓에 들어갈 때 폭죽 파티클 이펙트."""

    def __init__(self):
        self._particles: list[dict] = []

    def trigger(self, pocket_x: float, pocket_y: float, ball_color: tuple):
        """공이 포켓에 들어갈 때 호출."""
        for _ in range(35):
            angle = random.uniform(0, math.pi * 2)
            speed = random.uniform(80, 280)
            life = random.uniform(0.4, 1.0)
            # 70% 공 색상, 30% 금색/흰색 스파클
            if random.random() < 0.3:
                color = random.choice([
                    (255, 215, 0), (255, 255, 200), (255, 180, 50),
                ])
            else:
                color = ball_color
            self._particles.append({
                'x': float(pocket_x),
                'y': float(pocket_y),
                'vx': math.cos(angle) * speed,
                'vy': math.sin(angle) * speed - random.uniform(20, 60),
                'color': color,
                'life': life,
                'max_life': life,
                'size': random.uniform(2, 6),
            })
        # 큰 중앙 플래시
        self._particles.append({
            'x': float(pocket_x),
            'y': float(pocket_y),
            'vx': 0.0, 'vy': 0.0,
            'color': (255, 255, 220),
            'life': 0.2,
            'max_life': 0.2,
            'size': float(POCKET_RADIUS),
        })

    def update(self, dt: float):
        for p in self._particles:
            p['x'] += p['vx'] * dt
            p['y'] += p['vy'] * dt
            p['vy'] += 300 * dt   # 중력
            p['vx'] *= 0.97       # 공기 저항
            p['life'] -= dt
        self._particles = [p for p in self._particles if p['life'] > 0]

    def draw(self, screen: pygame.Surface):
        for p in self._particles:
            t = max(0.0, p['life'] / p['max_life'])
            size = max(1, int(p['size'] * t))
            r = min(255, int(p['color'][0] * t))
            g = min(255, int(p['color'][1] * t))
            b = min(255, int(p['color'][2] * t))
            ix, iy = int(p['x']), int(p['y'])
            if size > 2:
                pygame.gfxdraw.filled_circle(screen, ix, iy, size, (r, g, b))
                pygame.gfxdraw.aacircle(screen, ix, iy, size, (r, g, b))
            else:
                pygame.draw.circle(screen, (r, g, b), (ix, iy), size)

    @property
    def active(self):
        return len(self._particles) > 0

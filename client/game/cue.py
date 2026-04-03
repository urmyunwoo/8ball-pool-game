"""
큐대 렌더링, 조준, 스핀 컨트롤.
power 값은 GameScene에서 외부로 관리하고 draw/get_velocity에 인자로 전달한다.
"""
import pygame
import pygame.gfxdraw
import math
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from config import (
    C_GOLD, C_GOLD_LIGHT, MAX_POWER, BALL_RADIUS,
    WIN_W, TABLE_X, TABLE_W, TABLE_Y,
)


class Cue:
    CUE_LENGTH = 280
    SPIN_STEP  = 0.15
    SPIN_MAX   = 0.85
    INDICATOR_R = 28

    SMOOTH_SPEED = 0.35   # 각도 보간 비율 (0~1, 1이면 즉시)
    MAX_ANGLE_SPEED = 0.5  # 프레임당 최대 회전량(rad)

    def __init__(self):
        self.angle = 0.0
        self._target_angle = 0.0
        self.spin_x = 0.0
        self.spin_y = 0.0
        self._spin_dragging = False  # 스핀 인디케이터 드래그 중

    def reset_spin(self):
        self.spin_x = 0.0
        self.spin_y = 0.0

    @property
    def _indicator_pos(self) -> tuple[int, int]:
        """스핀 인디케이터 중심 좌표."""
        ir = self.INDICATOR_R
        ix = TABLE_X + TABLE_W - ir - 10
        iy = TABLE_Y - ir - 16
        return ix, iy

    def handle_spin_mouse(self, event) -> bool:
        """
        스핀 인디케이터의 마우스 이벤트 처리.
        처리했으면 True를 반환.
        """
        ix, iy = self._indicator_pos
        ir = self.INDICATOR_R

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos
            if math.hypot(mx - ix, my - iy) <= ir + 6:
                self._spin_dragging = True
                self._set_spin_from_mouse(mx, my, ix, iy, ir)
                return True

        elif event.type == pygame.MOUSEMOTION and self._spin_dragging:
            mx, my = event.pos
            self._set_spin_from_mouse(mx, my, ix, iy, ir)
            return True

        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if self._spin_dragging:
                self._spin_dragging = False
                return True

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:
            mx, my = event.pos
            if math.hypot(mx - ix, my - iy) <= ir + 6:
                self.reset_spin()
                return True

        return False

    def _set_spin_from_mouse(self, mx, my, ix, iy, ir):
        """마우스 위치를 스핀 값으로 변환."""
        dx = (mx - ix) / max(1, ir - 5)
        dy = (my - iy) / max(1, ir - 5)
        dist = math.hypot(dx, dy)
        if dist > self.SPIN_MAX:
            scale = self.SPIN_MAX / dist
            dx *= scale
            dy *= scale
        self.spin_x = dx
        self.spin_y = dy

    @property
    def shot_angle(self) -> float:
        return self.angle + math.pi

    def handle_spin_key(self, key):
        if key == pygame.K_LEFT:
            self.spin_x = max(-self.SPIN_MAX, self.spin_x - self.SPIN_STEP)
            return True
        elif key == pygame.K_RIGHT:
            self.spin_x = min(self.SPIN_MAX, self.spin_x + self.SPIN_STEP)
            return True
        elif key == pygame.K_UP:
            self.spin_y = max(-self.SPIN_MAX, self.spin_y - self.SPIN_STEP)
            return True
        elif key == pygame.K_DOWN:
            self.spin_y = min(self.SPIN_MAX, self.spin_y + self.SPIN_STEP)
            return True
        return False

    def update_angle(self, cue_ball, mouse_pos: tuple[int, int]):
        dx = mouse_pos[0] - cue_ball.x
        dy = mouse_pos[1] - cue_ball.y
        self._target_angle = math.atan2(dy, dx)

        # 각도 차이를 -π ~ π 범위로 정규화
        diff = self._target_angle - self.angle
        while diff > math.pi:
            diff -= 2 * math.pi
        while diff < -math.pi:
            diff += 2 * math.pi

        # 보간 값 계산 후 최대 회전 속도로 클램프
        step = diff * self.SMOOTH_SPEED
        if abs(step) > self.MAX_ANGLE_SPEED:
            step = math.copysign(self.MAX_ANGLE_SPEED, step)
        self.angle += step

    def get_velocity(self, power: float) -> tuple[float, float]:
        # 비선형 파워 커브: 저파워는 살짝만, 고파워(70%+)는 확 세게
        adjusted = power + 0.45 * power ** 3
        speed = adjusted * MAX_POWER
        a = self.shot_angle
        return math.cos(a) * speed, math.sin(a) * speed

    def draw(self, screen: pygame.Surface, cue_ball, power: float = 0.0):
        if cue_ball.pocketed:
            return
        cx, cy = int(cue_ball.x), int(cue_ball.y)
        r = BALL_RADIUS

        gap     = r + 5 + int(power * 45)
        start_d = gap
        end_d   = gap + self.CUE_LENGTH

        ax = math.cos(self.angle)
        ay = math.sin(self.angle)
        sx = cx + int(ax * start_d)
        sy = cy + int(ay * start_d)
        ex = cx + int(ax * end_d)
        ey = cy + int(ay * end_d)

        # 큐대 렌더링 (안티앨리어싱 테이퍼드 폴리곤)
        line_dx = ex - sx
        line_dy = ey - sy
        line_len = math.hypot(line_dx, line_dy)
        if line_len > 0.1:
            # 수직 벡터
            perp_x = -line_dy / line_len
            perp_y = line_dx / line_len

            tip_hw = 1.8     # 팁(공 쪽) 반폭
            butt_hw = 4.5    # 버트(손잡이 쪽) 반폭

            # 팁 부분 (밝은 색) → 버트 부분 (어두운 색)
            # 4개 꼭짓점으로 테이퍼드 형태
            pts = [
                (int(sx + perp_x * tip_hw),  int(sy + perp_y * tip_hw)),
                (int(sx - perp_x * tip_hw),  int(sy - perp_y * tip_hw)),
                (int(ex - perp_x * butt_hw), int(ey - perp_y * butt_hw)),
                (int(ex + perp_x * butt_hw), int(ey + perp_y * butt_hw)),
            ]

            # 메인 바디 (나무색)
            body_col = (190, 140, 55)
            pygame.gfxdraw.filled_polygon(screen, pts, body_col)
            pygame.gfxdraw.aapolygon(screen, pts, body_col)

            # 팁 하이라이트 (밝은 선)
            mid_len = line_len * 0.08  # 팁 끝 8%
            mx1 = sx + line_dx / line_len * mid_len
            my1 = sy + line_dy / line_len * mid_len
            tip_pts = [
                (int(sx + perp_x * tip_hw), int(sy + perp_y * tip_hw)),
                (int(sx - perp_x * tip_hw), int(sy - perp_y * tip_hw)),
                (int(mx1 - perp_x * (tip_hw + 0.3)), int(my1 - perp_y * (tip_hw + 0.3))),
                (int(mx1 + perp_x * (tip_hw + 0.3)), int(my1 + perp_y * (tip_hw + 0.3))),
            ]
            tip_col = (220, 210, 190)
            pygame.gfxdraw.filled_polygon(screen, tip_pts, tip_col)
            pygame.gfxdraw.aapolygon(screen, tip_pts, tip_col)

            # 버트 끝 장식 (어두운 부분)
            butt_start = line_len * 0.75
            bx1 = sx + line_dx / line_len * butt_start
            by1 = sy + line_dy / line_len * butt_start
            hw_at = tip_hw + (butt_hw - tip_hw) * 0.75
            butt_pts = [
                (int(bx1 + perp_x * hw_at),  int(by1 + perp_y * hw_at)),
                (int(bx1 - perp_x * hw_at),  int(by1 - perp_y * hw_at)),
                (int(ex - perp_x * butt_hw),  int(ey - perp_y * butt_hw)),
                (int(ex + perp_x * butt_hw),  int(ey + perp_y * butt_hw)),
            ]
            butt_col = (120, 70, 30)
            pygame.gfxdraw.filled_polygon(screen, butt_pts, butt_col)
            pygame.gfxdraw.aapolygon(screen, butt_pts, butt_col)

        # ── 줄무늬 파워 바 ──
        if power > 0.01:
            bw, bh = 130, 14
            bx = cx - bw // 2
            by = cy - r - 38

            # 배경
            pygame.draw.rect(screen, (30, 30, 30),
                             (bx - 2, by - 2, bw + 4, bh + 4), border_radius=4)

            fill_w = max(1, int(bw * power))

            # 줄무늬 패턴
            stripe_w = 8
            for i in range(0, fill_w, stripe_w):
                sw = min(stripe_w // 2, fill_w - i)
                if sw <= 0:
                    break
                t = i / max(1, bw)
                # 주황 → 빨강 그라디언트
                r_v = min(255, int(230 + 25 * t))
                g_v = max(20, int(160 - 140 * t))
                b_v = 20
                pygame.draw.rect(screen, (r_v, g_v, b_v),
                                 (bx + i, by, sw, bh), border_radius=2)
                # 빈 스트라이프 (어두운)
                if i + stripe_w // 2 < fill_w:
                    dw = min(stripe_w // 2, fill_w - i - stripe_w // 2)
                    if dw > 0:
                        pygame.draw.rect(screen, (r_v // 2, g_v // 2, 10),
                                         (bx + i + stripe_w // 2, by, dw, bh),
                                         border_radius=2)

            # 테두리
            pygame.draw.rect(screen, C_GOLD_LIGHT,
                             (bx - 2, by - 2, bw + 4, bh + 4), 1, border_radius=4)

    def draw_spin_indicator(self, screen: pygame.Surface):
        ir = self.INDICATOR_R
        ix, iy = self._indicator_pos

        # 드래그 중 강조 효과
        if self._spin_dragging:
            pygame.gfxdraw.aacircle(screen, ix, iy, ir + 8, (100, 160, 220, 80))
            pygame.gfxdraw.filled_circle(screen, ix, iy, ir + 8, (60, 120, 200, 40))

        # 배경 원 (안티앨리어싱)
        pygame.gfxdraw.aacircle(screen, ix, iy, ir + 4, (60, 60, 60))
        pygame.gfxdraw.filled_circle(screen, ix, iy, ir + 4, (60, 60, 60))
        pygame.gfxdraw.aacircle(screen, ix, iy, ir, (230, 230, 230))
        pygame.gfxdraw.filled_circle(screen, ix, iy, ir, (230, 230, 230))
        pygame.draw.aaline(screen, (180, 180, 180),
                           (ix - ir + 4, iy), (ix + ir - 4, iy))
        pygame.draw.aaline(screen, (180, 180, 180),
                           (ix, iy - ir + 4), (ix, iy + ir - 4))
        pygame.gfxdraw.aacircle(screen, ix, iy, ir, (100, 100, 100))

        # 타격점 (안티앨리어싱)
        dot_x = ix + int(self.spin_x * (ir - 5))
        dot_y = iy + int(self.spin_y * (ir - 5))
        pygame.gfxdraw.aacircle(screen, dot_x, dot_y, 5, (220, 40, 40))
        pygame.gfxdraw.filled_circle(screen, dot_x, dot_y, 5, (220, 40, 40))
        pygame.gfxdraw.aacircle(screen, dot_x, dot_y, 3, (255, 80, 80))
        pygame.gfxdraw.filled_circle(screen, dot_x, dot_y, 3, (255, 80, 80))

        # 스핀 라벨 + 효과 설명
        font = pygame.font.SysFont("malgunGothic", 14)
        spin_mag = math.hypot(self.spin_x, self.spin_y)
        if spin_mag > 0.1:
            # 스핀 종류 표시
            label_text = self._get_spin_label()
            label_color = (255, 180, 50)
        else:
            label_text = "클릭/드래그로 스핀"
            label_color = (160, 160, 160)
        label = font.render(label_text, True, label_color)
        screen.blit(label, label.get_rect(centerx=ix, top=iy + ir + 8))

        # 우클릭 리셋 힌트 (스핀이 있을 때만)
        if spin_mag > 0.1:
            hint_font = pygame.font.SysFont("malgunGothic", 12)
            hint = hint_font.render("우클릭: 리셋", True, (120, 120, 120))
            screen.blit(hint, hint.get_rect(centerx=ix, top=iy + ir + 22))

    def _get_spin_label(self) -> str:
        """현재 스핀 방향에 따른 라벨."""
        labels = []
        if self.spin_y < -0.15:
            labels.append("밀어치기")
        elif self.spin_y > 0.15:
            labels.append("끌어치기")
        if abs(self.spin_x) > 0.15:
            side = "우" if self.spin_x > 0 else "좌"
            labels.append(f"{side}회전")
        return " + ".join(labels) if labels else "스핀"

"""
캐롬 당구 (3구 / 4구) 게임 씬.
"""
import pygame
import math
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from config import (
    WIN_W, WIN_H, C_BG, C_GOLD, C_GOLD_LIGHT, C_TEXT, C_TEXT_DIM,
    TABLE_X, TABLE_Y, TABLE_W, TABLE_H, BALL_RADIUS, SIDEBAR_W,
    C_SIDEBAR_BG, C_SIDEBAR_BORDER, C_RED,
)
from scenes.base_scene import BaseScene
from game.physics import Ball, Physics
from game.table import draw_table, draw_balls, draw_guide_line
from game.cue import Cue
from game.carom_logic import CaromLogic, CaromResult
from game.sound import play, play_impact
from ui.button import Button
from ui.dialog import Dialog


class CaromGameScene(BaseScene):

    STATE_WAITING = "waiting"
    STATE_MOVING  = "moving"
    STATE_OVER    = "over"

    def on_enter(self, **kwargs):
        mode = kwargs.get("mode", "4ball")
        p1 = kwargs.get("player1", "플레이어 1")
        p2 = kwargs.get("player2", "플레이어 2")
        self._init_game(mode, p1, p2)

    def _init_game(self, mode: str, p1: str, p2: str):
        self._mode   = mode
        self.logic   = CaromLogic(mode, p1, p2)
        self.physics = Physics(has_pockets=False)
        self.cue     = Cue()
        self.balls   = self._build_balls()
        self.state   = self.STATE_WAITING

        self._power    = 0.0
        self._charging = False
        self._charge_start = (0, 0)

        mode_name = "쓰리쿠션 (3구)" if mode == "3cushion" else "4구"
        self._result_dialog = Dialog("", "", ["새 게임", "메뉴로"])
        self._font_msg  = pygame.font.SysFont("malgunGothic", 20)
        self._font_hud  = pygame.font.SysFont("malgunGothic", 19, bold=True)
        self._font_big  = pygame.font.SysFont("malgunGothic", 28, bold=True)
        self._font_score = pygame.font.SysFont("impact", 56, bold=True)

        self._leave_btn = Button(
            (15, WIN_H - 100, SIDEBAR_W - 30, 36),
            "← 메뉴로 나가기", 18,
            color=C_RED, text_color=(255, 255, 255),
        )
        self._msg_timer = 0.0

    def _build_balls(self) -> list[Ball]:
        balls = []
        cx = TABLE_X + TABLE_W // 2
        cy = TABLE_Y + TABLE_H // 2

        # 흰공 (P1)
        white = Ball(0, TABLE_X + TABLE_W * 0.25, cy)
        white.show_number = False
        balls.append(white)

        # 노란공 (P2)
        yellow = Ball(1, TABLE_X + TABLE_W * 0.75, cy)
        yellow.show_number = False
        balls.append(yellow)

        # 빨간공 1
        red1 = Ball(2, cx, cy - 50)
        red1.show_number = False
        red1._color = (210, 30, 30)
        balls.append(red1)

        if self._mode == "4ball":
            # 빨간공 2
            red2 = Ball(3, cx, cy + 50)
            red2.show_number = False
            red2._color = (210, 30, 30)
            balls.append(red2)

        return balls

    @property
    def _cue_ball(self) -> Ball:
        cue_num = self.logic.current_cue
        return next(b for b in self.balls if b.number == cue_num)

    # ── Event ───────────────────────────────────────────

    def handle_event(self, event: pygame.event.Event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            if self._charging:
                self._charging = False
                self._power    = 0.0
            return

        if self._result_dialog.visible:
            r = self._result_dialog.handle_event(event)
            if r == "새 게임":
                p1, p2 = self.logic.names
                self._init_game(self._mode, p1, p2)
            elif r == "메뉴로":
                self.manager.switch("menu")
            return

        if self._leave_btn.handle_event(event):
            self.manager.switch("menu")
            return

        if self.state == self.STATE_WAITING:
            # 스핀 마우스 컨트롤 우선
            if self.cue.handle_spin_mouse(event):
                return

            if event.type == pygame.KEYDOWN:
                self.cue.handle_spin_key(event.key)

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if TABLE_X <= event.pos[0] <= TABLE_X + TABLE_W and \
                   TABLE_Y <= event.pos[1] <= TABLE_Y + TABLE_H:
                    self._charging = True
                    self._charge_start = event.pos
                    self._power = 0.0

            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                if self._charging and self._power > 0.02:
                    self._shoot()
                self._charging = False

    def _shoot(self):
        cb = self._cue_ball
        vx, vy = self.cue.get_velocity(self._power)
        cb.vx = vx
        cb.vy = vy
        cb.spin_x = self.cue.spin_x
        cb.spin_y = self.cue.spin_y
        cb.spin_power = math.hypot(self.cue.spin_x, self.cue.spin_y)
        cb.shot_dir_x = math.cos(self.cue.shot_angle)
        cb.shot_dir_y = math.sin(self.cue.shot_angle)
        self.cue.reset_spin()

        self.physics.start_shot(cb.number)
        self.state   = self.STATE_MOVING
        self._power  = 0.0
        play("cue_shoot")

    # ── Update ──────────────────────────────────────────

    def update(self, dt: float):
        mouse = self.manager.get_mouse_pos()

        if self.state == self.STATE_WAITING:
            cb = self._cue_ball
            if not self._charging:
                self.cue.update_angle(cb, mouse)
            if self._charging:
                dx = mouse[0] - self._charge_start[0]
                dy = mouse[1] - self._charge_start[1]
                dist = math.hypot(dx, dy)
                self._power = min(1.0, dist / 120.0)

        elif self.state == self.STATE_MOVING:
            self.physics.step(self.balls, dt)

            # ASMR 충돌 사운드
            for evt in self.physics.collision_events:
                play_impact(evt.kind, evt.speed)

            if not self.physics.any_moving(self.balls):
                self._process_turn_end()

        if self._msg_timer > 0:
            self._msg_timer -= dt

    def _process_turn_end(self):
        result = self.logic.on_shot_end(
            self.physics.cushion_hits,
            self.physics.ball_contacts,
        )
        self._msg_timer = 3.0

        if result == CaromResult.WIN:
            self.state = self.STATE_OVER
            winner = self.logic.current_name
            self._result_dialog.title = "게임 종료!"
            self._result_dialog.message = f"{winner} 승리!"
            self._result_dialog.show()
            play("win")
        else:
            self.state = self.STATE_WAITING

    # ── Draw ────────────────────────────────────────────

    def draw(self, screen: pygame.Surface):
        screen.fill(C_BG)

        # 사이드바
        self._draw_sidebar(screen)
        self._leave_btn.draw(screen)

        # 턴 헤더
        mode_label = "쓰리쿠션 (3구)" if self._mode == "3cushion" else "4구"
        header = f"{mode_label}  |  {self.logic.current_name}의 차례"
        if self.state == self.STATE_MOVING:
            header = f"{mode_label}  |  공이 이동 중..."
        hs = self._font_big.render(header, True, C_GOLD_LIGHT)
        screen.blit(hs, hs.get_rect(
            centerx=TABLE_X + TABLE_W // 2, y=TABLE_Y - 50))

        # 테이블 (포켓 없음)
        draw_table(screen, pocketless=True)

        cb = self._cue_ball

        # 가이드라인 + 큐대
        if self.state == self.STATE_WAITING:
            draw_guide_line(screen, cb, self.cue.shot_angle,
                            other_balls=self.balls)
            self.cue.draw(screen, cb, self._power)
            self.cue.draw_spin_indicator(screen)

        draw_balls(screen, self.balls)

        # 쿠션 카운터 (3구 모드, 이동 중)
        if self._mode == "3cushion" and self.state == self.STATE_MOVING:
            ch = self.physics.cushion_hits
            bc = len(self.physics.ball_contacts)
            info = f"쿠션: {ch}  |  접촉: {bc}"
            cs = self._font_msg.render(info, True, C_GOLD_LIGHT)
            bg = pygame.Surface((cs.get_width() + 16, cs.get_height() + 8), pygame.SRCALPHA)
            bg.fill((0, 0, 0, 160))
            ix = TABLE_X + TABLE_W // 2
            iy = TABLE_Y + TABLE_H + 28
            screen.blit(bg, bg.get_rect(centerx=ix, centery=iy))
            screen.blit(cs, cs.get_rect(centerx=ix, centery=iy))

        # 메시지
        if self._msg_timer > 0 and self.logic.message:
            ms = self._font_msg.render(self.logic.message, True, C_GOLD_LIGHT)
            bg = pygame.Surface((ms.get_width() + 20, ms.get_height() + 10), pygame.SRCALPHA)
            bg.fill((0, 0, 0, 160))
            mcx = TABLE_X + TABLE_W // 2
            mcy = TABLE_Y + TABLE_H + 50
            screen.blit(bg, bg.get_rect(centerx=mcx, centery=mcy))
            screen.blit(ms, ms.get_rect(centerx=mcx, centery=mcy))

        self._result_dialog.draw(screen)

    def _draw_sidebar(self, screen):
        """점수판 사이드바."""
        sb = pygame.Rect(0, 0, SIDEBAR_W, WIN_H)
        pygame.draw.rect(screen, C_SIDEBAR_BG, sb)
        pygame.draw.line(screen, C_SIDEBAR_BORDER,
                         (SIDEBAR_W, 0), (SIDEBAR_W, WIN_H), 2)

        mode_label = "쓰리쿠션" if self._mode == "3cushion" else "4구 당구"
        ts = self._font_big.render(mode_label, True, C_GOLD_LIGHT)
        screen.blit(ts, ts.get_rect(centerx=SIDEBAR_W // 2, y=30))

        target = self._font_hud.render(
            f"목표: {self.logic.target_score}점", True, C_TEXT_DIM)
        screen.blit(target, target.get_rect(centerx=SIDEBAR_W // 2, y=70))

        # 플레이어 점수 카드
        for i in range(2):
            y_base = 130 + i * 260
            is_current = (i == self.logic.current and self.state != self.STATE_OVER)

            # 카드 배경
            card = pygame.Rect(15, y_base, SIDEBAR_W - 30, 230)
            card_color = (40, 50, 65) if is_current else (30, 35, 48)
            pygame.draw.rect(screen, card_color, card, border_radius=12)
            if is_current:
                pygame.draw.rect(screen, C_GOLD, card, 2, border_radius=12)

            # 공 색상 표시
            ball_color = (248, 248, 248) if i == 0 else (240, 210, 0)
            pygame.draw.circle(screen, ball_color,
                               (card.centerx, y_base + 40), 18)
            if is_current:
                pygame.draw.circle(screen, C_GOLD,
                                   (card.centerx, y_base + 40), 22, 2)

            # 이름
            ns = self._font_hud.render(self.logic.names[i], True, C_TEXT)
            screen.blit(ns, ns.get_rect(centerx=card.centerx, y=y_base + 68))

            # 점수
            score_s = self._font_score.render(
                str(self.logic.scores[i]), True, C_GOLD_LIGHT)
            screen.blit(score_s, score_s.get_rect(
                centerx=card.centerx, y=y_base + 100))

            # 진행률 바
            bar_x = card.x + 20
            bar_y = y_base + 175
            bar_w = card.width - 40
            bar_h = 12
            pygame.draw.rect(screen, (20, 25, 35),
                             (bar_x, bar_y, bar_w, bar_h), border_radius=6)
            fill = max(1, int(bar_w * self.logic.scores[i] / self.logic.target_score))
            fill_color = (50, 180, 80) if is_current else (80, 120, 160)
            pygame.draw.rect(screen, fill_color,
                             (bar_x, bar_y, fill, bar_h), border_radius=6)

            # 분수 표시
            frac = self._font_hud.render(
                f"{self.logic.scores[i]} / {self.logic.target_score}",
                True, C_TEXT_DIM)
            screen.blit(frac, frac.get_rect(
                centerx=card.centerx, y=y_base + 196))

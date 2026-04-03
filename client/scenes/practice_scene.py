"""
혼자 연습 씬 — 규칙 없이 공을 자유롭게 침.
사이드바 포함. 스핀 마우스 컨트롤 + ASMR 사운드 + 리플레이.
"""
import pygame
import math
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from config import (
    WIN_W, WIN_H, C_BG, C_GOLD, C_GOLD_LIGHT, C_TEXT, C_TEXT_DIM,
    TABLE_X, TABLE_Y, TABLE_W, TABLE_H, BALL_RADIUS, SIDEBAR_W,
    C_SIDEBAR_BG, C_SIDEBAR_BORDER, C_RED, BALL_COLORS,
)
from scenes.base_scene import BaseScene
from game.physics  import Ball, Physics
from game.table    import draw_table, draw_balls, draw_ball, draw_guide_line, PocketEffects
from game.cue      import Cue
from game.game_logic import GameLogic
from game.sound    import play, play_impact
from game.replay   import ReplayRecorder, ReplayPlayer, should_replay
from ui.button     import Button
from ui.game_hud   import draw_sidebar, draw_turn_header


class PracticeScene(BaseScene):

    def on_enter(self, **kwargs):
        self.physics = Physics()
        self.cue     = Cue()
        self.balls   = self._build_balls()
        self._power   = 0.0
        self._charging = False
        self._charge_start = (0, 0)
        self._moving   = False
        self._pocketed_count = 0
        self._shot_pocketed  = 0  # 이번 샷에서 넣은 공
        self._effects = PocketEffects()
        self._font = pygame.font.SysFont("malgunGothic", 22)

        # 리플레이
        self._recorder = ReplayRecorder()
        self._replay   = ReplayPlayer()

        self._leave_btn = Button(
            (15, WIN_H - 100, SIDEBAR_W - 30, 36),
            "← 메뉴로", 18,
            color=C_RED, text_color=(255, 255, 255),
        )
        self._reset_btn = Button(
            (15, WIN_H - 150, SIDEBAR_W - 30, 36),
            "리셋", 18,
        )

    def _build_balls(self) -> list[Ball]:
        balls = [Ball(0, GameLogic.CUE_START_X, GameLogic.CUE_START_Y)]
        for num, x, y in GameLogic("", "").rack_positions():
            balls.append(Ball(num, x, y))
        return balls

    @property
    def _cue_ball(self) -> Ball:
        return next(b for b in self.balls if b.number == 0)

    def handle_event(self, event: pygame.event.Event):
        # 리플레이 중에는 스페이스로 건너뛰기만 허용
        if self._replay.active:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                self._replay.skip()
            return

        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            if self._charging:
                self._charging = False
                self._power    = 0.0
            return

        if self._leave_btn.handle_event(event):
            self.manager.switch("menu")
        if self._reset_btn.handle_event(event):
            self.on_enter()

        if self._moving:
            return

        # 스핀 마우스 컨트롤 (키보드보다 우선)
        if self.cue.handle_spin_mouse(event):
            return

        if event.type == pygame.KEYDOWN:
            self.cue.handle_spin_key(event.key)

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            margin = 60
            if TABLE_X - margin <= event.pos[0] <= TABLE_X + TABLE_W + margin and \
               TABLE_Y - margin <= event.pos[1] <= TABLE_Y + TABLE_H + margin:
                self._charging = True
                self._charge_start = event.pos
                self._power    = 0.0

        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if self._charging and self._power > 0.02:
                cb = self._cue_ball
                if not cb.pocketed:
                    vx, vy = self.cue.get_velocity(self._power)
                    cb.vx, cb.vy = vx, vy
                    cb.spin_x = self.cue.spin_x
                    cb.spin_y = self.cue.spin_y
                    cb.spin_power = math.hypot(self.cue.spin_x, self.cue.spin_y)
                    cb.shot_dir_x = math.cos(self.cue.shot_angle)
                    cb.shot_dir_y = math.sin(self.cue.shot_angle)
                    self.cue.reset_spin()
                    self._moving = True
                    self._shot_pocketed = 0
                    self._recorder.start(self.balls)
                    play("cue_shoot")
            self._charging = False
            self._power    = 0.0

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:
            cb = self._cue_ball
            if cb.pocketed:
                mx, my = event.pos
                if TABLE_X + BALL_RADIUS < mx < TABLE_X + TABLE_W - BALL_RADIUS:
                    if TABLE_Y + BALL_RADIUS < my < TABLE_Y + TABLE_H - BALL_RADIUS:
                        cb.place(mx, my)

    def update(self, dt: float):
        # 리플레이 재생 중
        if self._replay.active:
            self._replay.update(dt)
            return

        mouse = self.manager.get_mouse_pos()
        cb    = self._cue_ball

        if not self._moving:
            if not cb.pocketed and not self._charging:
                self.cue.update_angle(cb, mouse)
            if self._charging:
                dx = mouse[0] - self._charge_start[0]
                dy = mouse[1] - self._charge_start[1]
                dist = math.hypot(dx, dy)
                self._power = min(1.0, dist / 120.0)
        else:
            pocketed = self.physics.step(self.balls, dt)
            self._recorder.capture(self.balls)

            # ASMR 충돌 사운드
            for evt in self.physics.collision_events:
                play_impact(evt.kind, evt.speed)

            if pocketed:
                for n in pocketed:
                    ball = next((b for b in self.balls if b.number == n), None)
                    if ball and ball.pocket_pos:
                        color = BALL_COLORS.get(n, (200, 200, 200))
                        self._effects.trigger(*ball.pocket_pos, color)
                real = [n for n in pocketed if n != 0]
                self._pocketed_count += len(real)
                self._shot_pocketed += len(real)
                if real:
                    play("pocket")

            self._effects.update(dt)

            if not self.physics.any_moving(self.balls):
                self._moving = False
                frames = self._recorder.stop()

                # 리플레이 판단
                if should_replay(self._shot_pocketed):
                    self._replay.start(frames, self._shot_pocketed,
                                       on_complete=lambda: None)

                if cb.pocketed:
                    cb.place(GameLogic.CUE_START_X, GameLogic.CUE_START_Y)

    def draw(self, screen: pygame.Surface):
        screen.fill(C_BG)

        # 사이드바
        draw_sidebar(screen, user=self.manager.user)
        self._leave_btn.draw(screen)
        self._reset_btn.draw(screen)

        # 연습 모드 정보 (사이드바 안)
        info_f = pygame.font.SysFont("malgunGothic", 18)
        info_s = info_f.render(f"넣은 공: {self._pocketed_count}개", True, C_GOLD_LIGHT)
        screen.blit(info_s, (20, 120))

        hint_s = info_f.render("우클릭: 큐볼 재배치", True, C_TEXT_DIM)
        screen.blit(hint_s, (20, 145))
        hint2_s = info_f.render("ESC: 취소/메뉴", True, C_TEXT_DIM)
        screen.blit(hint2_s, (20, 168))

        # 턴 헤더
        draw_turn_header(screen, "연습 모드", highlight=False)

        # 테이블 + 공
        draw_table(screen)

        # 리플레이 재생 중이면 녹화된 프레임 렌더링
        if self._replay.active:
            states = self._replay.get_ball_states()
            if states:
                for num, x, y, rot_x, rot_y, pocketed in states:
                    if pocketed:
                        continue
                    # 임시 Ball 객체로 렌더링
                    tmp = Ball(num, x, y)
                    tmp.rot_x = rot_x
                    tmp.rot_y = rot_y
                    draw_ball(screen, tmp)
            self._replay.draw_overlay(screen)
            return

        cb = self._cue_ball
        if not self._moving and not cb.pocketed:
            draw_guide_line(screen, cb, self.cue.shot_angle,
                               other_balls=self.balls)
            self.cue.draw(screen, cb, self._power)
            self.cue.draw_spin_indicator(screen)

        draw_balls(screen, self.balls)

        # 포켓 폭죽 이펙트
        self._effects.draw(screen)

"""
로컬 2인 게임 씬 — 사이드바 + 볼 상태 바 + 게임 HUD.
스핀 마우스 컨트롤 + ASMR 사운드 + 리플레이.
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
from game.game_logic import GameLogic, Phase, TurnResult
from game.sound    import play, play_impact
from game.replay   import ReplayRecorder, ReplayPlayer, should_replay
from ui.button     import Button
from ui.dialog     import Dialog
from ui.game_hud   import draw_sidebar, draw_ball_status_bar, draw_turn_header


class LocalGameScene(BaseScene):

    STATE_WAITING = "waiting"
    STATE_MOVING  = "moving"
    STATE_HAND    = "hand"
    STATE_OVER    = "over"
    STATE_REPLAY  = "replay"

    def on_enter(self, **kwargs):
        p1 = kwargs.get("player1", "플레이어 1")
        p2 = kwargs.get("player2", "플레이어 2")
        self._init_game(p1, p2)

    def _init_game(self, p1: str, p2: str):
        self.logic   = GameLogic(p1, p2)
        self.physics = Physics()
        self.cue     = Cue()
        self.balls   = self._build_balls()
        self.state   = self.STATE_WAITING

        self._pocketed_this_shot: list[int] = []
        self._cue_pocketed = False
        self._power = 0.0
        self._charging = False
        self._charge_start = (0, 0)
        self._dragging_cue = False

        # 리플레이
        self._recorder = ReplayRecorder()
        self._replay   = ReplayPlayer()
        self._pending_turn_end = False  # 리플레이 후 턴 처리 대기

        self._effects = PocketEffects()
        self._result_dialog = Dialog("", "", ["새 게임", "메뉴로"])
        self._font_msg  = pygame.font.SysFont("malgunGothic", 20)
        self._font_hud  = pygame.font.SysFont("malgunGothic", 19)

        # 사이드바 내 나가기 버튼
        self._leave_btn = Button(
            (15, WIN_H - 100, SIDEBAR_W - 30, 36),
            "← 메뉴로 나가기", 18,
            color=C_RED, text_color=(255, 255, 255),
        )

        self._msg_timer = 0.0

    def _build_balls(self) -> list[Ball]:
        balls = [Ball(0, GameLogic.CUE_START_X, GameLogic.CUE_START_Y)]
        for num, x, y in self.logic.rack_positions():
            balls.append(Ball(num, x, y))
        return balls

    @property
    def _cue_ball(self) -> Ball:
        return next(b for b in self.balls if b.number == 0)

    # ── Event ───────────────────────────────────────────

    def handle_event(self, event: pygame.event.Event):
        # 리플레이 중에는 스페이스로 건너뛰기만
        if self._replay.active:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                self._replay.skip()
            return

        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            if self._charging:
                self._charging = False
                self._power    = 0.0
            return

        if self._result_dialog.visible:
            r = self._result_dialog.handle_event(event)
            if r == "새 게임":
                p1 = self.logic.players[0].name
                p2 = self.logic.players[1].name
                self._init_game(p1, p2)
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
                    self._power    = 0.0

            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                if self._charging and self._power > 0.02:
                    self._shoot()
                self._charging = False

        elif self.state == self.STATE_HAND:
            cb = self._cue_ball
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mx, my = event.pos
                if TABLE_X + BALL_RADIUS < mx < TABLE_X + TABLE_W - BALL_RADIUS:
                    if TABLE_Y + BALL_RADIUS < my < TABLE_Y + TABLE_H - BALL_RADIUS:
                        cb.place(mx, my)
                        self.state = self.STATE_WAITING

    def _shoot(self):
        cb = self._cue_ball
        if cb.pocketed:
            return
        vx, vy = self.cue.get_velocity(self._power)
        cb.vx = vx
        cb.vy = vy
        cb.spin_x = self.cue.spin_x
        cb.spin_y = self.cue.spin_y
        cb.spin_power = math.hypot(self.cue.spin_x, self.cue.spin_y)
        cb.shot_dir_x = math.cos(self.cue.shot_angle)
        cb.shot_dir_y = math.sin(self.cue.shot_angle)
        self.cue.reset_spin()
        self.state              = self.STATE_MOVING
        self._pocketed_this_shot = []
        self._cue_pocketed      = False
        self._power             = 0.0
        self._recorder.start(self.balls)
        play("cue_shoot")

    # ── Update ──────────────────────────────────────────

    def update(self, dt: float):
        # 리플레이 재생 중
        if self._replay.active:
            self._replay.update(dt)
            return

        mouse = self.manager.get_mouse_pos()

        if self.state == self.STATE_WAITING:
            cb = self._cue_ball
            if not cb.pocketed and not self._charging:
                self.cue.update_angle(cb, mouse)
            if self._charging:
                dx = mouse[0] - self._charge_start[0]
                dy = mouse[1] - self._charge_start[1]
                dist = math.hypot(dx, dy)
                self._power = min(1.0, dist / 120.0)

        elif self.state == self.STATE_MOVING:
            new_pocketed = self.physics.step(self.balls, dt)
            self._recorder.capture(self.balls)

            # ASMR 충돌 사운드
            for evt in self.physics.collision_events:
                play_impact(evt.kind, evt.speed)

            for n in new_pocketed:
                ball = next((b for b in self.balls if b.number == n), None)
                if ball and ball.pocket_pos:
                    color = BALL_COLORS.get(n, (200, 200, 200))
                    self._effects.trigger(*ball.pocket_pos, color)
                if n == 0:
                    self._cue_pocketed = True
                    play("pocket")
                elif n is not None:
                    play("pocket")
            self._pocketed_this_shot.extend(new_pocketed)

            if not self.physics.any_moving(self.balls):
                frames = self._recorder.stop()
                real_pocketed = len([n for n in self._pocketed_this_shot if n != 0])

                # 리플레이 판단
                if should_replay(real_pocketed):
                    self._replay.start(
                        frames, real_pocketed,
                        on_complete=self._process_turn_end
                    )
                    self.state = self.STATE_REPLAY
                else:
                    self._process_turn_end()

        self._effects.update(dt)

        if self._msg_timer > 0:
            self._msg_timer -= dt

    def _process_turn_end(self):
        result = self.logic.on_shot_end(
            self._pocketed_this_shot,
            None,
            self._cue_pocketed,
        )
        self._msg_timer = 3.0

        if result in (TurnResult.WIN, TurnResult.LOSE):
            self.state = self.STATE_OVER
            winner = self.logic.players[self.logic.winner]
            self._result_dialog.title   = "게임 종료!"
            self._result_dialog.message = f"{winner.name}  승리!"
            self._result_dialog.show()
            play("win")
            self._save_result()
        elif result == TurnResult.FOUL:
            cb = self._cue_ball
            if cb.pocketed:
                cx, cy = self.logic.ball_in_hand_position()
                cb.place(cx, cy)
            self.state = self.STATE_HAND
            play("foul")
        else:
            self.state = self.STATE_WAITING

    def _save_result(self):
        if not self.manager.user:
            return
        winner_idx = self.logic.winner
        if winner_idx is None:
            return
        try:
            self.manager.api.save_match(
                winner_id=None, loser_id=None, game_mode="local",
            )
        except Exception:
            pass

    # ── Draw ────────────────────────────────────────────

    def draw(self, screen: pygame.Surface):
        screen.fill(C_BG)

        # 사이드바
        draw_sidebar(
            screen,
            user=self.manager.user,
            players=self.logic.players,
            current_turn=self.logic.current,
        )
        self._leave_btn.draw(screen)

        # 턴 헤더
        cp = self.logic.current_player
        if self.state == self.STATE_HAND:
            draw_turn_header(screen, "볼인핸드 — 테이블을 클릭해 큐볼을 배치하세요", highlight=True)
        elif self.state in (self.STATE_MOVING, self.STATE_REPLAY):
            draw_turn_header(screen, "공이 이동 중...", highlight=False)
        else:
            draw_turn_header(screen, f"{cp.name}의 차례예요", highlight=True)

        # 볼 상태 바
        p1 = self.logic.players[0]
        p2 = self.logic.players[1]
        draw_ball_status_bar(screen, self.balls, p1, p2)

        # 테이블
        draw_table(screen)

        # 리플레이 재생 중이면 녹화된 프레임 렌더링
        if self._replay.active:
            states = self._replay.get_ball_states()
            if states:
                for num, x, y, rot_x, rot_y, pocketed in states:
                    if pocketed:
                        continue
                    tmp = Ball(num, x, y)
                    tmp.rot_x = rot_x
                    tmp.rot_y = rot_y
                    draw_ball(screen, tmp)
            self._replay.draw_overlay(screen)
        else:
            cb = self._cue_ball

            # 가이드라인 + 큐대 + 스핀 인디케이터
            if self.state == self.STATE_WAITING and not cb.pocketed:
                draw_guide_line(screen, cb, self.cue.shot_angle,
                                   other_balls=self.balls)
                self.cue.draw(screen, cb, self._power)
                self.cue.draw_spin_indicator(screen)

            # 볼인핸드 미리보기
            if self.state == self.STATE_HAND:
                mx, my = self.manager.get_mouse_pos()
                preview = pygame.Surface((BALL_RADIUS * 2, BALL_RADIUS * 2), pygame.SRCALPHA)
                pygame.draw.circle(preview, (248, 248, 248, 160),
                                   (BALL_RADIUS, BALL_RADIUS), BALL_RADIUS)
                screen.blit(preview, (mx - BALL_RADIUS, my - BALL_RADIUS))

            draw_balls(screen, self.balls)

        # 포켓 폭죽 이펙트
        self._effects.draw(screen)

        # 메시지
        if self._msg_timer > 0 and self.logic.message:
            ms = self._font_msg.render(self.logic.message, True, C_GOLD_LIGHT)
            bg = pygame.Surface((ms.get_width() + 20, ms.get_height() + 10), pygame.SRCALPHA)
            bg.fill((0, 0, 0, 160))
            mcx = TABLE_X + TABLE_W // 2
            screen.blit(bg, bg.get_rect(centerx=mcx, centery=TABLE_Y + TABLE_H + 30))
            screen.blit(ms, ms.get_rect(centerx=mcx, centery=TABLE_Y + TABLE_H + 30))

        # 페이즈 표시
        if self.logic.phase == Phase.BREAK:
            ph = self._font_hud.render("BREAK SHOT", True, C_TEXT_DIM)
            screen.blit(ph, ph.get_rect(
                centerx=TABLE_X + TABLE_W // 2, y=TABLE_Y + TABLE_H + 10))

        self._result_dialog.draw(screen)

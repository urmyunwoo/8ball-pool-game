"""
원격 대결 게임 씬 — WebSocket으로 실시간 동기화.
사이드바 + 볼 상태 바 포함. 스핀 마우스 + ASMR 사운드.
"""
import pygame
import asyncio
import json
import threading
import math
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from config import (
    WIN_W, WIN_H, C_BG, C_GOLD, C_GOLD_LIGHT, C_TEXT, C_TEXT_DIM,
    TABLE_X, TABLE_Y, TABLE_W, TABLE_H, BALL_RADIUS, SIDEBAR_W, C_RED,
    BALL_COLORS,
)
from scenes.base_scene   import BaseScene
from game.physics        import Ball, Physics
from game.table          import draw_table, draw_balls, draw_guide_line, PocketEffects
from game.cue            import Cue
from game.game_logic     import GameLogic, Phase, TurnResult
from game.sound          import play, play_impact
from ui.button           import Button
from ui.dialog           import Dialog
from ui.chat_box         import ChatBox
from ui.game_hud         import draw_sidebar, draw_ball_status_bar, draw_turn_header


class OnlineGameScene(BaseScene):

    STATE_WAITING   = "waiting"
    STATE_MOVING    = "moving"
    STATE_OPPONENT  = "opponent"
    STATE_HAND      = "hand"
    STATE_OVER      = "over"

    def on_enter(self, **kwargs):
        self._room_id = kwargs.get("room_id", "")
        self._role    = kwargs.get("role", "host")

        self.physics = Physics()
        self.cue     = Cue()
        self.balls:  list[Ball] = []
        self.state   = self.STATE_OPPONENT

        self._power    = 0.0
        self._charging = False
        self._charge_start = (0, 0)
        self._pocketed_this_shot: list[int] = []
        self._cue_pocketed = False

        self._effects = PocketEffects()
        self._font_name = pygame.font.SysFont("malgunGothic", 22, bold=True)
        self._font_msg  = pygame.font.SysFont("malgunGothic", 20)
        self._font_hud  = pygame.font.SysFont("malgunGothic", 19)

        self._leave_btn = Button(
            (15, WIN_H - 100, SIDEBAR_W - 30, 36),
            "매치 나가기", 18,
            color=C_RED, text_color=(255, 255, 255),
        )
        self._result_dialog = Dialog("", "", ["메뉴로"])

        # 채팅
        self._chat = ChatBox((TABLE_X + TABLE_W + 10, TABLE_Y, 120, TABLE_H))
        self._chat.on_send = self._send_chat

        self._my_name    = self.manager.user["nickname"] if self.manager.user else "나"
        self._opp_name   = "상대방"
        self._my_turn    = self._role == "host"

        # 더미 플레이어 데이터 (사이드바용)
        self._players = [
            _SimplePlayer(self._my_name),
            _SimplePlayer(self._opp_name),
        ]

        # WebSocket
        self._ws_thread  = None
        self._ws_queue: list[dict] = []
        self._ws_lock    = threading.Lock()
        self._connect_ws()

    def _connect_ws(self):
        from network.ws_client import WsClient
        self._ws = WsClient(
            self.manager.ws_url,
            self._room_id,
            self.manager.user["token"] if self.manager.user else "",
        )
        self._ws.on_message = self._on_ws_message
        self._ws_thread = threading.Thread(target=self._ws.run, daemon=True)
        self._ws_thread.start()

    def _on_ws_message(self, msg: dict):
        with self._ws_lock:
            self._ws_queue.append(msg)

    def _send_chat(self, text: str):
        self._chat.add_message("나", text)
        if hasattr(self, "_ws"):
            self._ws.send({"type": "chat", "message": text})

    # ── Event ───────────────────────────────────────────

    def handle_event(self, event: pygame.event.Event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            if self._charging:
                self._charging = False
                self._power    = 0.0
            return

        if self._result_dialog.visible:
            r = self._result_dialog.handle_event(event)
            if r:
                self._cleanup()
                self.manager.switch("menu")
            return

        if self._leave_btn.handle_event(event):
            self._cleanup()
            self.manager.switch("menu")

        self._chat.handle_event(event)

        if not self._my_turn or self.state not in (self.STATE_WAITING, self.STATE_HAND):
            return

        if self.state == self.STATE_WAITING:
            # 스핀 마우스 컨트롤 우선
            if self.cue.handle_spin_mouse(event):
                return

            if event.type == pygame.KEYDOWN:
                self.cue.handle_spin_key(event.key)

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if TABLE_X <= event.pos[0] <= TABLE_X + TABLE_W:
                    if TABLE_Y <= event.pos[1] <= TABLE_Y + TABLE_H:
                        self._charging = True
                        self._charge_start = event.pos
                        self._power    = 0.0
            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                if self._charging and self._power > 0.02:
                    self._shoot()
                self._charging = False

        elif self.state == self.STATE_HAND:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mx, my = event.pos
                cb = self._get_cue_ball()
                if cb and TABLE_X + BALL_RADIUS < mx < TABLE_X + TABLE_W - BALL_RADIUS:
                    if TABLE_Y + BALL_RADIUS < my < TABLE_Y + TABLE_H - BALL_RADIUS:
                        cb.place(mx, my)
                        self.state = self.STATE_WAITING
                        self._ws.send({"type": "ball_in_hand", "x": mx, "y": my})

    def _shoot(self):
        cb = self._get_cue_ball()
        if not cb or cb.pocketed:
            return
        vx, vy = self.cue.get_velocity(self._power)
        cb.vx, cb.vy = vx, vy
        cb.spin_x = self.cue.spin_x
        cb.spin_y = self.cue.spin_y
        cb.spin_power = math.hypot(self.cue.spin_x, self.cue.spin_y)
        cb.shot_dir_x = math.cos(self.cue.shot_angle)
        cb.shot_dir_y = math.sin(self.cue.shot_angle)
        self.cue.reset_spin()
        self.state = self.STATE_MOVING
        self._pocketed_this_shot = []
        self._cue_pocketed = False
        play("cue_shoot")
        self._ws.send({
            "type":  "shot",
            "angle": self.cue.shot_angle,
            "power": self._power,
        })

    def _get_cue_ball(self) -> Ball | None:
        for b in self.balls:
            if b.number == 0:
                return b
        return None

    # ── Update ──────────────────────────────────────────

    def update(self, dt: float):
        with self._ws_lock:
            msgs = list(self._ws_queue)
            self._ws_queue.clear()
        for msg in msgs:
            self._handle_ws_message(msg)

        mouse = self.manager.get_mouse_pos()
        if self.state == self.STATE_WAITING and self._my_turn:
            cb = self._get_cue_ball()
            if cb and not cb.pocketed and not self._charging:
                self.cue.update_angle(cb, mouse)
            if self._charging:
                dx = mouse[0] - self._charge_start[0]
                dy = mouse[1] - self._charge_start[1]
                dist = math.hypot(dx, dy)
                self._power = min(1.0, dist / 120.0)

        if self.state == self.STATE_MOVING:
            pocketed = self.physics.step(self.balls, dt)

            # ASMR 충돌 사운드
            for evt in self.physics.collision_events:
                play_impact(evt.kind, evt.speed)

            if pocketed:
                for n in pocketed:
                    ball = next((b for b in self.balls if b.number == n), None)
                    if ball and ball.pocket_pos:
                        color = BALL_COLORS.get(n, (200, 200, 200))
                        self._effects.trigger(*ball.pocket_pos, color)
                    if n == 0:
                        self._cue_pocketed = True
                    play("pocket")
                self._pocketed_this_shot.extend(pocketed)
            if not self.physics.any_moving(self.balls):
                self.state = self.STATE_OPPONENT
                self._ws.send({
                    "type":     "turn_end",
                    "pocketed": self._pocketed_this_shot,
                    "cue_in":   self._cue_pocketed,
                })

        self._effects.update(dt)
        self._chat.update(dt)

    def _handle_ws_message(self, msg: dict):
        t = msg.get("type")

        if t == "init":
            self.balls = [Ball.from_dict(d) for d in msg.get("balls", [])]
            self.state = self.STATE_WAITING if self._my_turn else self.STATE_OPPONENT

        elif t == "opponent_shot":
            cb = self._get_cue_ball()
            if cb:
                angle = msg["angle"]
                power = msg["power"]
                cb.vx = math.cos(angle) * power
                cb.vy = math.sin(angle) * power
            self.state = self.STATE_MOVING
            play("cue_shoot")

        elif t == "turn_switch":
            self._my_turn = msg.get("your_turn", False)
            self.state = self.STATE_WAITING if self._my_turn else self.STATE_OPPONENT

        elif t == "ball_in_hand":
            cb = self._get_cue_ball()
            if cb:
                cb.place(msg["x"], msg["y"])
            self.state = self.STATE_WAITING if self._my_turn else self.STATE_OPPONENT

        elif t == "game_over":
            winner = msg.get("winner", "")
            self._result_dialog.title   = "게임 종료!"
            self._result_dialog.message = f"{winner}  승리!"
            self._result_dialog.show()
            self.state = self.STATE_OVER
            play("win")

        elif t == "chat":
            sender  = msg.get("sender", "상대")
            content = msg.get("message", "")
            self._chat.add_message(sender, content)

        elif t == "opponent_name":
            self._opp_name = msg.get("name", "상대방")
            self._players[1].name = self._opp_name

    def _cleanup(self):
        if hasattr(self, "_ws"):
            self._ws.close()

    # ── Draw ────────────────────────────────────────────

    def draw(self, screen: pygame.Surface):
        screen.fill(C_BG)

        # 사이드바
        turn_idx = 0 if self._my_turn else 1
        draw_sidebar(
            screen,
            user=self.manager.user,
            players=self._players,
            current_turn=turn_idx,
        )
        self._leave_btn.draw(screen)

        # 턴 헤더
        if self._my_turn:
            draw_turn_header(screen, "내 차례예요", highlight=True)
        else:
            draw_turn_header(screen, f"{self._opp_name}의 차례...", highlight=False)

        # 볼 상태 바
        draw_ball_status_bar(screen, self.balls)

        # 테이블
        draw_table(screen)

        cb = self._get_cue_ball()
        if self.state == self.STATE_WAITING and self._my_turn and cb and not cb.pocketed:
            draw_guide_line(screen, cb, self.cue.shot_angle,
                               other_balls=self.balls)
            self.cue.draw(screen, cb, self._power)
            self.cue.draw_spin_indicator(screen)

        draw_balls(screen, self.balls)

        # 포켓 폭죽 이펙트
        self._effects.draw(screen)

        self._chat.draw(screen)
        self._result_dialog.draw(screen)


class _SimplePlayer:
    """사이드바 렌더링용 간이 플레이어 객체."""
    def __init__(self, name):
        self.name = name
        self.group = None

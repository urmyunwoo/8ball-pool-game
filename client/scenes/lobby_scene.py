"""
원격 대결 로비 씬.
방 생성(코드 발급) or 코드 입력해서 입장.
"""
import pygame
import threading
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from config import (
    WIN_W, WIN_H, SIDEBAR_W,
    C_BG, C_GOLD, C_GOLD_LIGHT, C_TEXT, C_TEXT_DIM, C_RED,
)
from scenes.base_scene import BaseScene
from ui.button     import Button
from ui.text_input import TextInput
from ui.game_hud   import draw_menu_sidebar


class LobbyScene(BaseScene):

    MODE_CHOOSE = "choose"
    MODE_CREATE = "create"
    MODE_JOIN   = "join"

    def on_enter(self, **kwargs):
        self._mode   = self.MODE_CHOOSE
        self._error  = ""
        self._room_code  = ""
        self._waiting    = False

        cx = SIDEBAR_W + (WIN_W - SIDEBAR_W) // 2
        self._create_btn = Button((cx - 210, 340, 200, 54), "방 만들기",  28)
        self._join_btn   = Button((cx + 10,  340, 200, 54), "방 입장",    28)
        self._back_btn   = Button((SIDEBAR_W + 20, 20, 100, 38), "← 메뉴", 22)

        self._code_input  = TextInput((cx - 160, 340, 320, 48), "방 코드 (6자리)", 24, max_length=6)
        self._enter_btn   = Button((cx - 80, 406, 160, 48), "입장하기", 24)

        self._copy_btn    = Button((cx - 80, 406, 160, 42), "코드 복사", 22)
        self._refresh_btn = Button((cx - 80, 460, 160, 42), "새로고침", 22)

        self._title_font  = pygame.font.SysFont("malgunGothic", 40, bold=True)
        self._code_font   = pygame.font.SysFont("consolas",      62, bold=True)
        self._sub_font    = pygame.font.SysFont("malgunGothic",  22)
        self._err_font    = pygame.font.SysFont("malgunGothic",  19)

    def handle_event(self, event: pygame.event.Event):
        if self._back_btn.handle_event(event):
            self.manager.switch("menu")

        if self._mode == self.MODE_CHOOSE:
            if self._create_btn.handle_event(event):
                self._do_create_room()
            if self._join_btn.handle_event(event):
                self._mode = self.MODE_JOIN
                self._error = ""

        elif self._mode == self.MODE_JOIN:
            self._code_input.handle_event(event)
            if self._enter_btn.handle_event(event):
                self._do_join_room()

        elif self._mode == self.MODE_CREATE:
            if self._copy_btn.handle_event(event):
                try:
                    import pyperclip
                    pyperclip.copy(self._room_code)
                except Exception:
                    pass
            if self._refresh_btn.handle_event(event):
                self._check_room_ready()

    def _do_create_room(self):
        ok, data = self.manager.api.create_room()
        if ok:
            self._room_code = data.get("room_code", "")
            self._room_id   = data.get("room_id", "")
            self._mode      = self.MODE_CREATE
            self._error     = ""
        else:
            self._error = data.get("detail", "방 생성 실패")

    def _do_join_room(self):
        code = self._code_input.value.strip().upper()
        if len(code) != 6:
            self._error = "6자리 코드를 입력하세요"
            return
        ok, data = self.manager.api.join_room(code)
        if ok:
            self.manager.switch("online_game", room_id=data["room_id"], role="guest")
        else:
            self._error = data.get("detail", "입장 실패")

    def _check_room_ready(self):
        ok, data = self.manager.api.get_room(self._room_id)
        if ok and data.get("status") == "playing":
            self.manager.switch("online_game", room_id=self._room_id, role="host")
        else:
            self._error = "상대방이 아직 입장하지 않았습니다"

    def update(self, dt: float):
        if self._mode == self.MODE_JOIN:
            self._code_input.update(dt)

    def draw(self, screen: pygame.Surface):
        screen.fill((22, 26, 38))

        # 사이드바
        draw_menu_sidebar(screen, self.manager.user)

        cx = SIDEBAR_W + (WIN_W - SIDEBAR_W) // 2

        t = self._title_font.render("원격 대결", True, C_GOLD_LIGHT)
        screen.blit(t, t.get_rect(centerx=cx, y=80))

        self._back_btn.draw(screen)

        if self._mode == self.MODE_CHOOSE:
            desc = self._sub_font.render(
                "방을 만들거나, 친구의 방 코드를 입력해 입장하세요", True, C_TEXT_DIM)
            screen.blit(desc, desc.get_rect(centerx=cx, y=160))
            self._create_btn.draw(screen)
            self._join_btn.draw(screen)

        elif self._mode == self.MODE_CREATE:
            desc = self._sub_font.render(
                "아래 코드를 친구에게 공유하세요", True, C_TEXT_DIM)
            screen.blit(desc, desc.get_rect(centerx=cx, y=160))

            code_s = self._code_font.render(self._room_code, True, C_GOLD)
            screen.blit(code_s, code_s.get_rect(centerx=cx, y=240))

            wait_s = self._sub_font.render("상대방 입장 대기 중...", True, C_TEXT_DIM)
            screen.blit(wait_s, wait_s.get_rect(centerx=cx, y=370))
            self._copy_btn.draw(screen)
            self._refresh_btn.draw(screen)

        elif self._mode == self.MODE_JOIN:
            desc = self._sub_font.render(
                "친구에게 받은 6자리 방 코드를 입력하세요", True, C_TEXT_DIM)
            screen.blit(desc, desc.get_rect(centerx=cx, y=160))
            self._code_input.draw(screen)
            self._enter_btn.draw(screen)

        if self._error:
            es = self._err_font.render(self._error, True, C_RED)
            screen.blit(es, es.get_rect(centerx=cx, y=520))

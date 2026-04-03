"""
로그인 / 회원가입 씬.
탭 전환으로 두 기능을 한 화면에서 처리.
"""
import pygame
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from config import (
    WIN_W, WIN_H, SIDEBAR_W,
    C_BG, C_GOLD, C_GOLD_LIGHT, C_TEXT, C_TEXT_DIM, C_RED,
)
from scenes.base_scene import BaseScene
from ui.button import Button
from ui.text_input import TextInput
from ui.dialog import Dialog
from ui.game_hud import draw_menu_sidebar


class AuthScene(BaseScene):
    TAB_LOGIN    = "login"
    TAB_REGISTER = "register"

    def on_enter(self, **kwargs):
        self._next_scene = kwargs.get("next_scene", "menu")
        self._tab = self.TAB_LOGIN
        self._error = ""
        self._loading = False
        self._build_widgets()

    def _build_widgets(self):
        # 사이드바 오른쪽 게임 영역 중앙
        cx = SIDEBAR_W + (WIN_W - SIDEBAR_W) // 2
        form_w = 420
        form_x = cx - form_w // 2

        self._tab_login_btn    = Button((cx - 210, 160, 200, 44), "로그인",   24)
        self._tab_reg_btn      = Button((cx + 10,  160, 200, 44), "회원가입", 24)

        self._email_input  = TextInput((form_x, 240, form_w, 48), "이메일",   24)
        self._pw_input     = TextInput((form_x, 306, form_w, 48), "비밀번호", 24, password=True)

        self._nick_input   = TextInput((form_x, 372, form_w, 48), "닉네임",   24)
        self._pw2_input    = TextInput((form_x, 438, form_w, 48), "비밀번호 확인", 24, password=True)

        submit_y = 390 if self._tab == self.TAB_LOGIN else 504
        self._submit_btn = Button(
            (form_x, submit_y, form_w, 52),
            "로그인" if self._tab == self.TAB_LOGIN else "가입하기", 26,
        )
        self._back_btn = Button((SIDEBAR_W + 20, 20, 100, 38), "← 뒤로", 22)

        self._title_font  = pygame.font.SysFont("malgunGothic", 44, bold=True)
        self._label_font  = pygame.font.SysFont("malgunGothic", 20)
        self._error_font  = pygame.font.SysFont("malgunGothic", 19)

    def handle_event(self, event: pygame.event.Event):
        if self._tab_login_btn.handle_event(event):
            self._tab = self.TAB_LOGIN
            self._error = ""
            self._build_widgets()
        if self._tab_reg_btn.handle_event(event):
            self._tab = self.TAB_REGISTER
            self._error = ""
            self._build_widgets()

        if self._back_btn.handle_event(event):
            self.manager.switch("menu")

        self._email_input.handle_event(event)
        self._pw_input.handle_event(event)
        if self._tab == self.TAB_REGISTER:
            self._nick_input.handle_event(event)
            self._pw2_input.handle_event(event)

        if self._submit_btn.handle_event(event):
            self._on_submit()

    def _on_submit(self):
        email = self._email_input.value.strip()
        pw    = self._pw_input.value.strip()

        if not email or not pw:
            self._error = "이메일과 비밀번호를 입력하세요."
            return

        if self._tab == self.TAB_LOGIN:
            ok, data = self.manager.api.login(email, pw)
            if ok:
                self.manager.set_user(data)
                self.manager.switch(self._next_scene)
            else:
                self._error = data.get("detail", "로그인 실패")
        else:
            nick = self._nick_input.value.strip()
            pw2  = self._pw2_input.value.strip()
            if not nick:
                self._error = "닉네임을 입력하세요."
                return
            if pw != pw2:
                self._error = "비밀번호가 일치하지 않습니다."
                return
            ok, data = self.manager.api.register(email, pw, nick)
            if ok:
                ok2, data2 = self.manager.api.login(email, pw)
                if ok2:
                    self.manager.set_user(data2)
                    self.manager.switch(self._next_scene)
                else:
                    self._error = "가입 성공! 로그인 해주세요."
                    self._tab = self.TAB_LOGIN
                    self._build_widgets()
            else:
                self._error = data.get("detail", "가입 실패")

    def update(self, dt: float):
        self._email_input.update(dt)
        self._pw_input.update(dt)
        if self._tab == self.TAB_REGISTER:
            self._nick_input.update(dt)
            self._pw2_input.update(dt)

    def draw(self, screen: pygame.Surface):
        screen.fill((22, 26, 38))

        # 사이드바
        draw_menu_sidebar(screen, self.manager.user)

        cx = SIDEBAR_W + (WIN_W - SIDEBAR_W) // 2

        # 제목
        t = self._title_font.render("Pool Game — 계정", True, C_GOLD_LIGHT)
        screen.blit(t, t.get_rect(centerx=cx, y=80))

        # 탭 버튼
        self._tab_login_btn.draw(screen)
        self._tab_reg_btn.draw(screen)

        # 활성 탭 밑줄
        if self._tab == self.TAB_LOGIN:
            r = self._tab_login_btn.rect
        else:
            r = self._tab_reg_btn.rect
        pygame.draw.line(screen, C_GOLD, (r.x, r.bottom + 2), (r.right, r.bottom + 2), 2)

        # 폼 필드
        self._draw_label(screen, "이메일", self._email_input.rect.x, self._email_input.rect.y - 22)
        self._email_input.draw(screen)
        self._draw_label(screen, "비밀번호", self._pw_input.rect.x, self._pw_input.rect.y - 22)
        self._pw_input.draw(screen)

        if self._tab == self.TAB_REGISTER:
            self._draw_label(screen, "닉네임", self._nick_input.rect.x, self._nick_input.rect.y - 22)
            self._nick_input.draw(screen)
            self._draw_label(screen, "비밀번호 확인", self._pw2_input.rect.x, self._pw2_input.rect.y - 22)
            self._pw2_input.draw(screen)

        self._submit_btn.draw(screen)
        self._back_btn.draw(screen)

        if self._error:
            es = self._error_font.render(self._error, True, C_RED)
            screen.blit(es, es.get_rect(centerx=cx, y=self._submit_btn.rect.bottom + 14))

    def _draw_label(self, screen, text, x, y):
        ls = self._label_font.render(text, True, C_TEXT_DIM)
        screen.blit(ls, (x, y))

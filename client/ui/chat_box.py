"""
인게임 채팅 UI 컴포넌트.
"""
import pygame
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from config import C_GOLD, C_TEXT, C_TEXT_DIM


class ChatBox:
    BG_COLOR     = (15, 12, 10, 200)
    BORDER_COLOR = C_GOLD
    MAX_MESSAGES = 30

    def __init__(self, rect: tuple[int, int, int, int]):
        self.rect        = pygame.Rect(rect)
        self._messages: list[tuple[str, str]] = []  # [(sender, text), ...]
        self._input_text = ""
        self._font       = pygame.font.SysFont("malgunGothic", 18)
        self._input_font = pygame.font.SysFont("malgunGothic", 18)
        self._active     = False
        self._input_rect = pygame.Rect(
            self.rect.x, self.rect.bottom - 30,
            self.rect.width - 60, 28,
        )
        self._send_rect  = pygame.Rect(
            self._input_rect.right + 4, self._input_rect.y,
            54, 28,
        )
        self._cursor_vis = True
        self._cursor_t   = 0.0
        self.on_send     = None   # callback(text: str)

    def add_message(self, sender: str, text: str):
        self._messages.append((sender, text))
        if len(self._messages) > self.MAX_MESSAGES:
            self._messages.pop(0)

    def handle_event(self, event: pygame.event.Event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            self._active = self._input_rect.collidepoint(event.pos)
            if self._send_rect.collidepoint(event.pos):
                self._send()
        elif event.type == pygame.KEYDOWN and self._active:
            if event.key == pygame.K_RETURN:
                self._send()
            elif event.key == pygame.K_BACKSPACE:
                self._input_text = self._input_text[:-1]
            elif len(self._input_text) < 80:
                self._input_text += event.unicode

    def update(self, dt: float):
        self._cursor_t += dt
        if self._cursor_t >= 0.5:
            self._cursor_t  = 0.0
            self._cursor_vis = not self._cursor_vis

    def draw(self, screen: pygame.Surface):
        # 배경
        bg = pygame.Surface(self.rect.size, pygame.SRCALPHA)
        bg.fill(self.BG_COLOR)
        screen.blit(bg, self.rect.topleft)
        pygame.draw.rect(screen, self.BORDER_COLOR, self.rect, 1, border_radius=4)

        # 메시지 목록
        line_h = 22
        max_lines = (self.rect.height - 40) // line_h
        visible = self._messages[-max_lines:]
        y_start = self.rect.y + 6
        for sender, text in visible:
            color = C_GOLD if sender == "나" else C_TEXT
            s = self._font.render(f"{sender}: {text}", True, color)
            screen.blit(s, (self.rect.x + 6, y_start))
            y_start += line_h

        # 입력창
        border_c = C_GOLD if self._active else (60, 60, 60)
        pygame.draw.rect(screen, (20, 20, 20), self._input_rect, border_radius=4)
        pygame.draw.rect(screen, border_c, self._input_rect, 1, border_radius=4)
        ts = self._input_font.render(self._input_text, True, C_TEXT)
        screen.blit(ts, (self._input_rect.x + 6, self._input_rect.y + 6))
        if self._active and self._cursor_vis:
            cx = self._input_rect.x + 6 + ts.get_width() + 1
            pygame.draw.line(screen, C_TEXT, (cx, self._input_rect.y + 5), (cx, self._input_rect.bottom - 5), 1)

        # 전송 버튼
        pygame.draw.rect(screen, (40, 40, 40), self._send_rect, border_radius=4)
        pygame.draw.rect(screen, C_GOLD, self._send_rect, 1, border_radius=4)
        ss = self._input_font.render("전송", True, C_GOLD)
        screen.blit(ss, ss.get_rect(center=self._send_rect.center))

    def _send(self):
        text = self._input_text.strip()
        if text and self.on_send:
            self.on_send(text)
            self._input_text = ""

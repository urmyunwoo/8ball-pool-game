"""
텍스트 입력창 컴포넌트.
"""
import pygame
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from config import C_GOLD, C_TEXT, C_TEXT_DIM


class TextInput:
    BG_INACTIVE   = (25, 25, 25)
    BG_ACTIVE     = (35, 35, 35)
    BORDER_INACTIVE = (80, 80, 80)
    BORDER_ACTIVE   = C_GOLD

    def __init__(
        self,
        rect: tuple[int, int, int, int],
        placeholder: str = "",
        font_size: int = 20,
        max_length: int = 64,
        password: bool = False,
    ):
        self.rect        = pygame.Rect(rect)
        self.placeholder = placeholder
        self.font        = pygame.font.SysFont("malgunGothic", font_size)
        self.max_length  = max_length
        self.password    = password
        self.text        = ""
        self.active      = False
        self._cursor_vis = True
        self._cursor_t   = 0.0

    @property
    def value(self) -> str:
        return self.text

    def handle_event(self, event: pygame.event.Event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            self.active = self.rect.collidepoint(event.pos)
        elif event.type == pygame.KEYDOWN and self.active:
            if event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
            elif event.key in (pygame.K_RETURN, pygame.K_TAB):
                self.active = False
            elif len(self.text) < self.max_length:
                self.text += event.unicode

    def update(self, dt: float):
        if self.active:
            self._cursor_t += dt
            if self._cursor_t >= 0.5:
                self._cursor_t  = 0.0
                self._cursor_vis = not self._cursor_vis
        else:
            self._cursor_vis = False

    def draw(self, screen: pygame.Surface):
        bg     = self.BG_ACTIVE if self.active else self.BG_INACTIVE
        border = self.BORDER_ACTIVE if self.active else self.BORDER_INACTIVE

        pygame.draw.rect(screen, bg, self.rect, border_radius=6)
        pygame.draw.rect(screen, border, self.rect, 2, border_radius=6)

        if self.text:
            display = ("*" * len(self.text)) if self.password else self.text
            ts = self.font.render(display, True, C_TEXT)
        else:
            ts = self.font.render(self.placeholder, True, C_TEXT_DIM)

        # Clip text to input rect
        clip = self.rect.inflate(-12, 0)
        screen.set_clip(clip)
        screen.blit(ts, (self.rect.x + 10, self.rect.centery - ts.get_height() // 2))
        screen.set_clip(None)

        # Cursor
        if self.active and self._cursor_vis:
            cx = self.rect.x + 10 + ts.get_width() + 2
            cy = self.rect.y + 6
            pygame.draw.line(screen, C_TEXT, (cx, cy), (cx, self.rect.bottom - 6), 2)

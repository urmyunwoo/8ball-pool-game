"""
공통 버튼 컴포넌트.
"""
import pygame
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from config import C_GOLD, C_GOLD_LIGHT, C_TEXT, C_BG


class Button:
    NORMAL_COLOR  = (35, 35, 35)
    HOVER_COLOR   = (55, 55, 55)
    PRESS_COLOR   = (20, 20, 20)
    BORDER_COLOR  = C_GOLD
    BORDER_HOVER  = C_GOLD_LIGHT
    TEXT_COLOR    = C_TEXT

    def __init__(
        self,
        rect: tuple[int, int, int, int],
        text: str,
        font_size: int = 20,
        color: tuple | None = None,
        border_color: tuple | None = None,
        text_color: tuple | None = None,
    ):
        self.rect         = pygame.Rect(rect)
        self.text         = text
        self.font         = pygame.font.SysFont("malgunGothic", font_size, bold=True)
        self._color       = color or self.NORMAL_COLOR
        self._hover_color = (
            min(255, color[0] + 25),
            min(255, color[1] + 25),
            min(255, color[2] + 25),
        ) if color else self.HOVER_COLOR
        self._border      = border_color or self.BORDER_COLOR
        self._text_color  = text_color or self.TEXT_COLOR
        self._hovered     = False
        self._pressed     = False
        self.enabled      = True

    def handle_event(self, event: pygame.event.Event) -> bool:
        """Returns True if clicked."""
        if not self.enabled:
            return False
        if event.type == pygame.MOUSEMOTION:
            self._hovered = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self._pressed = True
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if self._pressed and self.rect.collidepoint(event.pos):
                self._pressed = False
                return True
            self._pressed = False
        return False

    def draw(self, screen: pygame.Surface):
        if self._pressed:
            color = self.PRESS_COLOR
        elif self._hovered:
            color = self._hover_color
        else:
            color = self._color

        border = self.BORDER_HOVER if self._hovered else self._border

        # 배경
        pygame.draw.rect(screen, color, self.rect, border_radius=8)
        # 테두리
        pygame.draw.rect(screen, border, self.rect, 2, border_radius=8)

        if not self.enabled:
            # 비활성화 오버레이
            s = pygame.Surface(self.rect.size, pygame.SRCALPHA)
            s.fill((0, 0, 0, 100))
            screen.blit(s, self.rect.topleft)

        # 텍스트
        ts = self.font.render(self.text, True, self._text_color)
        screen.blit(ts, ts.get_rect(center=self.rect.center))

"""
팝업 다이얼로그 컴포넌트.
사용 예: "AI 준비중", 게임 결과, 확인 메시지 등.
"""
import pygame
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from config import WIN_W, WIN_H, C_GOLD, C_GOLD_LIGHT, C_TEXT, C_TEXT_DIM
from ui.button import Button


class Dialog:
    BG_COLOR     = (20, 15, 12)
    BORDER_COLOR = C_GOLD

    def __init__(
        self,
        title: str,
        message: str,
        buttons: list[str] | None = None,
        width: int = 460,
        height: int = 240,
    ):
        self.title   = title
        self.message = message
        self._result: str | None = None
        self.visible = False

        self._rect = pygame.Rect(
            WIN_W // 2 - width // 2,
            WIN_H // 2 - height // 2,
            width, height,
        )

        btn_labels = buttons or ["확인"]
        btn_w = 120
        spacing = 20
        total   = len(btn_labels) * btn_w + (len(btn_labels) - 1) * spacing
        start_x = self._rect.centerx - total // 2
        btn_y   = self._rect.bottom - 60

        self._buttons: dict[str, Button] = {}
        for i, label in enumerate(btn_labels):
            bx = start_x + i * (btn_w + spacing)
            self._buttons[label] = Button((bx, btn_y, btn_w, 40), label, 22)

        self._title_font = pygame.font.SysFont("malgunGothic", 28, bold=True)
        self._msg_font   = pygame.font.SysFont("malgunGothic", 22)

    def show(self):
        self.visible  = True
        self._result  = None

    def hide(self):
        self.visible = False

    @property
    def result(self) -> str | None:
        """클릭된 버튼 라벨, 아직 없으면 None."""
        return self._result

    def handle_event(self, event: pygame.event.Event) -> str | None:
        if not self.visible:
            return None
        for label, btn in self._buttons.items():
            if btn.handle_event(event):
                self._result = label
                self.visible = False
                return label
        return None

    def draw(self, screen: pygame.Surface):
        if not self.visible:
            return

        # 반투명 오버레이
        overlay = pygame.Surface((WIN_W, WIN_H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        screen.blit(overlay, (0, 0))

        # 배경
        pygame.draw.rect(screen, self.BG_COLOR, self._rect, border_radius=12)
        pygame.draw.rect(screen, self.BORDER_COLOR, self._rect, 2, border_radius=12)

        # 제목
        ts = self._title_font.render(self.title, True, C_GOLD_LIGHT)
        screen.blit(ts, ts.get_rect(centerx=self._rect.centerx, y=self._rect.y + 24))

        # 구분선
        pygame.draw.line(
            screen, C_GOLD,
            (self._rect.x + 20, self._rect.y + 58),
            (self._rect.right - 20, self._rect.y + 58), 1,
        )

        # 메시지 (줄바꿈 지원)
        y = self._rect.y + 74
        for line in self.message.split("\n"):
            ms = self._msg_font.render(line, True, C_TEXT)
            screen.blit(ms, ms.get_rect(centerx=self._rect.centerx, y=y))
            y += 26

        # 버튼
        for btn in self._buttons.values():
            btn.draw(screen)

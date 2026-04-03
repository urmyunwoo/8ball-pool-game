"""
메인 메뉴 씬 — 참조 이미지 스타일로 디자인.
사이드바 + 큰 타이틀 + 컬러 버튼 레이아웃.
"""
import pygame
import math
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from config import (
    WIN_W, WIN_H, SIDEBAR_W,
    C_BG, C_GOLD, C_GOLD_LIGHT, C_TEXT, C_TEXT_DIM,
    C_BTN_GREEN, C_BTN_ORANGE, C_BTN_BLUE, C_BTN_DARK,
    C_SIDEBAR_BG, C_SIDEBAR_BORDER,
)
from scenes.base_scene import BaseScene
from ui.button import Button
from ui.dialog import Dialog
from ui.game_hud import draw_menu_sidebar
from game.sound import play


class MenuScene(BaseScene):

    def on_enter(self, **kwargs):
        # 게임 영역 중앙 (사이드바 오른쪽)
        game_cx = SIDEBAR_W + (WIN_W - SIDEBAR_W) // 2
        bw_full = 640       # 전체 너비 버튼
        bw_half = 308       # 반쪽 버튼
        bh      = 56
        bh_big  = 64
        gap     = 14

        # 버튼 시작 y
        btn_y = 310

        # 상단 행: 원격 대결 (녹색) + AI 대결 (주황)
        self._btn_online = _ColorButton(
            (game_cx - bw_full//2, btn_y, bw_half, bh_big),
            "🎱  원격 대결", 24, C_BTN_GREEN,
        )
        self._btn_ai = _ColorButton(
            (game_cx + bw_full//2 - bw_half, btn_y, bw_half, bh_big),
            "🤖  AI 대결", 24, C_BTN_ORANGE,
        )
        btn_y += bh_big + gap

        # 로컬 2인 대결 (녹색 와이드)
        self._btn_local = _ColorButton(
            (game_cx - bw_full//2, btn_y, bw_full, bh),
            "로컬 2인 대결", 24, C_BTN_GREEN,
        )
        btn_y += bh + gap

        # 혼자 연습하기 (파란색 와이드)
        self._btn_practice = _ColorButton(
            (game_cx - bw_full//2, btn_y, bw_full, bh + 10),
            "혼자 연습하기", 24, C_BTN_BLUE,
            subtitle="자유롭게 연습할 수 있습니다",
        )
        btn_y += bh + 10 + gap + 10

        # 캐롬 당구: 3구 + 4구
        self._btn_3cushion = _ColorButton(
            (game_cx - bw_full//2, btn_y, bw_half, bh),
            "3구 쓰리쿠션", 24, C_BTN_DARK,
        )
        self._btn_4ball = _ColorButton(
            (game_cx + bw_full//2 - bw_half, btn_y, bw_half, bh),
            "4구", 24, C_BTN_DARK,
        )
        btn_y += bh + gap

        # 하단 행: 전적 보기 + 게임 방법
        self._btn_records = _OutlineButton(
            (game_cx - bw_full//2, btn_y, bw_half, 46),
            "전적 보기", 22,
        )
        self._btn_help = _OutlineButton(
            (game_cx + bw_full//2 - bw_half, btn_y, bw_half, 46),
            "게임 방법 알아보기", 22,
        )

        # 로그인 버튼 (사이드바 내)
        user = self.manager.user
        if user:
            self._auth_btn = Button(
                (15, WIN_H - 100, SIDEBAR_W - 30, 36),
                f"로그아웃 ({user['nickname']})", 18,
            )
        else:
            self._auth_btn = Button(
                (15, WIN_H - 100, SIDEBAR_W - 30, 36),
                "로그인 / 가입", 18,
            )

        self._ai_dialog = Dialog(
            "AI 모드 준비 중",
            "AI 대결 모드는 현재 개발 중입니다.\n조금만 기다려 주세요!",
            ["확인"],
        )
        self._help_dialog = Dialog(
            "게임 방법",
            "8볼 포켓볼 규칙:\n"
            "• 솔리드(1-7) 또는 스트라이프(9-15)를 먼저 다 넣으세요\n"
            "• 자기 공을 다 넣은 후 8번 공을 넣으면 승리!\n"
            "• 큐볼이 포켓되면 파울 (상대방 볼인핸드)\n"
            "• 마우스 드래그로 파워 조절, 화살표 키로 스핀 조절",
            ["확인"],
        )

        self._title_font = pygame.font.SysFont("impact", 84, bold=True)
        self._title_font2 = pygame.font.SysFont("impact", 82)
        self._sub_font   = pygame.font.SysFont("malgunGothic", 20)

        self._name_dialog = None
        self._pending_mode = None  # "3cushion" | "4ball" | None(로컬)

    def handle_event(self, event: pygame.event.Event):
        if self._ai_dialog.visible:
            self._ai_dialog.handle_event(event)
            return
        if self._help_dialog.visible:
            self._help_dialog.handle_event(event)
            return

        if self._name_dialog and self._name_dialog.visible:
            result = self._name_dialog.handle_event(event)
            if result == "시작":
                p1, p2 = self._name_dialog.names
                if p1.strip() and p2.strip():
                    if self._pending_mode:
                        self.manager.switch("carom_game",
                                            mode=self._pending_mode,
                                            player1=p1.strip(), player2=p2.strip())
                    else:
                        self.manager.switch("local_game",
                                            player1=p1.strip(), player2=p2.strip())
            elif result == "취소":
                pass
            return

        if self._btn_online.handle_event(event):
            play("btn_click")
            if not self.manager.user:
                self.manager.switch("auth", next_scene="lobby")
            else:
                self.manager.switch("lobby")
        if self._btn_ai.handle_event(event):
            play("btn_click")
            self._ai_dialog.show()
        if self._btn_local.handle_event(event):
            play("btn_click")
            self._pending_mode = None
            self._name_dialog = _NameInputDialog()
            self._name_dialog.show()
        if self._btn_3cushion.handle_event(event):
            play("btn_click")
            self._pending_mode = "3cushion"
            self._name_dialog = _NameInputDialog()
            self._name_dialog.show()
        if self._btn_4ball.handle_event(event):
            play("btn_click")
            self._pending_mode = "4ball"
            self._name_dialog = _NameInputDialog()
            self._name_dialog.show()
        if self._btn_practice.handle_event(event):
            play("btn_click")
            self.manager.switch("practice")
        if self._btn_records.handle_event(event):
            play("btn_click")
            self.manager.switch("records")
        if self._btn_help.handle_event(event):
            play("btn_click")
            self._help_dialog.show()

        if self._auth_btn.handle_event(event):
            play("btn_click")
            if self.manager.user:
                self.manager.logout()
                self.on_enter()
            else:
                self.manager.switch("auth")

    def update(self, dt: float):
        pass

    def draw(self, screen: pygame.Surface):
        # 전체 배경
        screen.fill((22, 26, 38))

        # 사이드바
        draw_menu_sidebar(screen, self.manager.user)

        # 로그인 버튼 (사이드바 안)
        self._auth_btn.draw(screen)

        # ── 타이틀 영역 ──
        game_cx = SIDEBAR_W + (WIN_W - SIDEBAR_W) // 2

        # 타이틀 배경 배너 (초록색 그라디언트 줄)
        banner_y = 100
        banner_h = 120
        banner_rect = pygame.Rect(SIDEBAR_W + 40, banner_y, WIN_W - SIDEBAR_W - 80, banner_h)

        # 그라디언트 배너
        for i in range(banner_h):
            t = i / banner_h
            r_v = int(20 + 15 * math.sin(t * math.pi))
            g_v = int(90 + 40 * math.sin(t * math.pi))
            b_v = int(30 + 15 * math.sin(t * math.pi))
            pygame.draw.line(screen, (r_v, g_v, b_v),
                             (banner_rect.x, banner_rect.y + i),
                             (banner_rect.right, banner_rect.y + i))
        pygame.draw.rect(screen, (30, 110, 45), banner_rect, 3, border_radius=16)

        # 8볼 아이콘
        ball_cx = game_cx - 200
        ball_cy = banner_y + banner_h // 2
        # 공 그림자
        pygame.draw.circle(screen, (10, 50, 18), (ball_cx + 2, ball_cy + 2), 38)
        # 공 몸체
        pygame.draw.circle(screen, (20, 20, 20), (ball_cx, ball_cy), 38)
        # 하이라이트
        pygame.draw.circle(screen, (50, 50, 50), (ball_cx - 10, ball_cy - 10), 14)
        pygame.draw.circle(screen, (80, 80, 80), (ball_cx - 12, ball_cy - 12), 6)
        # 8 번호 원
        pygame.draw.circle(screen, (255, 255, 255), (ball_cx, ball_cy), 16)
        eight_f = pygame.font.SysFont("impact", 28, bold=True)
        eight_s = eight_f.render("8", True, (15, 15, 15))
        screen.blit(eight_s, eight_s.get_rect(center=(ball_cx, ball_cy)))

        # "BALL POOL" 텍스트
        title_x = ball_cx + 55
        title_y = banner_y + banner_h // 2

        # 외곽선 효과
        outline_f = self._title_font
        outline_text = "BALL POOL"
        for ox, oy in [(-2, -2), (2, -2), (-2, 2), (2, 2), (0, 3)]:
            os_s = outline_f.render(outline_text, True, (10, 50, 18))
            screen.blit(os_s, os_s.get_rect(midleft=(title_x + ox, title_y + oy)))

        # 메인 타이틀 (흰색)
        title_s = outline_f.render(outline_text, True, (255, 255, 255))
        screen.blit(title_s, title_s.get_rect(midleft=(title_x, title_y)))

        # ── 버튼들 ──
        self._btn_online.draw(screen)
        self._btn_ai.draw(screen)
        self._btn_local.draw(screen)
        self._btn_practice.draw(screen)
        self._btn_3cushion.draw(screen)
        self._btn_4ball.draw(screen)
        self._btn_records.draw(screen)
        self._btn_help.draw(screen)

        # 하단 배너
        footer_y = WIN_H - 70
        footer_rect = pygame.Rect(SIDEBAR_W + 40, footer_y,
                                  WIN_W - SIDEBAR_W - 80, 55)
        pygame.draw.rect(screen, (40, 44, 55), footer_rect, border_radius=10)
        pygame.draw.rect(screen, (55, 60, 72), footer_rect, 1, border_radius=10)
        footer_s = self._sub_font.render("포켓볼 게임에 오신 것을 환영합니다!", True, C_TEXT_DIM)
        screen.blit(footer_s, footer_s.get_rect(
            centery=footer_rect.centery, x=footer_rect.x + 20))

        # 다이얼로그
        self._ai_dialog.draw(screen)
        self._help_dialog.draw(screen)
        if self._name_dialog:
            self._name_dialog.draw(screen)


# ── 컬러 버튼 ──────────────────────────────────────────────

class _ColorButton:
    """배경색이 있는 게임 스타일 버튼."""

    def __init__(self, rect, text, font_size, color, subtitle=None):
        self.rect = pygame.Rect(rect)
        self.text = text
        self.color = color
        self.subtitle = subtitle
        self.font = pygame.font.SysFont("malgunGothic", font_size, bold=True)
        self.sub_font = pygame.font.SysFont("malgunGothic", 17) if subtitle else None
        self._hovered = False
        self._pressed = False

    def handle_event(self, event):
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

    def draw(self, screen):
        r, g, b = self.color
        if self._pressed:
            c = (max(0, r - 30), max(0, g - 30), max(0, b - 30))
        elif self._hovered:
            c = (min(255, r + 20), min(255, g + 20), min(255, b + 20))
        else:
            c = self.color

        # 그림자
        shadow = self.rect.move(0, 3)
        pygame.draw.rect(screen, (max(0, c[0] - 40), max(0, c[1] - 40), max(0, c[2] - 40)),
                         shadow, border_radius=10)
        # 배경
        pygame.draw.rect(screen, c, self.rect, border_radius=10)
        # 상단 하이라이트
        hl_rect = pygame.Rect(self.rect.x + 2, self.rect.y + 2,
                               self.rect.width - 4, self.rect.height // 3)
        hl_surf = pygame.Surface(hl_rect.size, pygame.SRCALPHA)
        hl_surf.fill((255, 255, 255, 25))
        screen.blit(hl_surf, hl_rect)

        # 텍스트
        ts = self.font.render(self.text, True, (255, 255, 255))
        if self.subtitle:
            ty = self.rect.centery - 10
        else:
            ty = self.rect.centery
        screen.blit(ts, ts.get_rect(centerx=self.rect.centerx, centery=ty))

        if self.subtitle and self.sub_font:
            ss = self.sub_font.render(self.subtitle, True, (255, 255, 255, 180))
            screen.blit(ss, ss.get_rect(centerx=self.rect.centerx,
                                         centery=self.rect.centery + 14))


class _OutlineButton:
    """테두리만 있는 버튼."""

    def __init__(self, rect, text, font_size):
        self.rect = pygame.Rect(rect)
        self.text = text
        self.font = pygame.font.SysFont("malgunGothic", font_size, bold=True)
        self._hovered = False
        self._pressed = False

    def handle_event(self, event):
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

    def draw(self, screen):
        bg = (55, 60, 72) if self._hovered else (40, 44, 55)
        if self._pressed:
            bg = (30, 34, 44)
        pygame.draw.rect(screen, bg, self.rect, border_radius=8)
        border = C_TEXT_DIM if self._hovered else (70, 75, 88)
        pygame.draw.rect(screen, border, self.rect, 2, border_radius=8)

        ts = self.font.render(self.text, True, C_TEXT)
        screen.blit(ts, ts.get_rect(center=self.rect.center))


# ── 이름 입력 다이얼로그 ─────────────────────────────────

class _NameInputDialog:

    def __init__(self):
        from ui.text_input import TextInput
        w, h = 440, 280
        self._rect = pygame.Rect(WIN_W // 2 - w // 2, WIN_H // 2 - h // 2, w, h)
        self.visible = False

        self._inp1 = TextInput(
            (self._rect.x + 30, self._rect.y + 80, 380, 44),
            placeholder="플레이어 1 이름", font_size=19,
        )
        self._inp2 = TextInput(
            (self._rect.x + 30, self._rect.y + 140, 380, 44),
            placeholder="플레이어 2 이름", font_size=19,
        )
        self._start_btn  = Button((self._rect.x + 30,  self._rect.bottom - 56, 180, 42), "시작",  20)
        self._cancel_btn = Button((self._rect.right - 210, self._rect.bottom - 56, 180, 42), "취소",  20)
        self._font = pygame.font.SysFont("malgunGothic", 26, bold=True)

    @property
    def names(self):
        return self._inp1.value, self._inp2.value

    def show(self):
        self.visible = True
        self._inp1.text = ""
        self._inp2.text = ""

    def handle_event(self, event):
        if not self.visible:
            return None
        self._inp1.handle_event(event)
        self._inp2.handle_event(event)
        if self._start_btn.handle_event(event):
            self.visible = False
            return "시작"
        if self._cancel_btn.handle_event(event):
            self.visible = False
            return "취소"
        return None

    def draw(self, screen):
        if not self.visible:
            return
        overlay = pygame.Surface((WIN_W, WIN_H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        screen.blit(overlay, (0, 0))

        pygame.draw.rect(screen, (20, 14, 10), self._rect, border_radius=12)
        pygame.draw.rect(screen, C_GOLD, self._rect, 2, border_radius=12)

        t = self._font.render("플레이어 이름 입력", True, C_GOLD_LIGHT)
        screen.blit(t, t.get_rect(centerx=self._rect.centerx, y=self._rect.y + 20))

        self._inp1.draw(screen)
        self._inp2.draw(screen)
        self._start_btn.draw(screen)
        self._cancel_btn.draw(screen)

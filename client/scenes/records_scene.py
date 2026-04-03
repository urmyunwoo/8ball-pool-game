"""
전적 보기 씬 — 서버에서 내 기록과 리더보드를 가져온다.
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
from ui.game_hud import draw_menu_sidebar


class RecordsScene(BaseScene):

    def on_enter(self, **kwargs):
        cx = SIDEBAR_W + (WIN_W - SIDEBAR_W) // 2
        self._back_btn    = Button((SIDEBAR_W + 20, 20, 100, 38), "← 메뉴", 22)
        self._refresh_btn = Button((SIDEBAR_W + 130, 20, 100, 38), "새로고침", 22)
        self._title_font  = pygame.font.SysFont("malgunGothic", 38, bold=True)
        self._sub_font    = pygame.font.SysFont("malgunGothic", 22)
        self._cell_font   = pygame.font.SysFont("malgunGothic", 20)
        self._err_font    = pygame.font.SysFont("malgunGothic", 19)

        self._my_stats: dict | None = None
        self._leaderboard: list     = []
        self._history: list         = []
        self._error = ""
        self._load_data()

    def _load_data(self):
        if not self.manager.user:
            self._error = "로그인 후 이용 가능합니다"
            return
        try:
            ok1, data1 = self.manager.api.get_my_records()
            if ok1:
                self._my_stats = data1.get("stats", {})
                self._history  = data1.get("history", [])
            else:
                self._error = data1.get("detail", "기록 로드 실패")

            ok2, data2 = self.manager.api.get_leaderboard()
            if ok2:
                self._leaderboard = data2.get("rankings", [])
        except Exception as e:
            self._error = f"서버 연결 실패: {e}"

    def handle_event(self, event: pygame.event.Event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.manager.switch("menu")
        if self._back_btn.handle_event(event):
            self.manager.switch("menu")
        if self._refresh_btn.handle_event(event):
            self._error = ""
            self._load_data()

    def update(self, dt: float):
        pass

    def draw(self, screen: pygame.Surface):
        screen.fill((22, 26, 38))

        # 사이드바
        draw_menu_sidebar(screen, self.manager.user)

        cx = SIDEBAR_W + (WIN_W - SIDEBAR_W) // 2

        title = self._title_font.render("전적 보기", True, C_GOLD_LIGHT)
        screen.blit(title, title.get_rect(centerx=cx, y=24))

        self._back_btn.draw(screen)
        self._refresh_btn.draw(screen)

        if self._error:
            es = self._err_font.render(self._error, True, C_RED)
            screen.blit(es, es.get_rect(centerx=cx, y=100))
            return

        y = 90
        content_x = SIDEBAR_W + 60

        # ── 내 통계 ──
        if self._my_stats:
            wins   = self._my_stats.get("wins", 0)
            losses = self._my_stats.get("losses", 0)
            total  = wins + losses
            rate   = f"{wins/total*100:.1f}%" if total else "0%"

            stat_x = cx - 300
            self._draw_stat_card(screen, "총 경기",  str(total), stat_x,        y)
            self._draw_stat_card(screen, "승리",     str(wins),  stat_x + 160,  y)
            self._draw_stat_card(screen, "패배",     str(losses),stat_x + 320,  y)
            self._draw_stat_card(screen, "승률",     rate,       stat_x + 480,  y)
            y += 100

        # ── 최근 매치 히스토리 ──
        if self._history:
            ht = self._sub_font.render("최근 경기 기록", True, C_GOLD)
            screen.blit(ht, (content_x, y))
            y += 32
            for match in self._history[:8]:
                mode     = match.get("game_mode", "?")
                result   = "승" if match.get("won") else "패"
                opp      = match.get("opponent_name", "?")
                date     = match.get("played_at", "")[:10]
                color    = C_GOLD_LIGHT if result == "승" else (180, 80, 80)
                row = f"[{result}]  vs {opp}  ({mode})  {date}"
                rs  = self._cell_font.render(row, True, color)
                screen.blit(rs, (content_x, y))
                y += 26
            y += 10

        # ── 리더보드 ──
        if self._leaderboard:
            lb_x = cx + 20
            lt = self._sub_font.render("랭킹 TOP 10", True, C_GOLD)
            screen.blit(lt, (lb_x, 90))
            row_y = 130
            for i, entry in enumerate(self._leaderboard[:10]):
                rank = entry.get("rank", i + 1)
                name = entry.get("nickname", "?")
                wins = entry.get("wins", 0)
                rate = entry.get("win_rate", 0)
                row  = f"#{rank}  {name}  {wins}승  {rate:.0f}%"
                color = C_GOLD_LIGHT if rank <= 3 else C_TEXT
                rs = self._cell_font.render(row, True, color)
                screen.blit(rs, (lb_x, row_y))
                row_y += 26

    def _draw_stat_card(self, screen, label, value, x, y):
        rect = pygame.Rect(x, y, 140, 80)
        pygame.draw.rect(screen, (28, 32, 45), rect, border_radius=8)
        pygame.draw.rect(screen, C_GOLD, rect, 1, border_radius=8)
        vf = pygame.font.SysFont("malgunGothic", 34, bold=True)
        lf = pygame.font.SysFont("malgunGothic", 18)
        vs = vf.render(value, True, C_GOLD_LIGHT)
        ls = lf.render(label, True, C_TEXT_DIM)
        screen.blit(vs, vs.get_rect(centerx=x + 70, y=y + 14))
        screen.blit(ls, ls.get_rect(centerx=x + 70, y=y + 52))

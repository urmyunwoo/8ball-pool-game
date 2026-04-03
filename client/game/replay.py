"""
리플레이 시스템 — 샷 녹화 및 하이라이트 재생.
멋진 콤보나 어려운 샷을 슬로모션으로 다시 보여줌.
"""
import pygame
import pygame.gfxdraw
import math
import copy
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from config import (
    TABLE_X, TABLE_Y, TABLE_W, TABLE_H,
    C_GOLD_LIGHT, C_TEXT, C_TEXT_DIM,
)


class ReplayFrame:
    """한 프레임의 공 상태 스냅샷."""
    __slots__ = ('balls',)

    def __init__(self, balls_data: list[tuple]):
        # (number, x, y, rot_x, rot_y, pocketed)
        self.balls = balls_data


class ReplayRecorder:
    """샷 동안의 공 상태를 녹화."""

    MAX_FRAMES = 1200  # 최대 ~10초 @ 120FPS

    def __init__(self):
        self._frames: list[ReplayFrame] = []
        self._recording = False
        self._frame_skip = 0
        self._skip_counter = 0

    def start(self, balls):
        """녹화 시작."""
        self._frames.clear()
        self._recording = True
        self._skip_counter = 0
        # 120FPS에서 매 2프레임마다 기록 (60FPS 재생)
        self._frame_skip = 1
        self._capture(balls)

    def capture(self, balls):
        """프레임 캡처 (매 update마다 호출)."""
        if not self._recording:
            return
        self._skip_counter += 1
        if self._skip_counter >= self._frame_skip:
            self._skip_counter = 0
            self._capture(balls)

    def stop(self) -> list[ReplayFrame]:
        """녹화 종료, 프레임 목록 반환."""
        self._recording = False
        return list(self._frames)

    def _capture(self, balls):
        if len(self._frames) >= self.MAX_FRAMES:
            return
        data = []
        for b in balls:
            data.append((
                b.number, b.x, b.y,
                b.rot_x, b.rot_y, b.pocketed,
            ))
        self._frames.append(ReplayFrame(data))


class ReplayPlayer:
    """녹화된 리플레이를 재생."""

    SLOWMO_SPEED = 0.35      # 슬로모션 배율
    FADE_IN_TIME = 0.5       # 리플레이 시작 페이드인
    LABEL_SHOW_TIME = 1.5    # "REPLAY" 라벨 표시 시간

    def __init__(self):
        self.active = False
        self._frames: list[ReplayFrame] = []
        self._frame_idx = 0.0
        self._elapsed = 0.0
        self._total_time = 0.0
        self._pocketed_count = 0
        self._on_complete = None
        self._label_font = None
        self._sub_font = None

    def start(self, frames: list[ReplayFrame], pocketed_count: int = 0,
              on_complete=None):
        """리플레이 재생 시작."""
        if not frames or len(frames) < 5:
            if on_complete:
                on_complete()
            return
        self.active = True
        self._frames = frames
        self._frame_idx = 0.0
        self._elapsed = 0.0
        self._total_time = len(frames) / 60.0 / self.SLOWMO_SPEED
        self._pocketed_count = pocketed_count
        self._on_complete = on_complete

    def skip(self):
        """리플레이 건너뛰기."""
        if self.active:
            self.active = False
            if self._on_complete:
                self._on_complete()

    def update(self, dt: float):
        """리플레이 프레임 진행."""
        if not self.active:
            return
        self._elapsed += dt
        # 슬로모션으로 프레임 진행
        self._frame_idx += dt * 60.0 * self.SLOWMO_SPEED
        if self._frame_idx >= len(self._frames) - 1:
            self.active = False
            if self._on_complete:
                self._on_complete()

    def get_ball_states(self) -> list[tuple] | None:
        """현재 프레임의 공 상태 반환."""
        if not self.active or not self._frames:
            return None
        idx = min(int(self._frame_idx), len(self._frames) - 1)
        return self._frames[idx].balls

    def draw_overlay(self, screen: pygame.Surface):
        """리플레이 오버레이 UI."""
        if not self.active:
            return

        # 폰트 초기화
        if self._label_font is None:
            self._label_font = pygame.font.SysFont("arial", 34, bold=True)
            self._sub_font = pygame.font.SysFont("malgunGothic", 18)

        # 화면 어둡게 + 비네팅 효과
        vignette = pygame.Surface((screen.get_width(), screen.get_height()),
                                  pygame.SRCALPHA)
        alpha = min(60, int(self._elapsed * 120))
        vignette.fill((0, 0, 0, alpha))
        screen.blit(vignette, (0, 0))

        # 상단 "REPLAY" 배너
        banner_h = 36
        banner_y = TABLE_Y - 55
        banner_surf = pygame.Surface((TABLE_W, banner_h), pygame.SRCALPHA)

        # 펄스 효과
        pulse = 0.7 + 0.3 * math.sin(self._elapsed * 4)
        r_val = int(255 * pulse)
        g_val = int(180 * pulse)

        banner_surf.fill((20, 20, 30, 180))
        screen.blit(banner_surf, (TABLE_X, banner_y))

        # "REPLAY" 텍스트
        replay_text = self._label_font.render("REPLAY", True,
                                               (r_val, g_val, 40))
        tx = TABLE_X + TABLE_W // 2
        screen.blit(replay_text,
                    replay_text.get_rect(centerx=tx, centery=banner_y + banner_h // 2))

        # 슬로모션 아이콘
        slow_text = self._sub_font.render(
            f"x{self.SLOWMO_SPEED:.1f} 슬로모션", True, (180, 180, 180))
        screen.blit(slow_text,
                    slow_text.get_rect(centerx=tx, top=banner_y + banner_h + 2))

        # 하단 프로그레스 바
        prog_y = TABLE_Y + TABLE_H + 8
        prog_w = TABLE_W
        prog_h = 4
        pygame.draw.rect(screen, (50, 50, 60),
                         (TABLE_X, prog_y, prog_w, prog_h), border_radius=2)
        progress = self._frame_idx / max(1, len(self._frames) - 1)
        fill_w = int(prog_w * progress)
        pygame.draw.rect(screen, (255, 180, 40),
                         (TABLE_X, prog_y, fill_w, prog_h), border_radius=2)

        # 건너뛰기 힌트
        skip_text = self._sub_font.render(
            "SPACE: 건너뛰기", True, (120, 120, 120))
        screen.blit(skip_text,
                    skip_text.get_rect(centerx=tx, top=prog_y + 10))


def should_replay(pocketed_count: int, combo: bool = False) -> bool:
    """리플레이를 보여줄지 판단."""
    # 2개 이상 넣으면 리플레이
    if pocketed_count >= 2:
        return True
    return combo

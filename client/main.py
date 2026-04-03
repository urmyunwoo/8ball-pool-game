# -*- coding: utf-8 -*-
"""
포켓볼 게임 진입점.
실행: python main.py
"""
import sys
import os
import asyncio

# Windows 터미널 UTF-8 강제 설정
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

# 현재 폴더를 sys.path에 추가 (상대 임포트 해결)
sys.path.insert(0, os.path.dirname(__file__))

import pygame
import json

# ── 브라우저(WASM)에서 시스템 폰트가 없으므로 번들 폰트로 대체 ──
_FONT_DIR = os.path.join(os.path.dirname(__file__), "assets", "fonts")
_original_sysfont = pygame.font.SysFont

def _patched_sysfont(name, size, bold=False, italic=False):
    try:
        font_file = os.path.join(_FONT_DIR, "malgunbd.ttf" if bold else "malgun.ttf")
        if os.path.exists(font_file):
            return pygame.font.Font(font_file, size)
    except Exception:
        pass
    return _original_sysfont(name, size, bold=bold, italic=italic)

pygame.font.SysFont = _patched_sysfont

from config import WIN_W, WIN_H, FPS, TITLE, SERVER_URL, WS_URL, TOKEN_FILE
from game.sound import init_sound

from scenes.menu_scene         import MenuScene
from scenes.auth_scene         import AuthScene
from scenes.local_game_scene   import LocalGameScene
from scenes.practice_scene     import PracticeScene
from scenes.lobby_scene        import LobbyScene
from scenes.online_game_scene  import OnlineGameScene
from scenes.records_scene      import RecordsScene
from scenes.carom_game_scene   import CaromGameScene

from network.api_client import ApiClient


class SceneManager:
    """모든 씬을 관리하는 중앙 컨트롤러."""

    def __init__(self, screen: pygame.Surface, game_surface: pygame.Surface):
        self.screen   = screen
        self.game_surface = game_surface  # 고정 해상도 렌더링 서피스
        self._scenes: dict = {}
        self._current = None
        self.user: dict | None = None   # 로그인된 사용자 정보
        self.api      = ApiClient(SERVER_URL)
        self.ws_url   = WS_URL
        self._fullscreen = False

        # 저장된 토큰으로 자동 로그인 시도
        self._try_auto_login()

    def _try_auto_login(self):
        ok, data = self.api.get_me()
        if ok:
            self.user = data
            self.user["token"] = self.api._token

    def register(self, name: str, scene):
        self._scenes[name] = scene

    def switch(self, name: str, **kwargs):
        if name not in self._scenes:
            print(f"[SceneManager] 알 수 없는 씬: {name}")
            return
        self._current = self._scenes[name]
        self._current.on_enter(**kwargs)

    def set_user(self, data: dict):
        self.user = data
        self.user["token"] = self.api._token

    def logout(self):
        self.user = None
        self.api.clear_token()

    def get_mouse_pos(self):
        """실제 마우스 위치를 게임 논리 좌표로 변환하여 반환."""
        return self._scale_mouse_pos(pygame.mouse.get_pos())

    def toggle_fullscreen(self):
        """전체화면 / 창모드 토글."""
        self._fullscreen = not self._fullscreen
        if self._fullscreen:
            self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        else:
            self.screen = pygame.display.set_mode(
                (WIN_W, WIN_H), pygame.RESIZABLE
            )

    def _scale_mouse_pos(self, pos):
        """실제 화면 좌표 → 게임 논리 좌표로 변환."""
        sw, sh = self.screen.get_size()
        gw, gh = self.game_surface.get_size()
        scale = min(sw / gw, sh / gh)
        scaled_w = int(gw * scale)
        scaled_h = int(gh * scale)
        offset_x = (sw - scaled_w) // 2
        offset_y = (sh - scaled_h) // 2
        mx = (pos[0] - offset_x) / scale
        my = (pos[1] - offset_y) / scale
        return (mx, my)

    def _remap_mouse_event(self, event):
        """마우스 이벤트의 좌표를 게임 좌표로 변환."""
        if hasattr(event, 'pos'):
            new_pos = self._scale_mouse_pos(event.pos)
            # 새 이벤트 생성 대신 속성 덮어쓰기
            event.pos = (int(new_pos[0]), int(new_pos[1]))
        return event

    async def run(self):
        clock = pygame.time.Clock()
        from config import C_BG

        while True:
            dt = clock.tick(FPS) / 1000.0

            events = pygame.event.get()
            for e in events:
                if e.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if e.type == pygame.KEYDOWN and e.key == pygame.K_F11:
                    self.toggle_fullscreen()
                    continue
                if e.type == pygame.VIDEORESIZE and not self._fullscreen:
                    self.screen = pygame.display.set_mode(
                        (e.w, e.h), pygame.RESIZABLE
                    )
                    continue
                # 마우스 이벤트 좌표 변환
                if e.type in (pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP,
                              pygame.MOUSEMOTION):
                    e = self._remap_mouse_event(e)
                if self._current:
                    self._current.handle_event(e)

            if self._current:
                self._current.update(dt)
                self.game_surface.fill(C_BG)
                self._current.draw(self.game_surface)

            # game_surface를 화면에 맞춰 스케일링
            sw, sh = self.screen.get_size()
            gw, gh = self.game_surface.get_size()
            scale = min(sw / gw, sh / gh)
            scaled_w = int(gw * scale)
            scaled_h = int(gh * scale)
            offset_x = (sw - scaled_w) // 2
            offset_y = (sh - scaled_h) // 2

            self.screen.fill((0, 0, 0))
            scaled = pygame.transform.smoothscale(self.game_surface, (scaled_w, scaled_h))
            self.screen.blit(scaled, (offset_x, offset_y))

            pygame.display.flip()
            await asyncio.sleep(0)  # 브라우저 이벤트 루프에 양보


async def main():
    pygame.init()
    init_sound()

    # 모니터 크기에 맞춰 초기 창 크기 결정 (내부 해상도는 WIN_W x WIN_H 유지)
    display_info = pygame.display.Info()
    max_w = int(display_info.current_w * 0.95)
    max_h = int(display_info.current_h * 0.95)
    init_w = min(WIN_W, max_w)
    init_h = min(WIN_H, max_h)
    screen = pygame.display.set_mode((init_w, init_h), pygame.RESIZABLE)
    pygame.display.set_caption(TITLE)

    # 게임 논리 해상도 서피스 (고정)
    game_surface = pygame.Surface((WIN_W, WIN_H))

    # 아이콘 설정 (없어도 무방)
    try:
        icon = pygame.Surface((32, 32))
        icon.fill((22, 90, 30))
        pygame.draw.circle(icon, (248, 248, 248), (16, 16), 10)
        pygame.display.set_icon(icon)
    except Exception:
        pass

    manager = SceneManager(screen, game_surface)

    # 씬 등록
    manager.register("menu",         MenuScene(manager))
    manager.register("auth",         AuthScene(manager))
    manager.register("local_game",   LocalGameScene(manager))
    manager.register("practice",     PracticeScene(manager))
    manager.register("lobby",        LobbyScene(manager))
    manager.register("online_game",  OnlineGameScene(manager))
    manager.register("records",      RecordsScene(manager))
    manager.register("carom_game",   CaromGameScene(manager))

    # 시작 씬
    manager.switch("menu")
    await manager.run()


asyncio.run(main())

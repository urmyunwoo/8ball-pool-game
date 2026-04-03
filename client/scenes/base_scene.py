"""
모든 씬이 상속하는 추상 기반 클래스.
"""
import pygame


class BaseScene:
    def __init__(self, manager):
        self.manager = manager  # SceneManager 참조

    def on_enter(self, **kwargs):
        """씬 진입 시 호출."""
        pass

    def handle_event(self, event: pygame.event.Event):
        """Pygame 이벤트 처리."""
        pass

    def update(self, dt: float):
        """매 프레임 업데이트. dt = 경과 시간(초)."""
        pass

    def draw(self, screen: pygame.Surface):
        """매 프레임 렌더링."""
        pass

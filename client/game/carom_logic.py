"""
3구(쓰리쿠션)와 4구 캐롬 당구 게임 로직.
"""
from enum import Enum, auto


class CaromResult(Enum):
    SCORE = auto()   # 득점 → 턴 유지
    MISS  = auto()   # 실패 → 턴 교대
    WIN   = auto()   # 목표 점수 도달 → 승리


class CaromLogic:
    """3구 / 4구 규칙 관리."""

    def __init__(self, mode: str, p1_name: str, p2_name: str,
                 target_score: int = 0):
        self.mode = mode  # "3cushion" or "4ball"
        self.names = [p1_name, p2_name]
        self.scores = [0, 0]
        self.current = 0
        self.target_score = target_score or (10 if mode == "3cushion" else 15)
        # 플레이어별 큐볼: P1 → 0(흰), P2 → 1(노란)
        self.cue_balls = [0, 1]
        self.message = ""

    @property
    def current_name(self) -> str:
        return self.names[self.current]

    @property
    def current_cue(self) -> int:
        return self.cue_balls[self.current]

    def on_shot_end(self, cushion_hits: int, ball_contacts: set) -> CaromResult:
        """샷 종료 후 득점 판정."""
        scored = False

        if self.mode == "3cushion":
            # 나머지 공 2개 모두 접촉 + 쿠션 3회 이상
            others = {b for b in ball_contacts}
            scored = len(others) >= 2 and cushion_hits >= 3
        else:
            # 4구: 빨간공(번호 2, 3) 2개 모두 접촉
            reds = {b for b in ball_contacts if b >= 2}
            scored = len(reds) >= 2

        if scored:
            self.scores[self.current] += 1
            if self.scores[self.current] >= self.target_score:
                self.message = f"{self.current_name} 승리!"
                return CaromResult.WIN
            self.message = f"{self.current_name} 득점! ({self.scores[self.current]}점)"
            return CaromResult.SCORE

        # 미스 → 턴 교대
        self.message = f"실패 → {self.names[1 - self.current]} 차례"
        self.current = 1 - self.current
        return CaromResult.MISS

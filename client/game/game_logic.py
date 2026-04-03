"""
8볼 게임 규칙 엔진.
상태 머신: BREAK → PLAYING → FINISH
"""
from enum import Enum, auto
from dataclasses import dataclass, field
from typing import Optional
import math
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from config import TABLE_X, TABLE_Y, TABLE_W, TABLE_H, BALL_RADIUS


class Phase(Enum):
    BREAK   = auto()   # 첫 브레이크 샷 전
    PLAYING = auto()   # 그룹 배정 후 일반 플레이
    FINISH  = auto()   # 게임 종료


class TurnResult(Enum):
    CONTINUE = auto()  # 공 넣음 → 턴 유지
    SWITCH   = auto()  # 못 넣음 → 상대 턴
    FOUL     = auto()  # 파울 → 상대방 볼인핸드
    WIN      = auto()  # 현재 플레이어 승리
    LOSE     = auto()  # 현재 플레이어 패배 (8번 공 실수)


@dataclass
class PlayerState:
    name:   str
    group:  Optional[str] = None   # "solid" | "stripe"
    pocketed_balls: list = field(default_factory=list)

    @property
    def is_done(self) -> bool:
        """자기 그룹 7개를 모두 넣었는지."""
        if self.group is None:
            return False
        if self.group == "solid":
            return len([b for b in self.pocketed_balls if 1 <= b <= 7]) == 7
        else:
            return len([b for b in self.pocketed_balls if 9 <= b <= 15]) == 7


class GameLogic:
    """
    8볼 규칙을 관리한다.
    - phase: BREAK / PLAYING / FINISH
    - current: 현재 턴 플레이어 인덱스 (0 or 1)
    """

    # 큐볼 초기 위치
    CUE_START_X = TABLE_X + TABLE_W * 0.25
    CUE_START_Y = TABLE_Y + TABLE_H * 0.5

    def __init__(self, player1_name: str, player2_name: str):
        self.players  = [PlayerState(player1_name), PlayerState(player2_name)]
        self.current  = 0
        self.phase    = Phase.BREAK
        self.winner: Optional[int] = None   # 0 or 1
        self.message  = ""
        self._first_hit_group: Optional[str] = None

    # ── public ──────────────────────────────────────────

    @property
    def current_player(self) -> PlayerState:
        return self.players[self.current]

    @property
    def other_player(self) -> PlayerState:
        return self.players[1 - self.current]

    def on_shot_end(
        self,
        pocketed: list[int],
        first_hit_group: Optional[str],
        cue_pocketed: bool,
    ) -> TurnResult:
        """
        공이 다 멈춘 후 호출.
        pocketed: 이번 샷에 포켓된 공 번호 목록
        first_hit_group: 큐볼이 처음 맞춘 공의 그룹
        cue_pocketed: 큐볼이 포켓됐는지
        """
        if self.phase == Phase.FINISH:
            return TurnResult.CONTINUE

        # 큐볼 포켓 = 파울
        if cue_pocketed:
            self.message = f"파울: 큐볼이 포켓됐습니다! {self.other_player.name}이 볼인핸드 획득"
            self._switch_turn()
            return TurnResult.FOUL

        real_pocketed = [n for n in pocketed if n != 0]

        # 8번 공 포켓 처리
        if 8 in real_pocketed:
            return self._handle_eight_pocketed(real_pocketed)

        if self.phase == Phase.BREAK:
            return self._handle_break(real_pocketed, first_hit_group)
        else:
            return self._handle_playing(real_pocketed, first_hit_group, cue_pocketed)

    def ball_in_hand_position(self) -> tuple[float, float]:
        """볼인핸드 기본 위치."""
        return self.CUE_START_X, self.CUE_START_Y

    def rack_positions(self) -> list[tuple[int, float, float]]:
        """
        8볼 삼각 랙 배치 위치 반환.
        Returns: [(ball_number, x, y), ...]
        """
        # 랙 꼭짓점: 테이블 오른쪽 3/4 지점
        apex_x = TABLE_X + TABLE_W * 0.72
        apex_y = TABLE_Y + TABLE_H * 0.50
        gap    = BALL_RADIUS * 2 + 1  # 공 지름 + 밀착 여유

        # 표준 8볼 랙 순서 (5행 삼각형)
        order = [
            [1],
            [2, 9],
            [3, 8, 10],
            [4, 11, 7, 12],
            [5, 13, 6, 14, 15],
        ]
        # 행 간격: gap * √3/2  (정삼각형 높이)
        row_dx = gap * math.sqrt(3) / 2
        positions = []
        for row_i, row in enumerate(order):
            row_x = apex_x + row_i * row_dx
            for col_j, ball_num in enumerate(row):
                offset = col_j - (len(row) - 1) / 2
                row_y  = apex_y + offset * gap
                positions.append((ball_num, row_x, row_y))
        return positions

    # ── internal ────────────────────────────────────────

    def _handle_break(self, pocketed: list[int], first_group: Optional[str]) -> TurnResult:
        if not pocketed:
            # 브레이크에서 아무것도 못 넣음 → 턴 교대
            self.message = f"{self.current_player.name}이 턴을 넘깁니다"
            self._switch_turn()
            return TurnResult.SWITCH

        # 브레이크에서 공 넣으면 그룹 배정
        solid_count  = len([n for n in pocketed if 1 <= n <= 7])
        stripe_count = len([n for n in pocketed if 9 <= n <= 15])
        if solid_count >= stripe_count:
            self.current_player.group = "solid"
            self.other_player.group   = "stripe"
        else:
            self.current_player.group = "stripe"
            self.other_player.group   = "solid"
        self.phase = Phase.PLAYING
        self._record_pocketed(pocketed)
        self.message = (
            f"{self.current_player.name} → {self.current_player.group.upper()} | "
            f"{self.other_player.name} → {self.other_player.group.upper()}"
        )
        return TurnResult.CONTINUE

    def _handle_playing(self, pocketed, first_group, cue_pocketed) -> TurnResult:
        my_group    = self.current_player.group
        their_group = self.other_player.group

        # 파울: 첫 번째 맞춘 공이 상대방 공이거나 아무것도 안 맞춤
        if first_group is not None and first_group != my_group and first_group != "eight":
            self.message = f"파울: 상대방 공을 먼저 맞췄습니다"
            self._record_pocketed(pocketed)
            self._switch_turn()
            return TurnResult.FOUL

        # 자기 공 넣음
        my_balls = [n for n in pocketed if self._is_my_ball(n)]
        bad_balls = [n for n in pocketed if self._is_their_ball(n)]

        if bad_balls:
            self.message = f"상대방 공을 넣었습니다! 턴이 교대됩니다"
            self._record_pocketed(pocketed)
            self._switch_turn()
            return TurnResult.FOUL

        if my_balls:
            self._record_pocketed(pocketed)
            if not pocketed:
                # 아무것도 못 넣음
                self.message = f"공을 넣지 못했습니다 → {self.other_player.name} 턴"
                self._switch_turn()
                return TurnResult.SWITCH
            self.message = f"{self.current_player.name}이 {len(my_balls)}개 넣음!"
            return TurnResult.CONTINUE
        else:
            self._record_pocketed(pocketed)
            self.message = f"공을 넣지 못했습니다 → {self.other_player.name} 턴"
            self._switch_turn()
            return TurnResult.SWITCH

    def _handle_eight_pocketed(self, pocketed: list[int]) -> TurnResult:
        if self.phase == Phase.BREAK:
            # 브레이크에서 8번 즉시 넣으면 재랙
            self.message = "브레이크에서 8번 포켓! 다시 랙을 배치합니다"
            return TurnResult.FOUL

        if self.current_player.is_done:
            # 정상 승리
            self.phase  = Phase.FINISH
            self.winner = self.current
            self.message = f"🎱 {self.current_player.name} 승리!"
            return TurnResult.WIN
        else:
            # 아직 자기 공 다 못 넣은 상태에서 8번 포켓 → 패배
            self.phase  = Phase.FINISH
            self.winner = 1 - self.current
            self.message = f"{self.current_player.name}이 8번 공을 너무 일찍 넣었습니다 → {self.other_player.name} 승리!"
            return TurnResult.LOSE

    def _is_my_ball(self, n: int) -> bool:
        g = self.current_player.group
        if g == "solid":
            return 1 <= n <= 7
        return 9 <= n <= 15

    def _is_their_ball(self, n: int) -> bool:
        g = self.other_player.group
        if g is None:
            return False
        if g == "solid":
            return 1 <= n <= 7
        return 9 <= n <= 15

    def _record_pocketed(self, pocketed: list[int]):
        for n in pocketed:
            if n == 0:
                continue
            if self._is_my_ball(n):
                self.current_player.pocketed_balls.append(n)
            elif self._is_their_ball(n):
                self.other_player.pocketed_balls.append(n)

    def _switch_turn(self):
        self.current = 1 - self.current

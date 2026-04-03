"""
공의 이동, 충돌, 마찰, 포켓 감지를 담당하는 물리 엔진.
충돌 이벤트를 반환하여 사운드 시스템과 연동.
"""
import math
import random
import sys
import os
from dataclasses import dataclass
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from config import (
    TABLE_X, TABLE_Y, TABLE_W, TABLE_H,
    BALL_RADIUS, POCKETS, POCKET_RADIUS,
    FRICTION_DAMPING, CUSHION_RESTITUTION,
    BALL_RESTITUTION, MIN_SPEED, PHYSICS_SUBSTEPS,
)


@dataclass
class CollisionEvent:
    """충돌 이벤트 — 사운드 재생에 사용."""
    kind: str       # "ball_hit" | "wall_hit"
    speed: float    # 상대 속도 (px/s)


class Ball:
    """물리 상태 + 타입 정보를 가진 당구공."""

    def __init__(self, number: int, x: float, y: float):
        self.number   = number
        self.x        = float(x)
        self.y        = float(y)
        self.vx       = 0.0
        self.vy       = 0.0
        self.radius   = BALL_RADIUS
        self.pocketed = False
        self.rot_x    = random.uniform(0, math.pi * 2)  # 3D 구체 회전 X축 (라디안)
        self.rot_y    = random.uniform(0, math.pi * 2)  # 3D 구체 회전 Y축 (라디안)
        self.show_number = True   # False면 숫자 안 그림 (캐롬용)
        self._color      = None  # 색상 오버라이드 (캐롬용)

        # 스핀 (큐볼 전용)
        self.spin_x    = 0.0
        self.spin_y    = 0.0
        self.spin_power = 0.0
        self.shot_dir_x = 0.0
        self.shot_dir_y = 0.0
        self.pocket_pos = None    # 포켓된 위치 (px, py)

        if number == 0:
            self.group = "cue"
        elif 1 <= number <= 7:
            self.group = "solid"
        elif number == 8:
            self.group = "eight"
        else:
            self.group = "stripe"

    @property
    def speed(self) -> float:
        return math.hypot(self.vx, self.vy)

    @property
    def is_moving(self) -> bool:
        return not self.pocketed and self.speed > MIN_SPEED

    def place(self, x: float, y: float):
        self.x  = float(x)
        self.y  = float(y)
        self.vx = 0.0
        self.vy = 0.0
        self.pocketed = False

    def shoot(self, angle_rad: float, power: float,
              spin_x: float = 0.0, spin_y: float = 0.0):
        self.vx = math.cos(angle_rad) * power
        self.vy = math.sin(angle_rad) * power
        self.spin_x = spin_x
        self.spin_y = spin_y
        self.spin_power = math.hypot(spin_x, spin_y)
        self.shot_dir_x = math.cos(angle_rad)
        self.shot_dir_y = math.sin(angle_rad)

    def to_dict(self) -> dict:
        return {
            "n": self.number,
            "x": round(self.x, 2),
            "y": round(self.y, 2),
            "vx": round(self.vx, 2),
            "vy": round(self.vy, 2),
            "pocketed": self.pocketed,
            "rx": round(self.rot_x, 3),
            "ry": round(self.rot_y, 3),
        }

    @classmethod
    def from_dict(cls, d: dict) -> "Ball":
        b = cls(d["n"], d["x"], d["y"])
        b.vx       = d.get("vx", 0.0)
        b.vy       = d.get("vy", 0.0)
        b.pocketed = d.get("pocketed", False)
        b.rot_x    = d.get("rx", b.rot_x)
        b.rot_y    = d.get("ry", b.rot_y)
        return b


class Physics:
    """공들의 물리 시뮬레이션."""

    def __init__(self, has_pockets=True):
        r = BALL_RADIUS
        self._left   = TABLE_X + r
        self._right  = TABLE_X + TABLE_W - r
        self._top    = TABLE_Y + r
        self._bottom = TABLE_Y + TABLE_H - r
        self.has_pockets = has_pockets
        # 캐롬 추적
        self._track_cue = -1
        self.cushion_hits = 0
        self.ball_contacts = set()
        # 충돌 이벤트 (사운드용)
        self.collision_events: list[CollisionEvent] = []

    def start_shot(self, cue_number: int):
        """샷 시작 시 추적 초기화 (캐롬용)."""
        self._track_cue = cue_number
        self.cushion_hits = 0
        self.ball_contacts = set()

    def step(self, balls: list[Ball], dt: float) -> list[int]:
        self.collision_events.clear()
        sub_dt = dt / PHYSICS_SUBSTEPS
        for _ in range(PHYSICS_SUBSTEPS):
            for b in balls:
                if b.pocketed:
                    continue
                b.x += b.vx * sub_dt
                b.y += b.vy * sub_dt
                # 3D 구체 회전 (이동 방향에 따라 구르기)
                spd = b.speed
                if spd > MIN_SPEED:
                    angular = sub_dt / b.radius
                    b.rot_x -= b.vy * angular
                    b.rot_y += b.vx * angular
            self._wall_collisions(balls)
            self._ball_collisions(balls)

        self._apply_friction(balls, dt)
        return self._check_pockets(balls)

    def any_moving(self, balls: list[Ball]) -> bool:
        return any(b.is_moving for b in balls)

    # ── 벽 충돌 ────────────────────────────────────────

    def _wall_collisions(self, balls):
        for b in balls:
            if b.pocketed:
                continue

            # 포켓 근처에서는 벽 충돌 무시 (포켓 모드만)
            if self.has_pockets:
                near_pocket = False
                for px, py in POCKETS:
                    if math.hypot(b.x - px, b.y - py) < POCKET_RADIUS + b.radius:
                        near_pocket = True
                        break
                if near_pocket:
                    continue

            spin_kick = b.spin_x * b.spin_power * 25 if b.number == self._track_cue or (self._track_cue == -1 and b.number == 0) else 0
            hits = 0
            pre_speed = b.speed

            if b.x < self._left:
                b.x  = self._left
                b.vx = abs(b.vx) * CUSHION_RESTITUTION
                b.vy += spin_kick
                hits += 1
            elif b.x > self._right:
                b.x  = self._right
                b.vx = -abs(b.vx) * CUSHION_RESTITUTION
                b.vy -= spin_kick
                hits += 1

            if b.y < self._top:
                b.y  = self._top
                b.vy = abs(b.vy) * CUSHION_RESTITUTION
                b.vx -= spin_kick
                hits += 1
            elif b.y > self._bottom:
                b.y  = self._bottom
                b.vy = -abs(b.vy) * CUSHION_RESTITUTION
                b.vx += spin_kick
                hits += 1

            # 캐롬 쿠션 추적
            if hits > 0 and b.number == self._track_cue:
                self.cushion_hits += hits
            # 충돌 이벤트 기록
            if hits > 0 and pre_speed > MIN_SPEED * 3:
                self.collision_events.append(
                    CollisionEvent("wall_hit", pre_speed)
                )

    # ── 공 간 충돌 ─────────────────────────────────────

    def _ball_collisions(self, balls):
        n = len(balls)
        for i in range(n):
            for j in range(i + 1, n):
                b1, b2 = balls[i], balls[j]
                if b1.pocketed or b2.pocketed:
                    continue
                dx   = b2.x - b1.x
                dy   = b2.y - b1.y
                dist = math.hypot(dx, dy)
                min_d = b1.radius + b2.radius
                if dist < min_d and dist > 1e-6:
                    nx  = dx / dist
                    ny  = dy / dist
                    # 겹침 해소
                    ovr = (min_d - dist) * 0.5
                    b1.x -= nx * ovr
                    b1.y -= ny * ovr
                    b2.x += nx * ovr
                    b2.y += ny * ovr
                    # 충격량 계산 (동일 질량 탄성 충돌)
                    dot = (b1.vx - b2.vx) * nx + (b1.vy - b2.vy) * ny
                    if dot > 0:
                        imp = dot * BALL_RESTITUTION
                        b1.vx -= imp * nx
                        b1.vy -= imp * ny
                        b2.vx += imp * nx
                        b2.vy += imp * ny
                        # 캐롬 접촉 추적
                        if b1.number == self._track_cue:
                            self.ball_contacts.add(b2.number)
                        elif b2.number == self._track_cue:
                            self.ball_contacts.add(b1.number)
                        # 충돌 이벤트 기록
                        rel_speed = math.hypot(
                            b1.vx - b2.vx, b1.vy - b2.vy
                        )
                        if rel_speed > MIN_SPEED * 2:
                            self.collision_events.append(
                                CollisionEvent("ball_hit", rel_speed)
                            )

    # ── 마찰 + 스핀 ───────────────────────────────────

    def _apply_friction(self, balls, dt: float):
        # 웹 풀 스타일 마찰: 일정 비율 감속 → 임계값 이하 즉시 정지
        factor = FRICTION_DAMPING ** (dt * 60)
        for b in balls:
            if b.pocketed:
                continue

            b.vx *= factor
            b.vy *= factor

            # 큐볼 스핀 (스핀은 유지)
            if b.number == 0 and b.spin_power > 0.02:
                follow = -b.spin_y * 120 * dt * b.spin_power
                b.vx += b.shot_dir_x * follow
                b.vy += b.shot_dir_y * follow
                side = b.spin_x * 60 * dt * b.spin_power
                b.vx += -b.shot_dir_y * side
                b.vy +=  b.shot_dir_x * side
                b.spin_power *= 0.95 ** (dt * 60)
                if b.spin_power < 0.02:
                    b.spin_power = 0.0

            # 깔끔한 정지 (질질 끌리지 않음)
            if b.speed < MIN_SPEED:
                b.vx = 0.0
                b.vy = 0.0

    # ── 포켓 감지 ──────────────────────────────────────

    def _check_pockets(self, balls) -> list[int]:
        if not self.has_pockets:
            return []
        pocketed = []
        for b in balls:
            if b.pocketed:
                continue
            for px, py in POCKETS:
                if math.hypot(b.x - px, b.y - py) < POCKET_RADIUS + b.radius * 0.4:
                    b.pocketed = True
                    b.pocket_pos = (px, py)
                    b.vx = 0.0
                    b.vy = 0.0
                    pocketed.append(b.number)
                    break
        return pocketed

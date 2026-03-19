"""World boss finite-state machine."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class WorldBossState(str, Enum):
    RESET_DUE = "reset_due"
    ALIVE = "alive"
    DEFEATED = "defeated"


@dataclass
class WorldBossSnapshot:
    hp: int
    max_hp: int
    last_reset: int
    now_ts: int
    day_start_ts: int

    @classmethod
    def from_row(cls, row, *, now_ts: int, day_start_ts: int) -> "WorldBossSnapshot":
        data = dict(row or {})
        return cls(
            hp=int(data.get("hp", 0) or 0),
            max_hp=int(data.get("max_hp", 0) or 0),
            last_reset=int(data.get("last_reset", 0) or 0),
            now_ts=int(now_ts or 0),
            day_start_ts=int(day_start_ts or 0),
        )


class WorldBossFSM:
    """Simple FSM for world boss lifecycle."""

    def __init__(self, snapshot: WorldBossSnapshot):
        self.snapshot = snapshot
        self.state = self._derive_state(snapshot)

    @staticmethod
    def _derive_state(snapshot: WorldBossSnapshot) -> WorldBossState:
        if snapshot.last_reset < snapshot.day_start_ts:
            return WorldBossState.RESET_DUE
        if snapshot.hp <= 0:
            return WorldBossState.DEFEATED
        return WorldBossState.ALIVE

    def should_daily_reset(self) -> bool:
        return self.state == WorldBossState.RESET_DUE

    def can_attack(self) -> bool:
        return self.state == WorldBossState.ALIVE

    def apply_daily_reset(self) -> None:
        self.snapshot.hp = int(self.snapshot.max_hp)
        self.snapshot.last_reset = int(self.snapshot.now_ts)
        self.state = WorldBossState.ALIVE

    def apply_damage(self, damage: int) -> int:
        dmg = max(0, int(damage or 0))
        self.snapshot.hp = max(0, int(self.snapshot.hp) - dmg)
        self.state = WorldBossState.DEFEATED if self.snapshot.hp <= 0 else WorldBossState.ALIVE
        return int(self.snapshot.hp)

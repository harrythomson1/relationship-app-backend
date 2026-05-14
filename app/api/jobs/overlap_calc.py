"""Port of the frontend overlap calculation.

A user's awake window is [wake_start, wake_end) in minutes from local midnight.
The window wraps midnight when wake_end <= wake_start (night-owl case).
"""

from dataclasses import dataclass
from datetime import datetime
from zoneinfo import ZoneInfo

MINUTES_PER_DAY = 1440


@dataclass(frozen=True)
class UserSchedule:
    time_zone: str
    wake_start: int
    wake_end: int


@dataclass(frozen=True)
class OverlapStatus:
    state: str  # "active" | "upcoming"
    minutes_until_open: int | None = None
    minutes_remaining: int | None = None


def _local_minutes(now_utc: datetime, tz: str) -> int:
    local = now_utc.astimezone(ZoneInfo(tz))
    return local.hour * 60 + local.minute


def _is_awake(now: int, start: int, end: int) -> bool:
    if start < end:
        return start <= now < end
    return now >= start or now < end


def _effective_end(now: int, start: int, end: int) -> int:
    if start < end:
        return end
    return end + MINUTES_PER_DAY if now >= start else end


def _next_start(now: int, start: int) -> int:
    return start if start >= now else start + MINUTES_PER_DAY


def calculate_overlap(now_utc: datetime, a: UserSchedule, b: UserSchedule) -> OverlapStatus:
    a_now = _local_minutes(now_utc, a.time_zone)
    b_now = _local_minutes(now_utc, b.time_zone)

    a_awake = _is_awake(a_now, a.wake_start, a.wake_end)
    b_awake = _is_awake(b_now, b.wake_start, b.wake_end)

    if a_awake and b_awake:
        a_end = _effective_end(a_now, a.wake_start, a.wake_end)
        b_end = _effective_end(b_now, b.wake_start, b.wake_end)
        return OverlapStatus(state="active", minutes_remaining=min(a_end - a_now, b_end - b_now))

    a_until = 0 if a_awake else _next_start(a_now, a.wake_start) - a_now
    b_until = 0 if b_awake else _next_start(b_now, b.wake_start) - b_now
    return OverlapStatus(state="upcoming", minutes_until_open=max(a_until, b_until))

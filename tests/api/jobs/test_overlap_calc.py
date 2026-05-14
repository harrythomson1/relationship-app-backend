from datetime import UTC, datetime

from app.api.jobs.overlap_calc import UserSchedule, calculate_overlap


def at(year, month, day, hour, minute=0):
    return datetime(year, month, day, hour, minute, tzinfo=UTC)


class TestCalculateOverlap:
    def test_both_awake_returns_active(self):
        # 13:00 UTC. Both in UTC, both awake 09:00-22:00.
        status = calculate_overlap(
            at(2026, 1, 1, 13),
            UserSchedule(time_zone="UTC", wake_start=9 * 60, wake_end=22 * 60),
            UserSchedule(time_zone="UTC", wake_start=9 * 60, wake_end=22 * 60),
        )
        assert status.state == "active"
        assert status.minutes_remaining == 9 * 60

    def test_one_asleep_returns_upcoming(self):
        # 13:00 UTC.
        # A (UTC): awake 09-22 -> awake now.
        # B (UTC+8 == Asia/Singapore): local 21:00, awake 09-22 -> awake but ends in 1h.
        # B will sleep at 22:00 local = 14:00 UTC. A wakes again at 09 UTC tomorrow.
        # If A is asleep at 08:00 UTC: A wakes at 09:00 UTC (60 min). B local 16:00, awake.
        status = calculate_overlap(
            at(2026, 1, 1, 8),
            UserSchedule(time_zone="UTC", wake_start=9 * 60, wake_end=22 * 60),
            UserSchedule(time_zone="Asia/Singapore", wake_start=9 * 60, wake_end=22 * 60),
        )
        assert status.state == "upcoming"
        assert status.minutes_until_open == 60

    def test_both_asleep_window_opens_at_later_waker(self):
        # 04:00 UTC.
        # A (UTC): wakes at 09 -> 300 min away.
        # B (UTC-5 == America/New_York): local 23:00 previous day; wakes at 06 local
        #   = 11:00 UTC -> 420 min away.
        status = calculate_overlap(
            at(2026, 1, 1, 4),
            UserSchedule(time_zone="UTC", wake_start=9 * 60, wake_end=22 * 60),
            UserSchedule(time_zone="America/New_York", wake_start=6 * 60, wake_end=22 * 60),
        )
        assert status.state == "upcoming"
        assert status.minutes_until_open == 420

    def test_wraparound_user_awake_just_after_midnight(self):
        # 01:00 UTC. Night-owl A awake 23:00-06:00 local (UTC) -> awake at 01:00.
        # B awake 09-22 -> asleep. Window opens at B's 09:00 -> 480 min.
        status = calculate_overlap(
            at(2026, 1, 1, 1),
            UserSchedule(time_zone="UTC", wake_start=23 * 60, wake_end=6 * 60),
            UserSchedule(time_zone="UTC", wake_start=9 * 60, wake_end=22 * 60),
        )
        assert status.state == "upcoming"
        assert status.minutes_until_open == 8 * 60

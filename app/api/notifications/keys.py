"""Canonical set of notification keys users can toggle.

Keys map to the `type` field we send in push payloads. The test push and any
ad-hoc admin pushes are intentionally not toggleable.
"""

from enum import Enum


class NotificationKey(str, Enum):
    overlap_opening = "overlap_opening"
    countdown_updated = "countdown_updated"


ALL_KEYS: tuple[NotificationKey, ...] = tuple(NotificationKey)

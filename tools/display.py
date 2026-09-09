"""Windows display helpers exposed via a dedicated feature module."""

from tools.system import adjust_brightness, open_settings, set_brightness

__all__ = [
    "set_brightness",
    "adjust_brightness",
    "open_display_settings",
]


def open_display_settings() -> str:
    return open_settings("display")

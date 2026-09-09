"""Windows display helpers exposed via a dedicated feature module."""

from tools.system import (
    adjust_brightness,
    get_audio_device_inventory,
    get_brightness,
    get_display_information,
    get_usb_inventory,
    open_settings,
    set_brightness,
)

__all__ = [
    "set_brightness",
    "adjust_brightness",
    "get_brightness",
    "get_display_information",
    "get_audio_device_inventory",
    "get_usb_inventory",
    "open_display_settings",
]


def open_display_settings() -> str:
    return open_settings("display")

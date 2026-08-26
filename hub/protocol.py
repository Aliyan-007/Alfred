import uuid


# =========================================================
# ALFRED DEVICE COMMAND ACTIONS
# =========================================================

ALLOWED_ACTIONS = {

    # =====================================================
    # CORE
    # =====================================================

    "ping",


    # =====================================================
    # WINDOWS / PC
    # =====================================================

    "open_application",


    # =====================================================
    # BROWSER / WEB
    # =====================================================

    "open_url",
    "web_search",


    # =====================================================
    # SPOTIFY
    # =====================================================

    "play_spotify",
    "spotify_control",


    # =====================================================
    # YOUTUBE
    # =====================================================

    "play_youtube",
    "youtube_control",


    # =====================================================
    # PC VOLUME
    # =====================================================

    "pc_volume_up",
    "pc_volume_down",
    "pc_volume_mute",
    "pc_volume_unmute",


    # =====================================================
    # GMAIL
    # =====================================================

    "draft_email",
    "send_pending_email",


    # =====================================================
    # DOCUMENTS
    # =====================================================

    "save_to_notepad",
    "save_to_word",


    # =====================================================
    # RESEARCH
    # =====================================================

    "research_youtube",


    # =====================================================
    # ANDROID — DEVICE
    # =====================================================

    "battery",
    "device_info",


    # =====================================================
    # ANDROID — APPS
    # =====================================================

    "apps.list",
    "apps.open_app",


    # =====================================================
    # ANDROID — URL
    # =====================================================

    "url.open",


    # =====================================================
    # ANDROID — MEDIA
    # =====================================================

    "media.play",
    "media.pause",
    "media.next",
    "media.previous",
    "media.stop",
    "media.fast_forward",
    "media.rewind",


    # =====================================================
    # ANDROID — VOLUME
    # =====================================================

    "volume.status",
    "volume.up",
    "volume.down",
    "volume.set",
    "volume.mute",


    # =====================================================
    # ANDROID — HARDWARE
    # =====================================================

    "hardware.flashlight_on",
    "hardware.flashlight_off",
    "hardware.vibrate",


    # =====================================================
    # ANDROID — NOTIFICATIONS
    # =====================================================

    "notifications.list",


    # =====================================================
    # ANDROID — CALENDAR
    # =====================================================

    "calendar.list",
    "calendar.search",
    "calendar.create",
    "calendar.reschedule",
    "calendar.cancel",


    # =====================================================
    # ANDROID — ALARMS / TIMERS
    # =====================================================

    "alarms.set_alarm",
    "alarms.set_timer",


    # =====================================================
    # ANDROID — CLIPBOARD
    # =====================================================

    "clipboard.get",
    "clipboard.set",


    # =====================================================
    # ANDROID — SHORTCUTS
    # =====================================================

    "shortcuts.list",
    "shortcuts.run",


    # =====================================================
    # ANDROID — ACCESSIBILITY
    # =====================================================

    "accessibility.back",
    "accessibility.home",
    "accessibility.tap",
    "accessibility.swipe",
    "accessibility.click_text",
}

# =========================================================
# CREATE COMMAND
# =========================================================

def create_command(
    device_id: str,
    action: str,
    parameters=None,
):

    device_id = device_id.strip()

    action = action.strip()


    if not device_id:

        raise ValueError(
            "device_id cannot be empty"
        )


    if not action:

        raise ValueError(
            "action cannot be empty"
        )


    if action not in ALLOWED_ACTIONS:

        raise ValueError(
            f"Unsupported action: {action}"
        )


    if parameters is None:

        parameters = {}


    if not isinstance(
        parameters,
        dict,
    ):

        raise TypeError(
            "parameters must be a dictionary"
        )


    return {
        "id": (
            "cmd_"
            + uuid.uuid4().hex
        ),
        "device": device_id,
        "action": action,
        "parameters": parameters,
    }


# =========================================================
# VALIDATE COMMAND
# =========================================================

def validate_command(
    command,
):

    if not isinstance(
        command,
        dict,
    ):

        return (
            False,
            "Command must be a dictionary.",
        )


    required_fields = (
        "id",
        "device",
        "action",
        "parameters",
    )


    for field in required_fields:

        if field not in command:

            return (
                False,
                f"Missing field: {field}",
            )


    if not isinstance(
        command["id"],
        str,
    ):

        return (
            False,
            "id must be a string.",
        )


    if not isinstance(
        command["device"],
        str,
    ):

        return (
            False,
            "device must be a string.",
        )


    if not isinstance(
        command["action"],
        str,
    ):

        return (
            False,
            "action must be a string.",
        )


    if command["action"] not in ALLOWED_ACTIONS:

        return (
            False,
            f"Unsupported action: "
            f"{command['action']}",
        )


    if not isinstance(
        command["parameters"],
        dict,
    ):

        return (
            False,
            "parameters must be a dictionary.",
        )


    return (
        True,
        "OK",
    )
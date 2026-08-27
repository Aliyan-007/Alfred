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
    # ANDROID — BATTERY / DEVICE
    # =====================================================

    "battery",
    "battery.status",

    "device_info",
    "device_info.status",


    # =====================================================
    # ANDROID — APPS
    # =====================================================

    "apps.list",
    "apps.open",
    "apps.open_app",
    "apps.close",
    "apps.current",


    # =====================================================
    # ANDROID — URL
    # =====================================================

    "url.open",


    # =====================================================
    # ANDROID — PHONE
    # =====================================================

    "phone.dial",
    "phone.call",
    "phone.sms",
    "phone.message",


    # =====================================================
    # ANDROID — MEDIA
    # =====================================================

    "media.play",
    "media.resume",
    "media.pause",
    "media.play_pause",
    "media.toggle",
    "media.next",
    "media.skip",
    "media.previous",
    "media.prev",
    "media.stop",
    "media.fast_forward",
    "media.rewind",
    "media.status",


    # =====================================================
    # ANDROID — VOLUME
    # =====================================================

    "volume.status",
    "volume.up",
    "volume.down",
    "volume.set",
    "volume.mute",
    "volume.unmute",


    # =====================================================
    # ANDROID — HARDWARE
    # =====================================================

    "hardware.flashlight_on",
    "hardware.flashlight_off",
    "hardware.torch_on",
    "hardware.torch_off",
    "hardware.vibrate",
    "hardware.brightness",
    "hardware.status",


    # =====================================================
    # ANDROID — SETTINGS
    # =====================================================

    "settings.wifi_on",
    "settings.wifi_off",
    "settings.enable_wifi",
    "settings.disable_wifi",

    "settings.bluetooth_on",
    "settings.bluetooth_off",
    "settings.enable_bluetooth",
    "settings.disable_bluetooth",

    "settings.airplane_mode",
    "settings.brightness",
    "settings.status",


    # =====================================================
    # ANDROID — NOTIFICATIONS
    # =====================================================

    "notifications.list",
    "notifications.read",
    "notifications.clear",
    "notifications.status",


    # =====================================================
    # ANDROID — CALENDAR
    # =====================================================

    "calendar.list",
    "calendar.search",
    "calendar.create",
    "calendar.reschedule",
    "calendar.cancel",
    "calendar.delete",


    # =====================================================
    # ANDROID — ALARMS / TIMERS
    # =====================================================

    "alarms.set",
    "alarms.create",
    "alarms.list",
    "alarms.cancel",

    "alarms.set_alarm",
    "alarms.set_timer",


    # =====================================================
    # ANDROID — CLIPBOARD
    # =====================================================

    "clipboard.get",
    "clipboard.set",
    "clipboard.clear",


    # =====================================================
    # ANDROID — SHORTCUTS
    # =====================================================

    "shortcuts.list",
    "shortcuts.run",
    "shortcuts.create",
    "shortcuts.delete",


    # =====================================================
    # ANDROID — ACCESSIBILITY
    # =====================================================

    "accessibility.back",
    "accessibility.home",
    "accessibility.recents",
    "accessibility.tap",
    "accessibility.swipe",
    "accessibility.click_text",
    "accessibility.status",
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

        "id":
            "cmd_" + uuid.uuid4().hex,

        "device":
            device_id,

        "action":
            action,

        "parameters":
            parameters,

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
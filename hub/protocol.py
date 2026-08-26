import uuid


# =========================================================
# ALFRED DEVICE COMMAND ACTIONS
# =========================================================

ALLOWED_ACTIONS = {
    # Core
    "ping",

    # Windows
    "open_application",

    # Browser / Web
    "open_url",
    "web_search",

    # Spotify
    "play_spotify",
    "spotify_control",

    # YouTube
    "play_youtube",
    "youtube_control",

    # Volume
    "pc_volume_up",
    "pc_volume_down",
    "pc_volume_mute",
    "pc_volume_unmute",

    # Gmail
    "draft_email",
    "send_pending_email",

    # Documents
    "save_to_notepad",
    "save_to_word",

    # Research
    "research_youtube",
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
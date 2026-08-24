import uuid

# =========================================================
# COMMAND ACTIONS
# =========================================================

ALLOWED_ACTIONS = {
    "ping",
    "open_application",
    "open_url",
    "play_media",
    "pause_media",
    "next_media",
    "previous_media",
    "search_web",
    "find_file",
    "open_file",
    "get_battery",
    "send_notification",
}


# =========================================================
# CREATE COMMAND
# =========================================================

def create_command(
    device_id: str,
    action: str,
    parameters=None,
):
    """
    Create a standard ALFRED command.
    """

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
    """
    Check whether a command follows the ALFRED protocol.

    Returns:
        (True, "OK")
    or:
        (False, "reason")
    """

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
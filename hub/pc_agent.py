import asyncio
import json

import websockets

from tools.ai_tools import execute_tool


# =========================================================
# CONFIGURATION
# =========================================================

HUB_URL = (
    "ws://127.0.0.1:8765"
)

DEVICE_ID = "pc_01"
DEVICE_NAME = "My PC"
DEVICE_TYPE = "pc"


# =========================================================
# PC CAPABILITIES
# =========================================================

CAPABILITIES = [
    "ping",
    "open_application",
    "open_url",
    "web_search",
    "play_spotify",
    "spotify_control",
    "play_youtube",
    "youtube_control",
    "pc_volume_up",
    "pc_volume_down",
    "pc_volume_mute",
    "pc_volume_unmute",
    "draft_email",
    "send_pending_email",
    "save_to_notepad",
    "save_to_word",
    "research_youtube",
]


# =========================================================
# DEVICE ACTION -> EXISTING ALFRED TOOL
# =========================================================

TOOL_MAP = {
    "open_application":
        "open_application",

    "open_url":
        "open_webpage",

    "web_search":
        "web_search",

    "play_spotify":
        "play_spotify",

    "spotify_control":
        "spotify_control",

    "play_youtube":
        "play_youtube",

    "youtube_control":
        "youtube_control",

    "pc_volume_up":
        "pc_volume_up",

    "pc_volume_down":
        "pc_volume_down",

    "pc_volume_mute":
        "pc_volume_mute",

    "pc_volume_unmute":
        "pc_volume_unmute",

    "draft_email":
        "draft_email",

    "send_pending_email":
        "send_pending_email",

    "save_to_notepad":
        "save_to_notepad",

    "save_to_word":
        "save_to_word",

    "research_youtube":
        "research_youtube",
}


# =========================================================
# PARAMETER TRANSLATION
# =========================================================

def translate_parameters(
    action,
    parameters,
):
    parameters = dict(
        parameters
    )

    # -----------------------------------------------------
    # OPEN APPLICATION
    # -----------------------------------------------------

    if action == "open_application":

        if (
            "name" in parameters
            and "application" not in parameters
        ):

            parameters[
                "application"
            ] = parameters.pop(
                "name"
            )

    return parameters

# =========================================================
# SEND JSON
# =========================================================

async def send_json(
    websocket,
    data,
):
    await websocket.send(
        json.dumps(
            data,
            ensure_ascii=False,
        )
    )


# =========================================================
# EXECUTE COMMAND
# =========================================================

def execute_command(
    command,
):
    command_id = command.get(
        "id"
    )

    action = command.get(
        "action"
    )

    parameters = command.get(
        "parameters",
        {},
    )

    if not isinstance(
        parameters,
        dict,
    ):
        parameters = {}

    print(
        f"[PC AGENT] Action: {action}"
    )

    print(
        f"[PC AGENT] Parameters: {parameters}"
    )

    # =====================================================
    # PING
    # =====================================================

    if action == "ping":

        return {
            "type": "command_result",
            "id": command_id,
            "device": DEVICE_ID,
            "success": True,
            "result": "pong",
        }

    # =====================================================
    # FIND EXISTING ALFRED TOOL
    # =====================================================

    tool_name = TOOL_MAP.get(
        action
    )

    if not tool_name:

        return {
            "type": "command_result",
            "id": command_id,
            "device": DEVICE_ID,
            "success": False,
            "error": {
                "code": "unsupported_action",
                "message": (
                    f"PC Agent does not support "
                    f"'{action}'."
                ),
            },
        }
    parameters = translate_parameters( 
        action, 
        parameters, 
    ) 
    print( 
        f"[PC AGENT] Translated parameters: {parameters}" 
        )

    # =====================================================
    # EXECUTE EXISTING TOOL
    # =====================================================

    try:

        result = execute_tool(
            tool_name,
            parameters,
        )

        # -------------------------------------------------
        # Existing ALFRED tools can report failure by
        # returning a string rather than raising an error.
        # -------------------------------------------------

        if (
            isinstance(
                result,
                str,
            )
            and result.startswith(
                "Tool '"
            )
            and " failed:" in result
        ):

            return {
                "type": "command_result",
                "id": command_id,
                "device": DEVICE_ID,
                "success": False,
                "error": {
                    "code": (
                        "tool_execution_failed"
                    ),
                    "message": result,
                },
            }

        # -------------------------------------------------
        # Successful tool execution
        # -------------------------------------------------

        return {
            "type": "command_result",
            "id": command_id,
            "device": DEVICE_ID,
            "success": True,
            "result": result,
        }

    except Exception as error:

        print(
            "[PC AGENT ERROR]",
            error,
        )

        return {
            "type": "command_result",
            "id": command_id,
            "device": DEVICE_ID,
            "success": False,
            "error": {
                "code": "execution_error",
                "message": str(error),
            },
        }


# =========================================================
# CONNECT TO HUB
# =========================================================

async def main():

    print()
    print(
        "=" * 60
    )
    print(
        "                   PC AGENT"
    )
    print(
        "=" * 60
    )
    print()

    print(
        f"[PC AGENT] Connecting to {HUB_URL}"
    )

    async with websockets.connect(
        HUB_URL
    ) as websocket:

        print(
            "[PC AGENT] Connected."
        )

        # -------------------------------------------------
        # REGISTER DEVICE
        # -------------------------------------------------

        registration = {
            "type": "register",
            "device_id": DEVICE_ID,
            "name": DEVICE_NAME,
            "device_type": DEVICE_TYPE,
            "capabilities": CAPABILITIES,
        }

        await send_json(
            websocket,
            registration,
        )

        print(
            "[PC AGENT] Registration sent."
        )

        response = await websocket.recv()

        print(
            "[PC AGENT] Hub response:",
            response,
        )

        print()
        print(
            "[PC AGENT] Waiting for commands..."
        )
        print()

        # -------------------------------------------------
        # COMMAND LOOP
        # -------------------------------------------------

        async for message in websocket:

            print(
                "[PC AGENT] Received:",
                message,
            )

            try:

                data = json.loads(
                    message
                )

            except json.JSONDecodeError:

                print(
                    "[PC AGENT] Invalid JSON."
                )

                continue

            if data.get(
                "type"
            ) != "command":

                continue

            command = data.get(
                "command",
                {},
            )

            # -------------------------------------------------
            # Execute command
            # -------------------------------------------------

            result = execute_command(
                command
            )

            # -------------------------------------------------
            # Return result to Hub
            # -------------------------------------------------

            await send_json(
                websocket,
                result,
            )

            print(
                "[PC AGENT] Result:",
                result,
            )

            print()


# =========================================================
# ENTRY POINT
# =========================================================

if __name__ == "__main__":

    try:

        asyncio.run(
            main()
        )

    except KeyboardInterrupt:

        print()
        print(
            "[PC AGENT] Shutdown."
        )

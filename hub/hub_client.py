import asyncio
import json
import uuid

import websockets


# =========================================================
# CONFIGURATION
# =========================================================

HUB_URL = (
    "ws://127.0.0.1:8765"
)


# =========================================================
# SEND COMMAND
# =========================================================

async def send_command_async(
    device,
    action,
    parameters=None,
    timeout=30,
):
    if parameters is None:

        parameters = {}

    command_id = (
        "cmd_"
        + uuid.uuid4().hex
    )

    command = {
        "id": command_id,
        "device": device,
        "action": action,
        "parameters": parameters,
    }

    try:

        async with websockets.connect(
            HUB_URL
        ) as websocket:

            print(
                "[HUB CLIENT] Connected."
            )

            message = {
                "type": "command",
                "command": command,
            }

            await websocket.send(
                json.dumps(
                    message,
                    ensure_ascii=False,
                )
            )

            print(
                "[HUB CLIENT] Sent:",
                command,
            )

            while True:

                response = await asyncio.wait_for(
                    websocket.recv(),
                    timeout=timeout,
                )

                data = json.loads(
                    response
                )

                if (
                    data.get("type")
                    == "command_result"
                    and data.get("id")
                    == command_id
                ):

                    return data

    except asyncio.TimeoutError:

        return {
            "success": False,
            "error": {
                "code": "timeout",
                "message": (
                    "The device did not respond "
                    "in time."
                ),
            },
        }

    except Exception as error:

        return {
            "success": False,
            "error": {
                "code": "hub_connection_error",
                "message": str(error),
            },
        }


# =========================================================
# SYNCHRONOUS WRAPPER
# =========================================================

def send_command(
    device,
    action,
    parameters=None,
    timeout=30,
):
    return asyncio.run(
        send_command_async(
            device=device,
            action=action,
            parameters=parameters,
            timeout=timeout,
        )
    )

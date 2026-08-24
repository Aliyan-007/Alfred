import asyncio
import json

import websockets
from protocol import validate_command


# =========================================================
# CONFIGURATION
# =========================================================

HOST = "127.0.0.1"
PORT = 8765


# =========================================================
# CONNECTED DEVICES
# =========================================================

connected_devices = {}


# =========================================================
# SEND JSON
# =========================================================

async def send_json(
    websocket,
    data,
):
    message = json.dumps(
        data,
        ensure_ascii=False,
    )

    await websocket.send(
        message
    )


# =========================================================
# CLIENT HANDLER
# =========================================================

async def handle_client(
    websocket,
):
    device_id = None

    print(
        "[HUB] Client connected."
    )

    try:

        async for message in websocket:

            print(
                f"[HUB] Received: {message}"
            )

            try:

                data = json.loads(
                    message
                )

            except json.JSONDecodeError:

                await send_json(
                    websocket,
                    {
                        "type": "error",
                        "message": (
                            "Invalid JSON."
                        ),
                    },
                )

                continue

            message_type = data.get(
                "type"
            )

            # =================================================
            # REGISTER DEVICE
            # =================================================

            if message_type == "register":

                device_id = data.get(
                    "device_id"
                )

                if not device_id:

                    await send_json(
                        websocket,
                        {
                            "type": "error",
                            "message": (
                                "device_id is required."
                            ),
                        },
                    )

                    continue

                connected_devices[
                    device_id
                ] = {
                    "websocket": websocket,
                    "name": data.get(
                        "name",
                        device_id,
                    ),
                    "type": data.get(
                        "device_type",
                        "unknown",
                    ),
                    "capabilities": data.get(
                        "capabilities",
                        [],
                    ),
                }

                print(
                    "[HUB] Registered device:",
                    device_id,
                )

                await send_json(
                    websocket,
                    {
                        "type": "registered",
                        "device_id": device_id,
                    },
                )

            # =================================================
            # PING
            # =================================================

            elif message_type == "ping":

                await send_json(
                    websocket,
                    {
                        "type": "pong"
                    },
                )
                        # =================================================
            # ROUTE COMMAND
            # =================================================

            elif message_type == "command":

                command = data.get(
                    "command"
                )

                valid, reason = validate_command(
                    command
                )

                if not valid:

                    await send_json(
                        websocket,
                        {
                            "type": "command_result",
                            "id": (
                                command.get("id")
                                if isinstance(command, dict)
                                else None
                            ),
                            "success": False,
                            "error": reason,
                        },
                    )

                    continue

                target_device = command[
                    "device"
                ]

                target = connected_devices.get(
                    target_device
                )

                if not target:

                    await send_json(
                        websocket,
                        {
                            "type": "command_result",
                            "id": command["id"],
                            "success": False,
                            "error": (
                                f"Device '{target_device}' "
                                "is not connected."
                            ),
                        },
                    )

                    continue

                print(
                    "[HUB] Routing command:",
                    command,
                )

                await send_json(
                    target["websocket"],
                    {
                        "type": "command",
                        "command": command,
                    },
                )
            # =================================================
            # UNKNOWN MESSAGE
            # =================================================

            else:

                await send_json(
                    websocket,
                    {
                        "type": "error",
                        "message": (
                            f"Unknown message type: "
                            f"{message_type}"
                        ),
                    },
                )

    except websockets.exceptions.ConnectionClosed:

        print(
            "[HUB] Client disconnected."
        )

    except Exception as error:

        print(
            "[HUB] Client error:",
            error,
        )

    finally:

        if device_id:

            existing = connected_devices.get(
                device_id
            )

            if (
                existing
                and existing.get(
                    "websocket"
                )
                is websocket
            ):

                del connected_devices[
                    device_id
                ]

            print(
                "[HUB] Device offline:",
                device_id,
            )


# =========================================================
# START SERVER
# =========================================================

async def main():

    print()
    print(
        "=" * 60
    )
    print(
        "                 ALFRED HUB"
    )
    print(
        "=" * 60
    )
    print()

    print(
        f"[HUB] Listening on ws://{HOST}:{PORT}"
    )

    async with websockets.serve(
        handle_client,
        HOST,
        PORT,
    ):

        print(
            "[HUB] Ready."
        )

        await asyncio.Future()


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
            "[HUB] Shutdown."
        )

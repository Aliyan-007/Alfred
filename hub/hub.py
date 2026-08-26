import asyncio
import json

import websockets

from .protocol import validate_command


# =========================================================
# CONFIGURATION
# =========================================================

HOST = "0.0.0.0"
PORT = 8765


# =========================================================
# CONNECTED DEVICES
# =========================================================

connected_devices = {}

# Maps command_id -> originating websocket.
# This allows the Hub to return a device result to the
# client that originally requested the command.
pending_commands = {}


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

            # -------------------------------------------------
            # Parse JSON
            # -------------------------------------------------

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

            if not isinstance(
                data,
                dict,
            ):

                await send_json(
                    websocket,
                    {
                        "type": "error",
                        "message": (
                            "Message must be a JSON object."
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

                device_id = (
                    data.get(
                        "device_id"
                    )
                    or ""
                ).strip()

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

                # If the same device ID was previously
                # connected through another socket, replace it.
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
                        "type": "pong",
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

                    command_id = None

                    if isinstance(
                        command,
                        dict,
                    ):

                        command_id = command.get(
                            "id"
                        )

                    await send_json(
                        websocket,
                        {
                            "type": "command_result",
                            "id": command_id,
                            "success": False,
                            "error": reason,
                        },
                    )

                    continue

                command_id = command[
                    "id"
                ]

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
                            "id": command_id,
                            "device": target_device,
                            "success": False,
                            "error": (
                                f"Device '{target_device}' "
                                "is not connected."
                            ),
                        },
                    )

                    continue

                # Remember who requested the command.
                pending_commands[
                    command_id
                ] = websocket

                print(
                    "[HUB] Routing command:",
                    command,
                )

                try:

                    await send_json(
                        target["websocket"],
                        {
                            "type": "command",
                            "command": command,
                        },
                    )

                except Exception as error:

                    # Remove the pending request because
                    # delivery failed.
                    pending_commands.pop(
                        command_id,
                        None,
                    )

                    await send_json(
                        websocket,
                        {
                            "type": "command_result",
                            "id": command_id,
                            "device": target_device,
                            "success": False,
                            "error": {
                                "code": "delivery_failed",
                                "message": str(error),
                            },
                        },
                    )

            # =================================================
            # COMMAND RESULT
            # =================================================

            elif message_type == "command_result":

                command_id = data.get(
                    "id"
                )

                if not command_id:

                    print(
                        "[HUB] Command result without ID."
                    )

                    continue

                requester = pending_commands.pop(
                    command_id,
                    None,
                )

                if requester is not None:

                    await send_json(
                        requester,
                        data,
                    )

                    print(
                        "[HUB] Returned result for command:",
                        command_id,
                    )

                else:

                    print(
                        "[HUB] No requester found for command:",
                        command_id,
                    )
            # =================================================
            # GET CONNECTED DEVICES
            # =================================================

            elif message_type == "get_devices":

                devices = []

                for current_device_id, device in connected_devices.items():

                    devices.append(
                        {
                            "device_id": current_device_id,
                            "name": device.get(
                                "name"
                            ),
                            "device_type": device.get(
                                "type"
                            ),
                            "capabilities": device.get(
                                "capabilities",
                                [],
                            ),
                        }
                    )

                await send_json(
                    websocket,
                    {
                        "type": "devices",
                        "devices": devices,
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

        # -----------------------------------------------------
        # Remove device registration only if this websocket
        # is still the active connection for that device.
        # -----------------------------------------------------

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

        # -----------------------------------------------------
        # Clean up commands that were waiting on this
        # disconnected requester.
        # -----------------------------------------------------

        stale_command_ids = [
            command_id
            for command_id, requester in pending_commands.items()
            if requester is websocket
        ]

        for command_id in stale_command_ids:

            pending_commands.pop(
                command_id,
                None,
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

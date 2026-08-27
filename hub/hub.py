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

    print(
        "[HUB] Sending:",
        message,
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

    print()
    print(
        "[HUB] Client connected:",
        id(websocket),
    )

    try:

        async for message in websocket:

            print()
            print(
                f"[HUB] Received from "
                f"{device_id or 'unregistered'}:"
            )

            print(
                message
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
                        "message": "Invalid JSON.",
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
                            "Message must be "
                            "a JSON object."
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


                # If another connection already exists
                # for this device, show it clearly.
                old_device = (
                    connected_devices.get(
                        device_id
                    )
                )

                if old_device:

                    print()
                    print(
                        "[HUB] WARNING: Replacing "
                        "existing device connection:"
                    )

                    print(
                        "[HUB] Device:",
                        device_id,
                    )

                    print(
                        "[HUB] Old socket:",
                        id(
                            old_device[
                                "websocket"
                            ]
                        ),
                    )

                    print(
                        "[HUB] New socket:",
                        id(
                            websocket
                        ),
                    )


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


                print()
                print(
                    "[HUB] Registered device:",
                    device_id,
                )

                print(
                    "[HUB] WebSocket:",
                    id(websocket),
                )

                print(
                    "[HUB] Capabilities:",
                    data.get(
                        "capabilities",
                        [],
                    ),
                )


                await send_json(
                    websocket,
                    {
                        "type": "registered",
                        "device_id": device_id,
                    },
                )

                continue


            # =================================================
            # PING
            # =================================================

            if message_type == "ping":

                await send_json(
                    websocket,
                    {
                        "type": "pong",
                    },
                )

                continue


            # =================================================
            # ROUTE COMMAND
            # =================================================

            if message_type == "command":

                command = data.get(
                    "command"
                )


                print()
                print(
                    "=" * 60
                )

                print(
                    "[HUB] COMMAND RECEIVED"
                )

                print(
                    "=" * 60
                )

                print(
                    json.dumps(
                        command,
                        indent=2,
                        ensure_ascii=False,
                    )
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


                    print(
                        "[HUB] COMMAND INVALID:",
                        reason,
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


                print()

                print(
                    "[HUB] Command ID:",
                    command_id,
                )

                print(
                    "[HUB] Target device:",
                    target_device,
                )

                print(
                    "[HUB] Action:",
                    command.get(
                        "action"
                    ),
                )


                print()

                print(
                    "[HUB] Connected devices:"
                )


                for current_id, current_device in (
                    connected_devices.items()
                ):

                    print(
                        "  -",
                        current_id,
                        "| socket:",
                        id(
                            current_device[
                                "websocket"
                            ]
                        ),
                    )


                target = connected_devices.get(
                    target_device
                )


                if not target:

                    print()

                    print(
                        "[HUB] TARGET DEVICE "
                        "NOT FOUND:",
                        target_device,
                    )


                    await send_json(
                        websocket,
                        {
                            "type": "command_result",

                            "id": command_id,

                            "device": target_device,

                            "success": False,

                            "error": (
                                f"Device "
                                f"'{target_device}' "
                                "is not connected."
                            ),
                        },
                    )

                    continue


                # Remember requester.
                pending_commands[
                    command_id
                ] = websocket


                target_socket = (
                    target[
                        "websocket"
                    ]
                )


                print()

                print(
                    "[HUB] FORWARDING COMMAND"
                )

                print(
                    "[HUB] From socket:",
                    id(websocket),
                )

                print(
                    "[HUB] To device:",
                    target_device,
                )

                print(
                    "[HUB] To socket:",
                    id(target_socket),
                )


                try:

                    await send_json(
                        target_socket,
                        {
                            "type": "command",
                            "command": command,
                        },
                    )


                    print(
                        "[HUB] Command forwarded "
                        "successfully."
                    )


                except Exception as error:

                    pending_commands.pop(
                        command_id,
                        None,
                    )


                    print(
                        "[HUB] DELIVERY FAILED:",
                        error,
                    )


                    await send_json(
                        websocket,
                        {
                            "type": "command_result",

                            "id": command_id,

                            "device": target_device,

                            "success": False,

                            "error": {
                                "code":
                                    "delivery_failed",

                                "message":
                                    str(error),
                            },
                        },
                    )

                continue


            # =================================================
            # COMMAND RESULT
            # =================================================

            if message_type == "command_result":

                command_id = data.get(
                    "id"
                )


                print()

                print(
                    "[HUB] COMMAND RESULT RECEIVED"
                )

                print(
                    "[HUB] From device:",
                    device_id,
                )

                print(
                    "[HUB] Command ID:",
                    command_id,
                )

                print(
                    "[HUB] Result:"
                )

                print(
                    json.dumps(
                        data,
                        indent=2,
                        ensure_ascii=False,
                    )
                )


                if not command_id:

                    print(
                        "[HUB] Command result "
                        "without ID."
                    )

                    continue


                requester = pending_commands.pop(
                    command_id,
                    None,
                )


                if requester is not None:

                    print()

                    print(
                        "[HUB] Returning result "
                        "to requester."
                    )

                    print(
                        "[HUB] Requester socket:",
                        id(requester),
                    )


                    await send_json(
                        requester,
                        data,
                    )

                else:

                    print()

                    print(
                        "[HUB] WARNING: No requester "
                        "found for command:",
                        command_id,
                    )

                continue


            # =================================================
            # GET CONNECTED DEVICES
            # =================================================

            if message_type == "get_devices":

                devices = []


                for (
                    current_device_id,
                    device,
                ) in connected_devices.items():

                    devices.append(
                        {
                            "device_id":
                                current_device_id,

                            "name":
                                device.get(
                                    "name"
                                ),

                            "device_type":
                                device.get(
                                    "type"
                                ),

                            "capabilities":
                                device.get(
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

                continue


            # =================================================
            # UNKNOWN MESSAGE
            # =================================================

            print()

            print(
                "[HUB] UNKNOWN MESSAGE TYPE:",
                message_type,
            )


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

        print()

        print(
            "[HUB] Client disconnected:",
            device_id,
        )


    except Exception as error:

        print()

        print(
            "[HUB] Client error:",
            error,
        )


    finally:

        # -----------------------------------------------------
        # Remove registration only if this exact socket
        # is still the registered socket.
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


                print()

                print(
                    "[HUB] Device offline:",
                    device_id,
                )


        # -----------------------------------------------------
        # Remove stale pending commands.
        # -----------------------------------------------------

        stale_command_ids = [

            command_id

            for command_id, requester in (
                pending_commands.items()
            )

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
        f"[HUB] Listening on "
        f"ws://{HOST}:{PORT}"
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

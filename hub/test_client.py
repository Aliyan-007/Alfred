import asyncio
import json

import websockets


HUB_URL = (
    "ws://127.0.0.1:8765"
)


async def main():

    print(
        f"[CLIENT] Connecting to {HUB_URL}"
    )

    async with websockets.connect(
        HUB_URL
    ) as websocket:

        print(
            "[CLIENT] Connected."
        )

        # -------------------------------------------------
        # REGISTER
        # -------------------------------------------------

        registration = {
            "type": "register",
            "device_id": "pc_01",
            "name": "My PC",
            "device_type": "pc",
            "capabilities": [
                "ping",
                "browser",
                "spotify",
                "youtube",
                "web_search",
                "filesystem",
                "applications",
            ],
        }

        await websocket.send(
            json.dumps(
                registration
            )
        )

        print(
            "[CLIENT] Registration sent."
        )

        response = await websocket.recv()

        print(
            "[CLIENT] Registration response:",
            response,
        )

        # -------------------------------------------------
        # WAIT FOR COMMANDS
        # -------------------------------------------------

        print(
            "[CLIENT] Waiting for commands..."
        )

        async for message in websocket:

            print(
                "[CLIENT] Received:",
                message,
            )

            try:

                data = json.loads(
                    message
                )

            except json.JSONDecodeError:

                print(
                    "[CLIENT] Invalid JSON."
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

            command_id = command.get(
                "id"
            )

            action = command.get(
                "action"
            )

            print(
                "[CLIENT] Command:",
                command,
            )

            # -------------------------------------------------
            # PING
            # -------------------------------------------------

            if action == "ping":

                result = {
                    "type": "command_result",
                    "id": command_id,
                    "success": True,
                    "result": "pong",
                }

                await websocket.send(
                    json.dumps(
                        result
                    )
                )

                print(
                    "[CLIENT] Sent pong."
                )

            else:

                result = {
                    "type": "command_result",
                    "id": command_id,
                    "success": False,
                    "error": (
                        f"Unsupported client action: "
                        f"{action}"
                    ),
                }

                await websocket.send(
                    json.dumps(
                        result
                    )
                )


if __name__ == "__main__":

    asyncio.run(
        main()
    )
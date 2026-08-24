import asyncio
import json

import websockets

from .protocol import create_command


HUB_URL = (
    "ws://127.0.0.1:8765"
)


async def main():

    async with websockets.connect(
        HUB_URL
    ) as websocket:

        command = create_command(
            device_id="pc_01",
            action="ping",
            parameters={},
        )

        message = {
            "type": "command",
            "command": command,
        }

        print(
            "[TEST] Sending:",
            message,
        )

        await websocket.send(
            json.dumps(
                message
            )
        )

        while True:

            response = await websocket.recv()

            print(
                "[TEST] Response:",
                response,
            )

            data = json.loads(
                response
            )

            if (
                data.get("type")
                == "command_result"
                and data.get("id")
                == command["id"]
            ):

                break


if __name__ == "__main__":

    asyncio.run(
        main()
    )
import asyncio
import json
import uuid

import websockets


HUB_URL = "ws://127.0.0.1:8765"

DEVICE_ID = "android_4d05377015b"


async def send_command(action, parameters=None):
    command_id = str(uuid.uuid4())

    command = {
        "id": command_id,
        "device": DEVICE_ID,
        "action": action,
        "parameters": parameters or {},
    }

    message = {
        "type": "command",
        "command": command,
    }

    print()
    print("=" * 60)
    print("ALFRED COMMAND TEST")
    print("=" * 60)
    print()
    print("Connecting to:", HUB_URL)
    print("Target device:", DEVICE_ID)
    print("Action:", action)
    print("Parameters:", json.dumps(parameters or {}))

    async with websockets.connect(HUB_URL) as websocket:

        print()
        print("Sending command...")
        print(json.dumps(message, indent=2))

        await websocket.send(json.dumps(message))

        print()
        print("Waiting for result...")

        while True:
            response = await websocket.recv()

            data = json.loads(response)

            print()
            print("Received:")
            print(json.dumps(data, indent=2))

            if (
                data.get("type") == "command_result"
                and data.get("id") == command_id
            ):
                print()
                print("=" * 60)

                if data.get("success"):
                    print("SUCCESS")
                else:
                    print("FAILED")

                print("=" * 60)

                break


if __name__ == "__main__":
    asyncio.run(
        send_command(
            "battery.status"
        )
    )
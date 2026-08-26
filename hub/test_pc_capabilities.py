import asyncio
import json
import sys

import websockets

from .protocol import create_command


HUB_URL = "ws://127.0.0.1:8765"
DEVICE_ID = "pc_01"


# =========================================================
# TEST COMMANDS
# =========================================================

TESTS = [
    {
        "name": "Ping",
        "action": "ping",
        "parameters": {},
    },

    {
        "name": "Open Notepad",
        "action": "open_application",
        "parameters": {
            "name": "notepad",
        },
    },

    {
        "name": "Open URL",
        "action": "open_url",
        "parameters": {
            "url": "https://www.youtube.com",
        },
    },

    {
        "name": "Web Search",
        "action": "web_search",
        "parameters": {
            "query": "Formula 1",
        },
    },

    {
        "name": "Spotify Playback",
        "action": "play_spotify",
        "parameters": {
            "query": "Charmer",
        },
    },

    {
        "name": "Spotify Control",
        "action": "spotify_control",
        "parameters": {
            "command": "pause",
        },
    },

    {
        "name": "YouTube Playback",
        "action": "play_youtube",
        "parameters": {
            "query": "Formula 1 highlights",
        },
    },

    {
        "name": "YouTube Control",
        "action": "youtube_control",
        "parameters": {
            "command": "pause",
        },
    },

    {
        "name": "Volume Up",
        "action": "pc_volume_up",
        "parameters": {},
    },

    {
        "name": "Volume Down",
        "action": "pc_volume_down",
        "parameters": {},
    },

    {
        "name": "Volume Mute",
        "action": "pc_volume_mute",
        "parameters": {},
    },

    {
        "name": "Volume Unmute",
        "action": "pc_volume_unmute",
        "parameters": {},
    },

    {
        "name": "YouTube Research",
        "action": "research_youtube",
        "parameters": {
            "query": "Formula 1 rules",
            "max_results": 3,
        },
    },

    {
        "name": "Save Word",
        "action": "save_to_word",
        "parameters": {
            "title": "ALFRED PC Agent Test",
        },
    },

    {
        "name": "Save Notepad",
        "action": "save_to_notepad",
        "parameters": {
            "title": "ALFRED PC Agent Test",
        },
    },

    {
        "name": "Gmail Draft",
        "action": "draft_email",
        "parameters": {
            "recipient": "YOUR_EMAIL@gmail.com",
            "subject": "ALFRED PC Agent Test",
            "body": (
                "This is a test draft created "
                "through the ALFRED PC Agent."
            ),
        },
    },
]


# =========================================================
# SEND COMMAND
# =========================================================

async def send_test(
    websocket,
    test,
):
    command = create_command(
        device_id=DEVICE_ID,
        action=test["action"],
        parameters=test["parameters"],
    )

    payload = {
        "type": "command",
        "command": command,
    }

    print()
    print(
        "=" * 70
    )

    print(
        f"TEST: {test['name']}"
    )

    print(
        f"Action: {test['action']}"
    )

    print(
        f"Parameters: {test['parameters']}"
    )

    print(
        "=" * 70
    )

    await websocket.send(
        json.dumps(
            payload,
            ensure_ascii=False,
        )
    )

    while True:

        response_raw = (
            await websocket.recv()
        )

        response = json.loads(
            response_raw
        )

        if (
            response.get(
                "type"
            )
            != "command_result"
        ):
            continue

        if response.get(
            "id"
        ) != command["id"]:

            continue

        print(
            "RESULT:"
        )

        print(
            json.dumps(
                response,
                indent=2,
                ensure_ascii=False,
            )
        )

        return response


# =========================================================
# MAIN
# =========================================================

async def main():

    print()
    print(
        "ALFRED PC CAPABILITY TEST"
    )
    print(
        "=" * 70
    )

    async with websockets.connect(
        HUB_URL
    ) as websocket:

        # -------------------------------------------------
        # NOTE
        # -------------------------------------------------

        print()
        print(
            "Connected to Hub."
        )

        print(
            "Starting capability tests..."
        )

        results = []

        for test in TESTS:

            try:

                response = await send_test(
                    websocket,
                    test,
                )

                results.append(
                    {
                        "name": test["name"],
                        "success": response.get(
                            "success",
                            False,
                        ),
                    }
                )

            except Exception as error:

                print(
                    f"TEST ERROR: {error}"
                )

                results.append(
                    {
                        "name": test["name"],
                        "success": False,
                    }
                )

        # -------------------------------------------------
        # SUMMARY
        # -------------------------------------------------

        print()
        print()
        print(
            "=" * 70
        )
        print(
            "FINAL TEST SUMMARY"
        )
        print(
            "=" * 70
        )

        passed = 0

        for result in results:

            status = (
                "PASS"
                if result["success"]
                else "FAIL"
            )

            print(
                f"{status:6} "
                f"{result['name']}"
            )

            if result["success"]:
                passed += 1

        print()
        print(
            f"Passed: {passed}/{len(results)}"
        )

        print(
            "=" * 70
        )


if __name__ == "__main__":

    asyncio.run(
        main()
    )
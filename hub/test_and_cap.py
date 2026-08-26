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

ANDROID_DEVICE_ID = (
    "android_4d05377015b"
)

TEST_CLIENT_ID = (
    "android_test_client"
)

COMMAND_TIMEOUT = 15


# =========================================================
# TEST RESULTS
# =========================================================

results = []


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
# CREATE COMMAND
# =========================================================

def create_command(
    action,
    parameters=None,
):

    if parameters is None:

        parameters = {}

    return {
        "id": (
            "cmd_"
            + uuid.uuid4().hex
        ),
        "device": ANDROID_DEVICE_ID,
        "action": action,
        "parameters": parameters,
    }


# =========================================================
# RUN TEST
# =========================================================

async def run_test(
    websocket,
    name,
    action,
    parameters=None,
    expect_success=True,
):

    print()
    print(
        "=" * 70
    )

    print(
        f"TEST: {name}"
    )

    print(
        f"Action: {action}"
    )

    print(
        f"Parameters: {parameters or {}}"
    )

    print(
        "=" * 70
    )

    command = create_command(
        action,
        parameters,
    )

    message = {
        "type": "command",
        "command": command,
    }

    try:

        await send_json(
            websocket,
            message,
        )

        response = await asyncio.wait_for(
            websocket.recv(),
            timeout=COMMAND_TIMEOUT,
        )

        data = json.loads(
            response
        )

        print()
        print(
            "RESPONSE:"
        )

        print(
            json.dumps(
                data,
                indent=2,
                ensure_ascii=False,
            )
        )

        success = data.get(
            "success",
            False,
        )

        passed = (
            success == expect_success
        )

        results.append(
            {
                "name": name,
                "action": action,
                "passed": passed,
                "response": data,
            }
        )

        if passed:

            print()
            print(
                "[PASS]"
            )

        else:

            print()
            print(
                "[FAIL]"
            )

    except asyncio.TimeoutError:

        print()
        print(
            "[TIMEOUT]"
        )

        results.append(
            {
                "name": name,
                "action": action,
                "passed": False,
                "response": "TIMEOUT",
            }
        )

    except Exception as error:

        print()
        print(
            f"[ERROR] {error}"
        )

        results.append(
            {
                "name": name,
                "action": action,
                "passed": False,
                "response": str(error),
            }
        )


# =========================================================
# PRINT SUMMARY
# =========================================================

def print_summary():

    print()
    print()
    print(
        "=" * 70
    )

    print(
        "        ALFRED ANDROID CAPABILITY TEST SUMMARY"
    )

    print(
        "=" * 70
    )

    passed_count = 0

    for result in results:

        status = (
            "PASS"
            if result["passed"]
            else "FAIL"
        )

        if result["passed"]:

            passed_count += 1

        print(
            f"[{status}] "
            f"{result['name']}"
        )

    total = len(
        results
    )

    failed = (
        total
        - passed_count
    )

    print()

    print(
        "-" * 70
    )

    print(
        f"TOTAL:  {total}"
    )

    print(
        f"PASSED: {passed_count}"
    )

    print(
        f"FAILED: {failed}"
    )

    print(
        "-" * 70
    )


# =========================================================
# MAIN
# =========================================================

async def main():

    print()

    print(
        "=" * 70
    )

    print(
        "        ALFRED ANDROID CAPABILITY TEST"
    )

    print(
        "=" * 70
    )

    print()

    print(
        f"[TEST] Connecting to {HUB_URL}"
    )

    try:

        async with websockets.connect(
            HUB_URL
        ) as websocket:

            print(
                "[TEST] Connected."
            )

            # =============================================
            # REGISTER TEST CLIENT
            # =============================================

            registration = {
                "type": "register",
                "device_id": TEST_CLIENT_ID,
                "name": "Android Capability Test",
                "device_type": "test_client",
                "capabilities": [],
            }

            await send_json(
                websocket,
                registration,
            )

            response = await websocket.recv()

            print(
                "[TEST] Registration response:"
            )

            print(
                response
            )


            # =============================================
            # BASIC TESTS
            # =============================================

            await run_test(
                websocket,
                "Ping",
                "ping",
            )


            await run_test(
                websocket,
                "Battery Information",
                "battery",
            )


            await run_test(
                websocket,
                "Device Information",
                "device_info",
            )


            # =============================================
            # APPS
            # =============================================

            await run_test(
                websocket,
                "List Applications",
                "apps.list",
            )


            # =============================================
            # VOLUME STATUS
            # =============================================

            await run_test(
                websocket,
                "Volume Status",
                "volume.status",
            )


            # =============================================
            # MEDIA
            # =============================================

            await run_test(
                websocket,
                "Media Play",
                "media.play",
            )


            await run_test(
                websocket,
                "Media Pause",
                "media.pause",
            )


            # =============================================
            # CLIPBOARD
            # =============================================

            await run_test(
                websocket,
                "Clipboard Set",
                "clipboard.set",
                {
                    "text": "ALFRED Android test",
                },
            )


            await run_test(
                websocket,
                "Clipboard Get",
                "clipboard.get",
            )


            # =============================================
            # SHORTCUTS
            # =============================================

            await run_test(
                websocket,
                "List Shortcuts",
                "shortcuts.list",
            )


            # =============================================
            # SUMMARY
            # =============================================

            print_summary()


    except ConnectionRefusedError:

        print()

        print(
            "[ERROR] Hub is not running."
        )

        print(
            "Start it with:"
        )

        print()

        print(
            "python -m hub.hub"
        )


    except Exception as error:

        print()

        print(
            f"[FATAL ERROR] {error}"
        )


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
            "[TEST] Stopped."
        )
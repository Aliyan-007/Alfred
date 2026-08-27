import asyncio
import json
import uuid

import websockets


# =========================================================
# CONFIGURATION
# =========================================================

HUB_URL = "ws://127.0.0.1:8765"

# IMPORTANT:
# This is the Mock Android Device currently registered
# with the ALFRED Hub.
ANDROID_DEVICE_ID = "mock_android_device"

TEST_CLIENT_ID = "android_test_client"

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
        "id": "cmd_" + uuid.uuid4().hex,
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
    print("=" * 70)

    print(f"TEST: {name}")

    print(f"Action: {action}")

    print(f"Parameters: {parameters or {}}")

    print("=" * 70)

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

        print("RESPONSE:")

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

        print()

        if passed:

            print("[PASS]")

        else:

            print("[FAIL]")

    except asyncio.TimeoutError:

        print()

        print("[TIMEOUT]")

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

        print(f"[ERROR] {error}")

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

    print("=" * 70)

    print(
        "        ALFRED ANDROID CAPABILITY TEST SUMMARY"
    )

    print("=" * 70)

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
            f"{result['name']} "
            f"({result['action']})"
        )

    total = len(
        results
    )

    failed = (
        total
        - passed_count
    )

    print()

    print("-" * 70)

    print(f"TOTAL:  {total}")

    print(f"PASSED: {passed_count}")

    print(f"FAILED: {failed}")

    print("-" * 70)

    if failed == 0:

        print()

        print(
            "ALL MOCK ANDROID TESTS PASSED!"
        )

    else:

        print()

        print(
            "SOME TESTS FAILED."
        )


# =========================================================
# MAIN
# =========================================================

async def main():

    print()

    print("=" * 70)

    print(
        "        ALFRED FULL ANDROID CAPABILITY TEST"
    )

    print("=" * 70)

    print()

    print(
        f"[TEST] Target device: "
        f"{ANDROID_DEVICE_ID}"
    )

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

            print()

            print(
                "[TEST] Registration response:"
            )

            print(
                response
            )


            # =============================================
            # BATTERY
            # =============================================

            await run_test(
                websocket,
                "Battery Information",
                "battery",
            )


            # =============================================
            # DEVICE INFORMATION
            # =============================================

            await run_test(
                websocket,
                "Device Information",
                "device_info",
            )


            # =============================================
            # APPLICATIONS
            # =============================================

            await run_test(
                websocket,
                "List Applications",
                "apps.list",
            )

            await run_test(
                websocket,
                "Open Spotify",
                "apps.open",
                {
                    "package":
                        "com.spotify.music",
                },
            )

            await run_test(
                websocket,
                "Current Application",
                "apps.current",
            )

            await run_test(
                websocket,
                "Close Application",
                "apps.close",
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

            await run_test(
                websocket,
                "Media Next",
                "media.next",
            )

            await run_test(
                websocket,
                "Media Previous",
                "media.previous",
            )

            await run_test(
                websocket,
                "Media Stop",
                "media.stop",
            )

            await run_test(
                websocket,
                "Media Fast Forward",
                "media.fast_forward",
            )

            await run_test(
                websocket,
                "Media Rewind",
                "media.rewind",
            )

            await run_test(
                websocket,
                "Media Status",
                "media.status",
            )


            # =============================================
            # VOLUME
            # =============================================

            await run_test(
                websocket,
                "Volume Status",
                "volume.status",
            )

            await run_test(
                websocket,
                "Volume Up",
                "volume.up",
            )

            await run_test(
                websocket,
                "Volume Down",
                "volume.down",
            )

            await run_test(
                websocket,
                "Set Volume",
                "volume.set",
                {
                    "level": 75,
                },
            )

            await run_test(
                websocket,
                "Mute Volume",
                "volume.mute",
            )


            # =============================================
            # HARDWARE
            # =============================================

            await run_test(
                websocket,
                "Flashlight On",
                "hardware.flashlight_on",
            )

            await run_test(
                websocket,
                "Flashlight Off",
                "hardware.flashlight_off",
            )

            await run_test(
                websocket,
                "Vibrate",
                "hardware.vibrate",
                {
                    "duration_ms": 500,
                },
            )

            await run_test(
                websocket,
                "Hardware Status",
                "hardware.status",
            )


            # =============================================
            # CLIPBOARD
            # =============================================

            await run_test(
                websocket,
                "Clipboard Set",
                "clipboard.set",
                {
                    "text":
                        "ALFRED Android test",
                },
            )

            await run_test(
                websocket,
                "Clipboard Get",
                "clipboard.get",
            )

            await run_test(
                websocket,
                "Clipboard Clear",
                "clipboard.clear",
            )


            # =============================================
            # SETTINGS
            # =============================================

            await run_test(
                websocket,
                "WiFi On",
                "settings.wifi_on",
            )

            await run_test(
                websocket,
                "WiFi Off",
                "settings.wifi_off",
            )

            await run_test(
                websocket,
                "Bluetooth On",
                "settings.bluetooth_on",
            )

            await run_test(
                websocket,
                "Bluetooth Off",
                "settings.bluetooth_off",
            )

            await run_test(
                websocket,
                "Settings Status",
                "settings.status",
            )


            # =============================================
            # PHONE
            # =============================================

            await run_test(
                websocket,
                "Dial Phone Number",
                "phone.dial",
                {
                    "number":
                        "+1234567890",
                },
            )

            await run_test(
                websocket,
                "Send SMS",
                "phone.sms",
                {
                    "number":
                        "+1234567890",

                    "message":
                        "Hello from ALFRED",
                },
            )


            # =============================================
            # URL
            # =============================================

            await run_test(
                websocket,
                "Open URL",
                "url.open",
                {
                    "url":
                        "https://www.google.com",
                },
            )


            # =============================================
            # CALENDAR
            # =============================================

            await run_test(
                websocket,
                "Create Calendar Event",
                "calendar.create",
                {
                    "title":
                        "ALFRED Test Meeting",

                    "time":
                        "2026-08-27T10:00:00",
                },
            )

            await run_test(
                websocket,
                "List Calendar Events",
                "calendar.list",
            )


            # =============================================
            # ALARMS
            # =============================================

            await run_test(
                websocket,
                "Create Alarm",
                "alarms.set",
                {
                    "time":
                        "07:30",

                    "label":
                        "ALFRED Test Alarm",
                },
            )

            await run_test(
                websocket,
                "List Alarms",
                "alarms.list",
            )


            # =============================================
            # ACCESSIBILITY
            # =============================================

            await run_test(
                websocket,
                "Accessibility Back",
                "accessibility.back",
            )

            await run_test(
                websocket,
                "Accessibility Home",
                "accessibility.home",
            )

            await run_test(
                websocket,
                "Accessibility Recents",
                "accessibility.recents",
            )

            await run_test(
                websocket,
                "Accessibility Tap",
                "accessibility.tap",
                {
                    "x": 500,

                    "y": 500,
                },
            )

            await run_test(
                websocket,
                "Accessibility Swipe",
                "accessibility.swipe",
                {
                    "x1": 100,

                    "y1": 500,

                    "x2": 800,

                    "y2": 500,
                },
            )

            await run_test(
                websocket,
                "Accessibility Click Text",
                "accessibility.click_text",
                {
                    "text":
                        "Settings",
                },
            )

            await run_test(
                websocket,
                "Accessibility Status",
                "accessibility.status",
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

        print()

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

import asyncio
import json

import websockets


# =========================================================
# CONFIGURATION
# =========================================================

HUB_URL = (
    "ws://127.0.0.1:8765"
)

TEST_CLIENT_ID = (
    "device_discovery_test"
)


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
# MAIN
# =========================================================

async def main():

    print()

    print(
        "=" * 60
    )

    print(
        "       ALFRED DEVICE DISCOVERY TEST"
    )

    print(
        "=" * 60
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

            await send_json(
                websocket,
                {
                    "type": "register",
                    "device_id": TEST_CLIENT_ID,
                    "name": "Device Discovery Test",
                    "device_type": "test_client",
                    "capabilities": [],
                },
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
            # REQUEST DEVICES
            # =============================================

            print()
            print(
                "[TEST] Requesting connected devices..."
            )

            await send_json(
                websocket,
                {
                    "type": "get_devices",
                },
            )

            response = await websocket.recv()

            data = json.loads(
                response
            )

            print()

            print(
                "=" * 60
            )

            print(
                "CONNECTED DEVICES"
            )

            print(
                "=" * 60
            )

            devices = data.get(
                "devices",
                [],
            )

            if not devices:

                print()
                print(
                    "No devices connected."
                )

                return


            for index, device in enumerate(
                devices,
                start=1,
            ):

                print()

                print(
                    f"[{index}]"
                )

                print(
                    "Device ID:",
                    device.get(
                        "device_id"
                    ),
                )

                print(
                    "Name:",
                    device.get(
                        "name"
                    ),
                )

                print(
                    "Type:",
                    device.get(
                        "device_type"
                    ),
                )

                print(
                    "Capabilities:"
                )

                capabilities = device.get(
                    "capabilities",
                    [],
                )

                if capabilities:

                    for capability in capabilities:

                        print(
                            "  -",
                            capability,
                        )

                else:

                    print(
                        "  None"
                    )


            print()
            print(
                "=" * 60
            )

            print(
                f"TOTAL DEVICES: {len(devices)}"
            )

            print(
                "=" * 60
            )


    except Exception as error:

        print()

        print(
            "[ERROR]",
            error,
        )


# =========================================================
# ENTRY POINT
# =========================================================

if __name__ == "__main__":

    asyncio.run(
        main()
    )
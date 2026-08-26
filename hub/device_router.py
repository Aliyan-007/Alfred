import asyncio
import json

import websockets


# =========================================================
# CONFIGURATION
# =========================================================

HUB_URL = (
    "ws://127.0.0.1:8765"
)


# =========================================================
# GET CONNECTED DEVICES
# =========================================================

async def get_connected_devices():

    async with websockets.connect(
        HUB_URL
    ) as websocket:

        await websocket.send(
            json.dumps(
                {
                    "type": "get_devices",
                }
            )
        )

        response = await websocket.recv()

        data = json.loads(
            response
        )

        return data.get(
            "devices",
            [],
        )


# =========================================================
# NORMALIZE CAPABILITY
# =========================================================

def normalize_capability(
    capability,
):

    if isinstance(
        capability,
        str,
    ):

        return capability

    if isinstance(
        capability,
        dict,
    ):

        return capability.get(
            "id"
        )

    return None


# =========================================================
# FIND DEVICE
# =========================================================

async def find_device_for_capability(
    capability,
):

    devices = await get_connected_devices()

    for device in devices:

        capabilities = device.get(
            "capabilities",
            [],
        )

        for item in capabilities:

            current_capability = (
                normalize_capability(
                    item
                )
            )

            if (
                current_capability
                == capability
            ):

                return device

    return None


# =========================================================
# FIND DEVICE BY TYPE
# =========================================================

async def find_device_by_type(
    device_type,
):

    devices = await get_connected_devices()

    for device in devices:

        if (
            device.get(
                "device_type"
            )
            == device_type
        ):

            return device

    return None


# =========================================================
# TEST
# =========================================================

async def main():

    print()

    print(
        "=" * 60
    )

    print(
        "       ALFRED DEVICE ROUTER TEST"
    )

    print(
        "=" * 60
    )

    devices = await get_connected_devices()

    print()

    print(
        f"Connected devices: {len(devices)}"
    )

    for device in devices:

        print()

        print(
            "Device:",
            device.get(
                "name"
            ),
        )

        print(
            "ID:",
            device.get(
                "device_id"
            ),
        )

        print(
            "Type:",
            device.get(
                "device_type"
            ),
        )

    print()

    print(
        "-" * 60
    )

    device = await find_device_by_type(
        "pc"
    )

    if device:

        print(
            "PC FOUND:"
        )

        print(
            device
        )

    else:

        print(
            "NO PC FOUND"
        )

    print()

    device = await find_device_for_capability(
        "battery"
    )

    if device:

        print(
            "BATTERY DEVICE FOUND:"
        )

        print(
            device
        )

    else:

        print(
            "NO BATTERY DEVICE FOUND"
        )


# =========================================================
# ENTRY POINT
# =========================================================

if __name__ == "__main__":

    asyncio.run(
        main()
    )
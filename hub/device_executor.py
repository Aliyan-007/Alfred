import asyncio
import json
import uuid

import websockets


# =========================================================
# CONFIGURATION
# =========================================================

HUB_URL = "ws://127.0.0.1:8765"

COMMAND_TIMEOUT = 30


# =========================================================
# CAPABILITY MATCHING
# =========================================================

def normalize_capability(
    capability,
):
    """
    Convert a capability into its ID.

    Supports:

    "media"

    and:

    {
        "id": "media",
        "state": "available"
    }
    """

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
            "id",
            "",
        )

    return ""


def capability_is_available(
    capability,
):
    """
    Check whether a capability is available.
    """

    if isinstance(
        capability,
        str,
    ):
        return True

    if isinstance(
        capability,
        dict,
    ):
        state = capability.get(
            "state",
            "available",
        )

        return (
            state
            == "available"
        )

    return False


def supports_action(
    capabilities,
    action,
):
    """
    Check whether a device supports an action.

    Exact match:

        ping
        ping

    Parent capability match:

        media
        media.play

        volume
        volume.status

        clipboard
        clipboard.set
    """

    if not capabilities:
        return False

    for capability in capabilities:

        if not capability_is_available(
            capability
        ):
            continue

        capability_id = normalize_capability(
            capability
        )

        if not capability_id:
            continue

        # Exact match
        if (
            capability_id
            == action
        ):
            return True

        # Parent capability match
        if action.startswith(
            capability_id + "."
        ):
            return True

    return False


# =========================================================
# GET CONNECTED DEVICES
# =========================================================

async def get_devices_async():

    try:

        async with websockets.connect(
            HUB_URL
        ) as websocket:

            executor_id = (
                "alfred_executor_"
                + uuid.uuid4().hex[:8]
            )

            registration = {
                "type": "register",
                "device_id": executor_id,
                "name": "ALFRED Device Executor",
                "device_type": "alfred",
                "capabilities": [],
            }

            await websocket.send(
                json.dumps(
                    registration
                )
            )

            # Wait for registration response
            response = await asyncio.wait_for(
                websocket.recv(),
                timeout=COMMAND_TIMEOUT,
            )

            registration_response = json.loads(
                response
            )

            # Optional safety check
            if (
                registration_response.get(
                    "type"
                )
                not in (
                    "registered",
                    None,
                )
            ):
                return []

            await websocket.send(
                json.dumps(
                    {
                        "type": "get_devices",
                    }
                )
            )

            response = await asyncio.wait_for(
                websocket.recv(),
                timeout=COMMAND_TIMEOUT,
            )

            data = json.loads(
                response
            )

            # Hub may return devices in different formats
            if isinstance(
                data,
                dict,
            ):

                if (
                    "devices"
                    in data
                ):
                    return data[
                        "devices"
                    ]

                if (
                    "result"
                    in data
                ):
                    result = data[
                        "result"
                    ]

                    if isinstance(
                        result,
                        dict,
                    ):
                        return result.get(
                            "devices",
                            [],
                        )

                    if isinstance(
                        result,
                        list,
                    ):
                        return result

            return []

    except Exception as error:

        print(
            f"[DEVICE EXECUTOR] "
            f"Device discovery error: "
            f"{error}"
        )

        return []


def get_connected_devices():

    return asyncio.run(
        get_devices_async()
    )


# =========================================================
# SELECT DEVICE
# =========================================================

def select_device(
    action,
    devices,
    requested_device=None,
):
    """
    Select a connected device that supports
    the requested action.
    """

    if requested_device:

        for device in devices:

            device_id = (
                device.get(
                    "device_id"
                )
                or device.get(
                    "id"
                )
            )

            if (
                device_id
                != requested_device
            ):
                continue

            capabilities = device.get(
                "capabilities",
                [],
            )

            if supports_action(
                capabilities,
                action,
            ):
                return device

        return None


    # =====================================================
    # AUTOMATIC DEVICE SELECTION
    # =====================================================

    for device in devices:

        capabilities = device.get(
            "capabilities",
            [],
        )

        if supports_action(
            capabilities,
            action,
        ):
            return device

    return None


# =========================================================
# EXECUTE COMMAND
# =========================================================

async def execute_device_command_async(
    action,
    parameters=None,
    device=None,
):

    if parameters is None:

        parameters = {}

    executor_id = (
        "alfred_executor_"
        + uuid.uuid4().hex[:8]
    )

    command_id = (
        "cmd_"
        + uuid.uuid4().hex
    )

    try:

        async with websockets.connect(
            HUB_URL
        ) as websocket:

            # =============================================
            # REGISTER EXECUTOR
            # =============================================

            registration = {
                "type": "register",
                "device_id": executor_id,
                "name": "ALFRED Device Executor",
                "device_type": "alfred",
                "capabilities": [],
            }

            await websocket.send(
                json.dumps(
                    registration
                )
            )

            registration_response = await asyncio.wait_for(
                websocket.recv(),
                timeout=COMMAND_TIMEOUT,
            )

            registration_data = json.loads(
                registration_response
            )


            # =============================================
            # GET DEVICES
            # =============================================

            await websocket.send(
                json.dumps(
                    {
                        "type": "get_devices",
                    }
                )
            )

            devices_response = await asyncio.wait_for(
                websocket.recv(),
                timeout=COMMAND_TIMEOUT,
            )

            devices_data = json.loads(
                devices_response
            )


            # =============================================
            # EXTRACT DEVICE LIST
            # =============================================

            devices = []

            if isinstance(
                devices_data,
                dict,
            ):

                if (
                    "devices"
                    in devices_data
                ):
                    devices = (
                        devices_data[
                            "devices"
                        ]
                    )

                elif isinstance(
                    devices_data.get(
                        "result"
                    ),
                    dict,
                ):

                    devices = (
                        devices_data[
                            "result"
                        ].get(
                            "devices",
                            [],
                        )
                    )

                elif isinstance(
                    devices_data.get(
                        "result"
                    ),
                    list,
                ):

                    devices = (
                        devices_data[
                            "result"
                        ]
                    )


            # =============================================
            # FIND DEVICE
            # =============================================

            selected_device = select_device(
                action,
                devices,
                device,
            )

            if not selected_device:

                return {
                    "success": False,
                    "error": (
                        f"No connected device "
                        f"supports '{action}'."
                    ),
                }


            # =============================================
            # GET DEVICE ID
            # =============================================

            device_id = (
                selected_device.get(
                    "device_id"
                )
                or selected_device.get(
                    "id"
                )
            )


            if not device_id:

                return {
                    "success": False,
                    "error": (
                        "Selected device "
                        "has no device ID."
                    ),
                }


            print(
                f"[DEVICE EXECUTOR] "
                f"Sending '{action}' "
                f"to {device_id}"
            )


            # =============================================
            # CREATE COMMAND
            # =============================================

            command = {
                "id": command_id,
                "device": device_id,
                "action": action,
                "parameters": parameters,
            }


            message = {
                "type": "command",
                "command": command,
            }


            await websocket.send(
                json.dumps(
                    message
                )
            )


            # =============================================
            # WAIT FOR MATCHING RESULT
            # =============================================

            while True:

                response = await asyncio.wait_for(
                    websocket.recv(),
                    timeout=COMMAND_TIMEOUT,
                )

                data = json.loads(
                    response
                )

                message_type = data.get(
                    "type"
                )


                # Ignore unrelated messages
                if (
                    message_type
                    != "command_result"
                ):
                    continue


                # Ignore result for another command
                if (
                    data.get(
                        "id"
                    )
                    != command_id
                ):
                    continue


                return data


    except asyncio.TimeoutError:

        return {
            "success": False,
            "error": (
                f"Command '{action}' "
                f"timed out after "
                f"{COMMAND_TIMEOUT} seconds."
            ),
        }


    except Exception as error:

        return {
            "success": False,
            "error": str(
                error
            ),
        }


# =========================================================
# PUBLIC FUNCTION
# =========================================================

def execute_device_command(
    action,
    parameters=None,
    device=None,
):
    """
    Execute a command on the best connected device.

    Examples:

        execute_device_command(
            "media.play"
        )

        execute_device_command(
            "clipboard.set",
            {
                "text": "Hello"
            }
        )

        execute_device_command(
            "media.pause",
            device="android_4d05377015b"
        )
    """

    return asyncio.run(
        execute_device_command_async(
            action,
            parameters,
            device,
        )
    )


# =========================================================
# COMMAND LINE TEST
# =========================================================

if __name__ == "__main__":

    import sys


    if len(
        sys.argv
    ) < 2:

        print()

        print(
            "Usage:"
        )

        print()

        print(
            'python -m hub.device_executor '
            '"media.play"'
        )

        print()

        raise SystemExit(
            1
        )


    action = sys.argv[1]

    result = execute_device_command(
        action
    )

    print()

    print(
        json.dumps(
            result,
            indent=2,
            ensure_ascii=False,
        )
    )
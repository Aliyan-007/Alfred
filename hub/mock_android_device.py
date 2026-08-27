import asyncio
import json
import uuid
from datetime import datetime

import websockets


# =========================================================
# CONFIGURATION
# =========================================================

HUB_URL = "ws://127.0.0.1:8765"

DEVICE_ID = "mock_android_device"

DEVICE_NAME = "Mock Android Phone"

DEVICE_TYPE = "android"


# =========================================================
# DEVICE STATE
# =========================================================

device_state = {

    "clipboard": "",

    "volume": 50,

    "flashlight": False,

    "wifi": True,

    "bluetooth": False,

    "media_playing": False,

    "current_app": None,

    "battery": 85,

    "brightness": 50,

    "airplane_mode": False,

    "alarms": [],

    "calendar_events": [],

}


# =========================================================
# CAPABILITIES
#
# These are intentionally aligned with the capability IDs
# registered by the Android app's CapabilityProvider.
# =========================================================

CAPABILITIES = [

    {
        "id": "battery",
        "state": "available",
    },

    {
        "id": "device_info",
        "state": "available",
    },

    {
        "id": "apps",
        "state": "available",
    },

    {
        "id": "url",
        "state": "available",
    },

    {
        "id": "phone",
        "state": "available",
    },

    {
        "id": "media",
        "state": "available",
    },

    {
        "id": "volume",
        "state": "available",
    },

    {
        "id": "hardware",
        "state": "available",
    },

    {
        "id": "settings",
        "state": "available",
    },

    {
        "id": "notifications",
        "state": "available",
    },

    {
        "id": "calendar",
        "state": "available",
    },

    {
        "id": "alarms",
        "state": "available",
    },

    {
        "id": "clipboard",
        "state": "available",
    },

    {
        "id": "shortcuts",
        "state": "available",
    },

    {
        "id": "accessibility",
        "state": "available",
    },

]


# =========================================================
# HELPER FUNCTIONS
# =========================================================

def make_result(
    command_id,
    success=True,
    data=None,
    error=None,
):

    result = {

        "type": "command_result",

        "id": command_id,

        "success": success,

    }

    if data is not None:

        result["data"] = data

    if error is not None:

        result["error"] = error

    return result


def print_command(
    action,
    parameters,
):

    print()

    print(
        "=" * 60
    )

    print(
        "COMMAND RECEIVED"
    )

    print(
        "=" * 60
    )

    print(
        "Action:",
        action,
    )

    print(
        "Parameters:",
        json.dumps(
            parameters,
            indent=2,
        ),
    )

    print(
        "=" * 60
    )

    print()


# =========================================================
# APPLICATION COMMANDS
# =========================================================

def handle_apps(
    action,
    parameters,
):

    if action == "apps.open":

        package = (
            parameters.get(
                "package"
            )
            or parameters.get(
                "app"
            )
            or parameters.get(
                "name"
            )
        )

        if not package:

            return False, None, (
                "Missing package or app name"
            )

        device_state[
            "current_app"
        ] = package

        return True, {

            "opened": package,

            "message":
                f"Opened {package}",

        }, None


    if action == "apps.close":

        previous_app = (
            device_state[
                "current_app"
            ]
        )

        device_state[
            "current_app"
        ] = None

        return True, {

            "closed": previous_app,

        }, None


    if action == "apps.current":

        return True, {

            "current_app":
                device_state[
                    "current_app"
                ]

        }, None


    if action == "apps.list":

        apps = [

            {
                "name": "Spotify",

                "package":
                    "com.spotify.music",

            },

            {
                "name": "YouTube",

                "package":
                    "com.google.android.youtube",

            },

            {
                "name": "Chrome",

                "package":
                    "com.android.chrome",

            },

            {
                "name": "WhatsApp",

                "package":
                    "com.whatsapp",

            },

            {
                "name": "Settings",

                "package":
                    "com.android.settings",

            },

        ]

        return True, {

            "apps": apps,

        }, None


    return None


# =========================================================
# MEDIA COMMANDS
# =========================================================

def handle_media(
    action,
    parameters,
):

    media_action = (
        action.split(
            ".",
            1,
        )[1]
        if "." in action
        else "status"
    )

    if media_action in (
        "play",
        "resume",
    ):

        device_state[
            "media_playing"
        ] = True

        return True, {

            "playing": True,

            "command":
                media_action,

        }, None


    if media_action in (
        "pause",
        "stop",
    ):

        device_state[
            "media_playing"
        ] = False

        return True, {

            "playing": False,

            "command":
                media_action,

        }, None


    if media_action in (
        "next",
        "previous",
        "rewind",
        "fast_forward",
    ):

        return True, {

            "command":
                media_action,

            "performed": True,

        }, None


    if media_action == "status":

        return True, {

            "playing":
                device_state[
                    "media_playing"
                ]

        }, None


    return False, None, (
        f"Unsupported media action: "
        f"{media_action}"
    )


# =========================================================
# VOLUME COMMANDS
# =========================================================

def handle_volume(
    action,
    parameters,
):

    volume_action = (
        action.split(
            ".",
            1,
        )[1]
        if "." in action
        else "status"
    )

    if volume_action == "set":

        level = parameters.get(
            "level"
        )

        if level is None:

            level = parameters.get(
                "volume"
            )

        if level is None:

            return False, None, (
                "Missing volume level"
            )

        try:

            level = int(
                level
            )

        except (
            TypeError,
            ValueError,
        ):

            return False, None, (
                "Volume must be a number"
            )

        level = max(
            0,
            min(
                100,
                level,
            ),
        )

        device_state[
            "volume"
        ] = level

        return True, {

            "volume": level,

        }, None


    if volume_action == "up":

        device_state[
            "volume"
        ] = min(
            100,
            device_state[
                "volume"
            ]
            + 10,
        )

        return True, {

            "volume":
                device_state[
                    "volume"
                ]

        }, None


    if volume_action == "down":

        device_state[
            "volume"
        ] = max(
            0,
            device_state[
                "volume"
            ]
            - 10,
        )

        return True, {

            "volume":
                device_state[
                    "volume"
                ]

        }, None


    if volume_action in (
        "mute",
        "off",
    ):

        device_state[
            "volume"
        ] = 0

        return True, {

            "volume": 0,

        }, None


    if volume_action == "status":

        return True, {

            "volume":
                device_state[
                    "volume"
                ]

        }, None


    return False, None, (
        f"Unsupported volume action: "
        f"{volume_action}"
    )


# =========================================================
# HARDWARE COMMANDS
# =========================================================

def handle_hardware(
    action,
    parameters,
):

    hardware_action = (
        action.split(
            ".",
            1,
        )[1]
        if "." in action
        else "status"
    )

    if hardware_action in (
        "flashlight_on",
        "torch_on",
    ):

        device_state[
            "flashlight"
        ] = True

        return True, {

            "flashlight": "on"

        }, None


    if hardware_action in (
        "flashlight_off",
        "torch_off",
    ):

        device_state[
            "flashlight"
        ] = False

        return True, {

            "flashlight": "off"

        }, None


    if hardware_action == "vibrate":

        duration = parameters.get(
            "duration_ms",
            300,
        )

        return True, {

            "vibrated_ms":
                duration

        }, None


    if hardware_action == "status":

        return True, {

            "flashlight":
                "on"
                if device_state[
                    "flashlight"
                ]
                else "off"

        }, None


    return False, None, (
        f"Unsupported hardware action: "
        f"{hardware_action}"
    )


# =========================================================
# CLIPBOARD COMMANDS
# =========================================================

def handle_clipboard(
    action,
    parameters,
):

    clipboard_action = (
        action.split(
            ".",
            1,
        )[1]
        if "." in action
        else "get"
    )

    if clipboard_action == "set":

        text = parameters.get(
            "text"
        )

        if text is None:

            return False, None, (
                "Missing clipboard text"
            )

        device_state[
            "clipboard"
        ] = str(
            text
        )

        return True, {

            "text":
                device_state[
                    "clipboard"
                ]

        }, None


    if clipboard_action == "get":

        return True, {

            "text":
                device_state[
                    "clipboard"
                ]

        }, None


    if clipboard_action == "clear":

        device_state[
            "clipboard"
        ] = ""

        return True, {

            "cleared": True

        }, None


    return False, None, (
        f"Unsupported clipboard action: "
        f"{clipboard_action}"
    )


# =========================================================
# SETTINGS COMMANDS
# =========================================================

def handle_settings(
    action,
    parameters,
):

    settings_action = (
        action.split(
            ".",
            1,
        )[1]
        if "." in action
        else "status"
    )

    if settings_action in (
        "wifi_on",
        "enable_wifi",
    ):

        device_state[
            "wifi"
        ] = True

        return True, {

            "wifi": True

        }, None


    if settings_action in (
        "wifi_off",
        "disable_wifi",
    ):

        device_state[
            "wifi"
        ] = False

        return True, {

            "wifi": False

        }, None


    if settings_action in (
        "bluetooth_on",
        "enable_bluetooth",
    ):

        device_state[
            "bluetooth"
        ] = True

        return True, {

            "bluetooth": True

        }, None


    if settings_action in (
        "bluetooth_off",
        "disable_bluetooth",
    ):

        device_state[
            "bluetooth"
        ] = False

        return True, {

            "bluetooth": False

        }, None


    if settings_action == "status":

        return True, {

            "wifi":
                device_state[
                    "wifi"
                ],

            "bluetooth":
                device_state[
                    "bluetooth"
                ],

            "airplane_mode":
                device_state[
                    "airplane_mode"
                ],

            "brightness":
                device_state[
                    "brightness"
                ],

        }, None


    return True, {

        "requested_setting":
            settings_action,

        "opened": True,

    }, None


# =========================================================
# PHONE COMMANDS
# =========================================================

def handle_phone(
    action,
    parameters,
):

    phone_action = (
        action.split(
            ".",
            1,
        )[1]
        if "." in action
        else ""
    )

    if phone_action in (
        "dial",
        "call",
    ):

        number = parameters.get(
            "number"
        )

        if not number:

            return False, None, (
                "Missing phone number"
            )

        return True, {

            "dialing":
                number

        }, None


    if phone_action in (
        "sms",
        "message",
    ):

        number = parameters.get(
            "number"
        )

        message = parameters.get(
            "message"
        )

        if not number:

            return False, None, (
                "Missing phone number"
            )

        return True, {

            "number": number,

            "message": message,

            "sent": True,

        }, None


    return False, None, (
        f"Unsupported phone action: "
        f"{phone_action}"
    )


# =========================================================
# ACCESSIBILITY COMMANDS
# =========================================================

def handle_accessibility(
    action,
    parameters,
):

    accessibility_action = (
        action.split(
            ".",
            1,
        )[1]
        if "." in action
        else "status"
    )

    allowed = [

        "back",

        "home",

        "recents",

        "tap",

        "swipe",

        "click_text",

    ]

    if accessibility_action in allowed:

        return True, {

            "action":
                accessibility_action,

            "performed": True,

        }, None


    if accessibility_action == "status":

        return True, {

            "enabled": True,

            "connected": True,

        }, None


    return False, None, (
        f"Unsupported accessibility action: "
        f"{accessibility_action}"
    )


# =========================================================
# BATTERY COMMANDS
# =========================================================

def handle_battery(
    action,
    parameters,
):

    return True, {

        "level":
            device_state[
                "battery"
            ],

        "charging": False,

    }, None


# =========================================================
# DEVICE INFORMATION
# =========================================================

def handle_device_info(
    action,
    parameters,
):

    return True, {

        "manufacturer":
            "ALFRED",

        "model":
            "Mock Android Device",

        "android_version":
            "15",

        "device_id":
            DEVICE_ID,

    }, None


# =========================================================
# URL COMMANDS
# =========================================================

def handle_url(
    action,
    parameters,
):

    url = parameters.get(
        "url"
    )

    if not url:

        return False, None, (
            "Missing URL"
        )

    return True, {

        "opened_url":
            url

    }, None


# =========================================================
# CALENDAR COMMANDS
# =========================================================

def handle_calendar(
    action,
    parameters,
):

    calendar_action = (
        action.split(
            ".",
            1,
        )[1]
        if "." in action
        else "list"
    )

    if calendar_action == "create":

        event = {

            "id":
                uuid.uuid4().hex[:8],

            "title":
                parameters.get(
                    "title",
                    "Untitled Event",
                ),

            "time":
                parameters.get(
                    "time"
                ),

            "created_at":
                datetime.now()
                .isoformat(),

        }

        device_state[
            "calendar_events"
        ].append(
            event
        )

        return True, {

            "event": event

        }, None


    if calendar_action == "list":

        return True, {

            "events":
                device_state[
                    "calendar_events"
                ]

        }, None


    return False, None, (
        f"Unsupported calendar action: "
        f"{calendar_action}"
    )


# =========================================================
# ALARM COMMANDS
# =========================================================

def handle_alarms(
    action,
    parameters,
):

    alarm_action = (
        action.split(
            ".",
            1,
        )[1]
        if "." in action
        else "list"
    )

    if alarm_action in (
        "set",
        "create",
    ):

        alarm = {

            "id":
                uuid.uuid4().hex[:8],

            "time":
                parameters.get(
                    "time"
                ),

            "label":
                parameters.get(
                    "label",
                    "ALFRED Alarm",
                ),

        }

        device_state[
            "alarms"
        ].append(
            alarm
        )

        return True, {

            "alarm": alarm

        }, None


    if alarm_action == "list":

        return True, {

            "alarms":
                device_state[
                    "alarms"
                ]

        }, None


    return False, None, (
        f"Unsupported alarm action: "
        f"{alarm_action}"
    )


# =========================================================
# COMMAND ROUTER
# =========================================================

def execute_command(
    action,
    parameters,
):

    print(
        f"[MOCK DEVICE] Executing action: {action}"
    )

    if action == "apps.open":

        package = (
            parameters.get("package")
            or parameters.get("app")
            or parameters.get("name")
        )

        if not package:

            return (
                False,
                None,
                "Missing package or app name",
            )

        device_state["current_app"] = package

        return (
            True,
            {
                "opened": package,
                "message": f"Opened {package}",
            },
            None,
        )


    if action.startswith("apps."):

        return handle_apps(
            action,
            parameters,
        )


    if action.startswith("media."):

        return handle_media(
            action,
            parameters,
        )


    if action.startswith("volume."):

        return handle_volume(
            action,
            parameters,
        )


    if action.startswith("hardware."):

        return handle_hardware(
            action,
            parameters,
        )


    if action.startswith("clipboard."):

        return handle_clipboard(
            action,
            parameters,
        )


    if action.startswith("settings."):

        return handle_settings(
            action,
            parameters,
        )


    if action.startswith("phone."):

        return handle_phone(
            action,
            parameters,
        )


    if action.startswith("accessibility."):

        return handle_accessibility(
            action,
            parameters,
        )


    if action.startswith("battery"):

        return handle_battery(
            action,
            parameters,
        )


    if action.startswith("device_info"):

        return handle_device_info(
            action,
            parameters,
        )


    if action.startswith("url."):

        return handle_url(
            action,
            parameters,
        )


    if action.startswith("calendar."):

        return handle_calendar(
            action,
            parameters,
        )


    if action.startswith("alarms."):

        return handle_alarms(
            action,
            parameters,
        )


    return (
        False,
        None,
        f"Unsupported action: {action}",
    )

# =========================================================
# REGISTER DEVICE
# =========================================================

def build_registration():

    return {

        "type": "register",

        "device_id":
            DEVICE_ID,

        "name":
            DEVICE_NAME,

        "device_type":
            DEVICE_TYPE,

        "capabilities":
            CAPABILITIES,

    }


# =========================================================
# RUN DEVICE
# =========================================================

async def run_device():

    while True:

        try:

            print()

            print(
                "=" * 60
            )

            print(
                "ALFRED MOCK ANDROID DEVICE"
            )

            print(
                "=" * 60
            )

            print(
                f"Connecting to: {HUB_URL}"
            )

            print()

            async with websockets.connect(
                HUB_URL
            ) as websocket:

                # -----------------------------------------
                # REGISTER
                # -----------------------------------------

                registration = (
                    build_registration()
                )

                await websocket.send(
                    json.dumps(
                        registration
                    )
                )

                print(
                    "Registration sent"
                )

                response = (
                    await websocket.recv()
                )

                print(
                    "Hub response:"
                )

                print(
                    response
                )

                print()

                print(
                    "Mock Android device is READY"
                )

                print(
                    f"Device ID: {DEVICE_ID}"
                )

                print()

                print(
                    "Waiting for commands..."
                )

                print()

                # -----------------------------------------
                # COMMAND LOOP
                # -----------------------------------------

                async for raw in websocket:

                    try:

                        message = json.loads(
                            raw
                        )

                    except json.JSONDecodeError:

                        print(
                            "Invalid JSON received"
                        )

                        continue


                    message_type = (
                        message.get(
                            "type"
                        )
                    )


                    # -------------------------------------
                    # PING
                    # -------------------------------------

                    if message_type == "ping":

                        await websocket.send(
                            json.dumps(
                                {
                                    "type":
                                        "pong"
                                }
                            )
                        )

                        continue


                    # -------------------------------------
                    # COMMAND
                    # -------------------------------------

                    if message_type != "command":

                        print(
                            "Ignoring message:",
                            message_type,
                        )

                        continue


                    command = (
                        message.get(
                            "command",
                            {},
                        )
                    )

                    command_id = (
                        command.get(
                            "id"
                        )
                    )

                    target_device = (
                        command.get(
                            "device"
                        )
                    )

                    action = (
                        command.get(
                            "action"
                        )
                    )

                    parameters = (
                        command.get(
                            "parameters",
                            {},
                        )
                    )


                    # -------------------------------------
                    # CHECK DEVICE
                    # -------------------------------------

                    if (
                        target_device
                        and target_device
                        != DEVICE_ID
                    ):

                        print(
                            "Command belongs to another device"
                        )

                        continue


                    # -------------------------------------
                    # EXECUTE
                    # -------------------------------------

                    print_command(
                        action,
                        parameters,
                    )

                    try:

                        success, data, error = (
                            execute_command(
                                action,
                                parameters,
                            )
                        )

                    except Exception as error:

                        success = False

                        data = None

                        error = str(
                            error
                        )


                    # -------------------------------------
                    # RESULT
                    # -------------------------------------

                    result = make_result(
                        command_id,

                        success,

                        data,

                        error,
                    )

                    print(
                        "RESULT:"
                    )

                    print(
                        json.dumps(
                            result,
                            indent=2,
                        )
                    )

                    await websocket.send(
                        json.dumps(
                            result
                        )
                    )


        except (
            websockets.ConnectionClosed,
            ConnectionRefusedError,
            OSError,
        ) as error:

            print()

            print(
                "Connection lost:"
            )

            print(
                error
            )

            print()

            print(
                "Retrying in 3 seconds..."
            )

            await asyncio.sleep(
                3
            )


        except Exception as error:

            print()

            print(
                "Unexpected error:"
            )

            print(
                error
            )

            print()

            print(
                "Retrying in 5 seconds..."
            )

            await asyncio.sleep(
                5
            )


# =========================================================
# ENTRY POINT
# =========================================================

if __name__ == "__main__":

    try:

        asyncio.run(
            run_device()
        )

    except KeyboardInterrupt:

        print()

        print(
            "Mock Android device stopped."
        )
import ctypes
import json

import requests
import websocket

from tools.browser import ensure_brave
# =========================================================
# CONFIGURATION
# =========================================================

CDP_BASE = "http://127.0.0.1:9222"
CDP_TIMEOUT = 8


# =========================================================
# WINDOWS MASTER VOLUME
# =========================================================

VK_VOLUME_MUTE = 0xAD
VK_VOLUME_DOWN = 0xAE
VK_VOLUME_UP = 0xAF


def press_volume_key(
    key_code: int,
):
    """
    Send a Windows volume key.
    """

    ctypes.windll.user32.keybd_event(
        key_code,
        0,
        0,
        0,
    )

    ctypes.windll.user32.keybd_event(
        key_code,
        0,
        2,
        0,
    )


def pc_volume_up():
    press_volume_key(
        VK_VOLUME_UP
    )

    return "PC volume increased, Sir."


def pc_volume_down():
    press_volume_key(
        VK_VOLUME_DOWN
    )

    return "PC volume decreased, Sir."


def pc_volume_mute():
    press_volume_key(
        VK_VOLUME_MUTE
    )

    return "PC volume muted, Sir."


def pc_volume_unmute():
    press_volume_key(
        VK_VOLUME_MUTE
    )

    return "PC volume unmuted, Sir."


# =========================================================
# CDP COMMAND
# =========================================================

def cdp_command(
    ws,
    command_id,
    method,
    params=None,
):
    """
    Send a Chrome DevTools Protocol command and wait
    for its matching response.
    """

    message = {
        "id": command_id,
        "method": method,
    }

    if params is not None:
        message["params"] = params

    ws.send(
        json.dumps(message)
    )

    while True:

        response = json.loads(
            ws.recv()
        )

        if response.get("id") == command_id:
            return response


# =========================================================
# FIND MEDIA TABS
# =========================================================

def find_media_tabs():
    """
    Make sure ALFRED's Brave is running, then find
    existing YouTube and Spotify tabs.
    """

    if not ensure_brave():
        raise RuntimeError(
            "ALFRED's Brave browser could not be started."
        )

    response = requests.get(
        f"{CDP_BASE}/json/list",
        timeout=5,
    )

    response.raise_for_status()

    pages = response.json()

    youtube_tabs = []
    spotify_tabs = []

    for page in pages:

        if page.get("type") != "page":
            continue

        url = page.get(
            "url",
            "",
        ).lower()

        if "youtube.com" in url:
            youtube_tabs.append(page)

        elif "open.spotify.com" in url:
            spotify_tabs.append(page)

    return (
        youtube_tabs,
        spotify_tabs,
    )
# =========================================================
# CONNECT TO MEDIA TAB
# =========================================================

def connect_to_tab(
    page,
):
    """
    Connect directly to an existing Brave tab.
    """

    websocket_url = page.get(
        "webSocketDebuggerUrl"
    )

    if not websocket_url:
        return None

    ws = websocket.create_connection(
        websocket_url,
        timeout=CDP_TIMEOUT,
        origin=CDP_BASE,
    )

    cdp_command(
        ws,
        1,
        "Runtime.enable",
    )

    return ws


# =========================================================
# YOUTUBE CONTROL
# =========================================================

def youtube_control(
    action: str,
):
    """
    Control the first available YouTube tab.
    """

    youtube_tabs, _ = find_media_tabs()

    if not youtube_tabs:

        return (
            "I don't currently have a YouTube "
            "tab open, Sir."
        )

    ws = None

    try:

        ws = connect_to_tab(
            youtube_tabs[0]
        )

        if ws is None:

            return (
                "I couldn't connect to YouTube, Sir."
            )

        expressions = {

            # -------------------------------------------------
            # PAUSE
            # -------------------------------------------------

            "pause": """
                (() => {

                    const video =
                        document.querySelector("video");

                    if (!video) {
                        return false;
                    }

                    if (video.paused) {
                        return false;
                    }

                    video.pause();

                    return true;

                })()
            """,

            # -------------------------------------------------
            # RESUME
            # -------------------------------------------------

            "resume": """
                (() => {

                    const video =
                        document.querySelector("video");

                    if (!video) {
                        return false;
                    }

                    if (!video.paused) {
                        return false;
                    }

                    const result =
                        video.play();

                    return true;

                })()
            """,

            # -------------------------------------------------
            # STOP
            # -------------------------------------------------

            "stop": """
                (() => {

                    const video =
                        document.querySelector("video");

                    if (!video) {
                        return false;
                    }

                    video.pause();

                    video.currentTime = 0;

                    return true;

                })()
            """,

            # -------------------------------------------------
            # NEXT
            # -------------------------------------------------

            "next": """
                (() => {

                    const button =
                        document.querySelector(
                            ".ytp-next-button"
                        );

                    if (!button) {
                        return false;
                    }

                    button.click();

                    return true;

                })()
            """,

            # -------------------------------------------------
            # PREVIOUS
            # -------------------------------------------------

            "previous": """
                (() => {

                    const button =
                        document.querySelector(
                            ".ytp-prev-button"
                        );

                    if (!button) {
                        return false;
                    }

                    button.click();

                    return true;

                })()
            """,

            # -------------------------------------------------
            # VOLUME UP
            # -------------------------------------------------

            "volume_up": """
                (() => {

                    const video =
                        document.querySelector("video");

                    if (!video) {
                        return false;
                    }

                    video.volume =
                        Math.min(
                            1,
                            video.volume + 0.10
                        );

                    return true;

                })()
            """,

            # -------------------------------------------------
            # VOLUME DOWN
            # -------------------------------------------------

            "volume_down": """
                (() => {

                    const video =
                        document.querySelector("video");

                    if (!video) {
                        return false;
                    }

                    video.volume =
                        Math.max(
                            0,
                            video.volume - 0.10
                        );

                    return true;

                })()
            """,
        }

        expression = expressions.get(
            action
        )

        if expression is None:

            return (
                "I don't know that YouTube "
                "control, Sir."
            )

        result = cdp_command(
            ws,
            2,
            "Runtime.evaluate",
            {
                "expression": expression,
                "returnByValue": True,
            },
        )

        success = (
            result
            .get("result", {})
            .get("result", {})
            .get("value", False)
        )

        if not success:

            messages = {

                "pause":
                    "YouTube is already paused, Sir.",

                "resume":
                    "YouTube is already playing, "
                    "or I couldn't start it, Sir.",

                "stop":
                    "I couldn't stop YouTube, Sir.",

                "next":
                    "I couldn't move to the next "
                    "YouTube video, Sir.",

                "previous":
                    "I couldn't go to the previous "
                    "YouTube video, Sir.",

                "volume_up":
                    "I couldn't increase YouTube volume, Sir.",

                "volume_down":
                    "I couldn't decrease YouTube volume, Sir.",
            }

            return messages.get(
                action,
                "I couldn't control YouTube, Sir.",
            )

        responses = {

            "pause":
                "YouTube paused, Sir.",

            "resume":
                "YouTube resumed, Sir.",

            "stop":
                "YouTube stopped, Sir.",

            "next":
                "Playing the next YouTube video, Sir.",

            "previous":
                "Going back to the previous "
                "YouTube video, Sir.",

            "volume_up":
                "YouTube volume increased, Sir.",

            "volume_down":
                "YouTube volume decreased, Sir.",
        }

        return responses[action]

    except Exception as error:

        return (
            "I couldn't control YouTube, Sir. "
            f"{error}"
        )

    finally:

        if ws is not None:

            try:
                ws.close()
            except Exception:
                pass


# =========================================================
# SPOTIFY CONTROL
# =========================================================

def spotify_control(
    action: str,
):
    """
    Control Spotify using the exact controls exposed
    by the current Spotify web player.
    """

    _, spotify_tabs = find_media_tabs()

    if not spotify_tabs:

        return (
            "I don't currently have a Spotify "
            "tab open, Sir."
        )

    ws = None

    try:

        ws = connect_to_tab(
            spotify_tabs[0]
        )

        if ws is None:

            return (
                "I couldn't connect to Spotify, Sir."
            )

        # -------------------------------------------------
        # PAUSE
        # -------------------------------------------------

        if action == "pause":

            expression = """
            (() => {

                const button =
                    document.querySelector(
                        '[data-testid="control-button-playpause"]'
                    );

                if (!button) {
                    return false;
                }

                const label = (
                    button.getAttribute(
                        "aria-label"
                    ) || ""
                ).toLowerCase();

                if (!label.includes("pause")) {
                    return false;
                }

                button.click();

                return true;

            })()
            """

            response_text = (
                "Spotify paused, Sir."
            )

        # -------------------------------------------------
        # RESUME
        # -------------------------------------------------

        elif action == "resume":

            expression = """
            (() => {

                const button =
                    document.querySelector(
                        '[data-testid="control-button-playpause"]'
                    );

                if (!button) {
                    return false;
                }

                const label = (
                    button.getAttribute(
                        "aria-label"
                    ) || ""
                ).toLowerCase();

                if (!label.includes("play")) {
                    return false;
                }

                button.click();

                return true;

            })()
            """

            response_text = (
                "Spotify resumed, Sir."
            )

        # -------------------------------------------------
        # NEXT
        # -------------------------------------------------

        elif action == "next":

            expression = """
            (() => {

                const button =
                    document.querySelector(
                        '[data-testid="control-button-skip-forward"]'
                    );

                if (!button) {
                    return false;
                }

                button.click();

                return true;

            })()
            """

            response_text = (
                "Playing the next song, Sir."
            )

        # -------------------------------------------------
        # PREVIOUS
        # -------------------------------------------------

        elif action == "previous":

            expression = """
            (() => {

                const button =
                    document.querySelector(
                        '[data-testid="control-button-skip-back"]'
                    );

                if (!button) {
                    return false;
                }

                button.click();

                return true;

            })()
            """

            response_text = (
                "Going back to the previous song, Sir."
            )

        # -------------------------------------------------
        # UNSUPPORTED
        # -------------------------------------------------

        else:

            return (
                "That Spotify control isn't "
                "available yet, Sir."
            )

        # -------------------------------------------------
        # EXECUTE
        # -------------------------------------------------

        result = cdp_command(
            ws,
            50,
            "Runtime.evaluate",
            {
                "expression": expression,
                "returnByValue": True,
            },
        )

        success = (
            result
            .get("result", {})
            .get("result", {})
            .get("value", False)
        )

        if not success:

            messages = {

                "pause":
                    "Spotify is already paused, "
                    "or I couldn't pause it, Sir.",

                "resume":
                    "Spotify is already playing, "
                    "or I couldn't resume it, Sir.",

                "next":
                    "I couldn't skip to the next song, Sir.",

                "previous":
                    "I couldn't go to the previous "
                    "song, Sir.",
            }

            return messages.get(
                action,
                "I couldn't control Spotify, Sir.",
            )

        return response_text

    except Exception as error:

        return (
            "I couldn't control Spotify, Sir. "
            f"{error}"
        )

    finally:

        if ws is not None:

            try:
                ws.close()
            except Exception:
                pass


# =========================================================
# TARGETED MEDIA CONTROL
# =========================================================

def media_control(
    service: str,
    action: str,
):
    """
    Explicitly control Spotify or YouTube.
    """

    service = (
        service
        .lower()
        .strip()
    )

    if service == "spotify":

        return spotify_control(
            action
        )

    if service == "youtube":

        return youtube_control(
            action
        )

    return (
        "I don't know that media service, Sir."
    )


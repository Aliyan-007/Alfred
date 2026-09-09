import ctypes
import json
from typing import Optional

import requests
import websocket

from tools.browser import (
    CDP_BASE,
    CDP_TIMEOUT,
    connect_page,
    cdp_command,
    ensure_brave,
)


# =========================================================
# WINDOWS MEDIA / VOLUME KEYS
# =========================================================

VK_VOLUME_MUTE = 0xAD
VK_VOLUME_DOWN = 0xAE
VK_VOLUME_UP = 0xAF


def _press_key(key_code: int) -> None:
    """Press and release a Windows media key."""
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


def pc_volume_up() -> str:
    """Increase system volume."""
    _press_key(VK_VOLUME_UP)
    _press_key(VK_VOLUME_UP)
    return "Volume increased, Sir."


def pc_volume_down() -> str:
    """Decrease system volume."""
    _press_key(VK_VOLUME_DOWN)
    _press_key(VK_VOLUME_DOWN)
    return "Volume decreased, Sir."


def pc_volume_mute() -> str:
    """Toggle Windows audio mute."""
    _press_key(VK_VOLUME_MUTE)
    return "Audio muted, Sir."


def pc_volume_unmute() -> str:
    """
    Toggle Windows audio mute.

    Windows exposes mute as a toggle rather than separate mute/unmute
    media keys, so this intentionally uses the same key as mute.
    """
    _press_key(VK_VOLUME_MUTE)
    return "Audio unmuted, Sir."


# =========================================================
# MEDIA TAB DISCOVERY
# =========================================================

def find_media_tab(service: str) -> Optional[dict]:
    """
    Find an open YouTube or Spotify tab controlled by Brave CDP.
    """
    if not ensure_brave():
        return None

    service = str(service or "").strip().lower()

    domains = {
        "youtube": "youtube.com",
        "spotify": "open.spotify.com",
    }

    domain = domains.get(service)

    if not domain:
        return None

    try:
        response = requests.get(
            f"{CDP_BASE}/json/list",
            timeout=3,
        )
        response.raise_for_status()

        pages = response.json()

        for page in pages:
            if page.get("type") != "page":
                continue

            url = page.get("url", "").lower()

            if domain in url:
                return page

    except Exception as error:
        print(f"[MEDIA] Failed to find {service} tab: {error}")

    return None


# =========================================================
# GENERIC CDP JAVASCRIPT HELPER
# =========================================================

def _evaluate_media_script(page: dict, script: str):
    """
    Execute JavaScript inside a media tab and return its value.
    """
    ws = None

    try:
        ws = connect_page(page)

        cdp_command(
            ws,
            1,
            "Runtime.enable",
        )

        result = cdp_command(
            ws,
            2,
            "Runtime.evaluate",
            {
                "expression": script,
                "returnByValue": True,
                "awaitPromise": True,
            },
        )

        root = result.get("result", {})

        if "exceptionDetails" in root:
            exception = root["exceptionDetails"].get(
                "exception",
                {},
            )

            description = exception.get(
                "description",
                "Media script failed.",
            )

            raise RuntimeError(description)

        return root.get("result", {}).get("value")

    finally:
        if ws:
            ws.close()


# =========================================================
# YOUTUBE
# =========================================================

def youtube_control(action: str) -> str:
    """
    Control playback in the currently open YouTube tab.

    Supported:
        pause
        resume
        stop
        next
        previous
    """
    page = find_media_tab("youtube")

    if not page:
        return "No open YouTube tab was found, Sir."

    action = str(action or "").strip().lower()

    scripts = {
        "pause": """
            (() => {
                const video = document.querySelector("video");

                if (!video || video.paused) {
                    return false;
                }

                video.pause();
                return true;
            })()
        """,

        "resume": """
            (() => {
                const video = document.querySelector("video");

                if (!video || !video.paused) {
                    return false;
                }

                const result = video.play();

                if (result && typeof result.catch === "function") {
                    result.catch(() => {});
                }

                return true;
            })()
        """,

        "stop": """
            (() => {
                const video = document.querySelector("video");

                if (!video) {
                    return false;
                }

                video.pause();
                video.currentTime = 0;

                return true;
            })()
        """,

        "next": """
            (() => {
                const button =
                    document.querySelector(".ytp-next-button") ||
                    document.querySelector(".ytp-next-button.ytp-button");

                if (!button || button.disabled) {
                    return false;
                }

                button.click();
                return true;
            })()
        """,

        "previous": """
            (() => {
                const button =
                    document.querySelector(".ytp-prev-button") ||
                    document.querySelector(".ytp-prev-button.ytp-button");

                if (!button || button.disabled) {
                    return false;
                }

                button.click();
                return true;
            })()
        """,
    }

    script = scripts.get(action)

    if not script:
        return f"Unknown YouTube action: {action}"

    try:
        success = bool(
            _evaluate_media_script(
                page,
                script,
            )
        )

        if success:
            return f"YouTube {action} executed, Sir."

        return f"YouTube could not {action}, Sir."

    except Exception as error:
        return f"Error controlling YouTube: {error}"


# =========================================================
# SPOTIFY
# =========================================================

def spotify_control(action: str) -> str:
    """
    Control playback in the currently open Spotify Web Player tab.

    Supported:
        pause
        resume
        next
        previous
    """
    page = find_media_tab("spotify")

    if not page:
        return "No open Spotify tab was found, Sir."

    action = str(action or "").strip().lower()

    scripts = {
        "pause": """
            (() => {
                const button = document.querySelector(
                    '[data-testid="control-button-playpause"]'
                );

                if (!button) {
                    return false;
                }

                const label = (
                    button.getAttribute("aria-label") || ""
                ).toLowerCase();

                if (!label.includes("pause")) {
                    return false;
                }

                button.click();
                return true;
            })()
        """,

        "resume": """
            (() => {
                const button = document.querySelector(
                    '[data-testid="control-button-playpause"]'
                );

                if (!button) {
                    return false;
                }

                const label = (
                    button.getAttribute("aria-label") || ""
                ).toLowerCase();

                if (!label.includes("play")) {
                    return false;
                }

                button.click();
                return true;
            })()
        """,

        "next": """
            (() => {
                const button =
                    document.querySelector(
                        '[data-testid="control-button-skip-forward"]'
                    ) ||
                    document.querySelector(
                        'button[aria-label*="Next"]'
                    );

                if (!button || button.disabled) {
                    return false;
                }

                button.click();
                return true;
            })()
        """,

        "previous": """
            (() => {
                const button =
                    document.querySelector(
                        '[data-testid="control-button-skip-back"]'
                    ) ||
                    document.querySelector(
                        'button[aria-label*="Previous"]'
                    );

                if (!button || button.disabled) {
                    return false;
                }

                button.click();
                return true;
            })()
        """,
    }

    script = scripts.get(action)

    if not script:
        return f"Unknown Spotify action: {action}"

    try:
        success = bool(
            _evaluate_media_script(
                page,
                script,
            )
        )

        if success:
            return f"Spotify {action} executed, Sir."

        return f"Spotify could not {action}, Sir."

    except Exception as error:
        return f"Error controlling Spotify: {error}"

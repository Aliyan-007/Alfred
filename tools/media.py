import ctypes
import json
import requests
import websocket
from tools.browser import ensure_brave

CDP_BASE = "http://127.0.0.1:9222"
CDP_TIMEOUT = 5

VK_VOLUME_MUTE = 0xAD
VK_VOLUME_DOWN = 0xAE
VK_VOLUME_UP = 0xAF


# =========================================================
# HARDWARE VOLUME
# =========================================================

def _press_key(key_code: int):
    ctypes.windll.user32.keybd_event(key_code, 0, 0, 0)
    ctypes.windll.user32.keybd_event(key_code, 0, 2, 0)


def pc_volume_up():
    _press_key(VK_VOLUME_UP)
    _press_key(VK_VOLUME_UP)
    return "Volume increased, Sir."


def pc_volume_down():
    _press_key(VK_VOLUME_DOWN)
    _press_key(VK_VOLUME_DOWN)
    return "Volume decreased, Sir."


def pc_volume_mute():
    _press_key(VK_VOLUME_MUTE)
    return "Audio muted, Sir."


def pc_volume_unmute():
    _press_key(VK_VOLUME_MUTE)
    return "Audio unmuted, Sir."


# =========================================================
# CDP MEDIA PLAYBACK (YOUTUBE / SPOTIFY)
# =========================================================

def find_media_tab(service: str):
    if not ensure_brave():
        return None
    try:
        res = requests.get(f"{CDP_BASE}/json/list", timeout=3)
        pages = res.json()
        domain = "youtube.com" if service == "youtube" else "open.spotify.com"
        for page in pages:
            if page.get("type") == "page" and domain in page.get("url", "").lower():
                return page
    except Exception:
        pass
    return None


def youtube_control(action: str) -> str:
    page = find_media_tab("youtube")
    if not page:
        return "No open YouTube tab was found, Sir."

    ws = None
    try:
        ws = websocket.create_connection(page["webSocketDebuggerUrl"], timeout=CDP_TIMEOUT)
        
        scripts = {
            "pause": "const v = document.querySelector('video'); if (v && !v.paused) { v.pause(); true; } else { false; }",
            "resume": "const v = document.querySelector('video'); if (v && v.paused) { v.play(); true; } else { false; }",
            "stop": "const v = document.querySelector('video'); if (v) { v.pause(); v.currentTime = 0; true; } else { false; }",
            "next": "const b = document.querySelector('.ytp-next-button'); if (b) { b.click(); true; } else { false; }",
            "previous": "const b = document.querySelector('.ytp-prev-button'); if (b) { b.click(); true; } else { false; }",
        }
        
        script = scripts.get(action.lower())
        if not script:
            return f"Unknown YouTube action: {action}"

        ws.send(json.dumps({
            "id": 1,
            "method": "Runtime.evaluate",
            "params": {"expression": script, "returnByValue": True}
        }))
        res = json.loads(ws.recv())
        val = res.get("result", {}).get("result", {}).get("value", False)
        
        return f"YouTube {action} executed, Sir." if val else f"YouTube could not {action}, Sir."
    except Exception as e:
        return f"Error controlling YouTube: {e}"
    finally:
        if ws:
            ws.close()


def spotify_control(action: str) -> str:
    page = find_media_tab("spotify")
    if not page:
        return "No open Spotify tab was found, Sir."

    ws = None
    try:
        ws = websocket.create_connection(page["webSocketDebuggerUrl"], timeout=CDP_TIMEOUT)

        scripts = {
            "pause": "const b = document.querySelector('[data-testid=\"control-button-playpause\"]'); if (b && b.getAttribute('aria-label').toLowerCase().includes('pause')) { b.click(); true; } else { false; }",
            "resume": "const b = document.querySelector('[data-testid=\"control-button-playpause\"]'); if (b && b.getAttribute('aria-label').toLowerCase().includes('play')) { b.click(); true; } else { false; }",
            "next": "const b = document.querySelector('[data-testid=\"control-button-skip-forward\"]'); if (b) { b.click(); true; } else { false; }",
            "previous": "const b = document.querySelector('[data-testid=\"control-button-skip-back\"]'); if (b) { b.click(); true; } else { false; }",
        }

        script = scripts.get(action.lower())
        if not script:
            return f"Unknown Spotify action: {action}"

        ws.send(json.dumps({
            "id": 1,
            "method": "Runtime.evaluate",
            "params": {"expression": script, "returnByValue": True}
        }))
        res = json.loads(ws.recv())
        val = res.get("result", {}).get("result", {}).get("value", False)

        return f"Spotify {action} executed, Sir." if val else f"Spotify could not {action}, Sir."
    except Exception as e:
        return f"Error controlling Spotify: {e}"
    finally:
        if ws:
            ws.close()
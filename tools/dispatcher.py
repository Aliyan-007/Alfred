import re
from tools.system import (
    open_application,
    close_application,
    minimize_application,
    maximize_application,
    activate_application,
    lock_pc,
    shutdown_pc,
    restart_pc,
    sleep_pc,
    sign_out,
    cancel_shutdown,
    get_system_information,
    get_cpu_information,
    get_memory_information,
    get_storage_information,
    get_battery_information,
    get_network_information,
    take_screenshot,
    get_clipboard_text,
    set_clipboard_text,
    clear_clipboard,
)
from tools.file_manager import (
    find_and_open_file,
    create_folder,
    create_file,
    delete_item,
    rename_item,
)
from tools.browser import (
    browser_search,
    open_url,
    new_tab,
    close_active_tab,
    browser_action,
)
from tools.media import (
    pc_volume_up,
    pc_volume_down,
    pc_volume_mute,
    pc_volume_unmute,
    youtube_control,
    spotify_control,
)
from tools.spotify import play_spotify


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower().strip())


# =========================================================
# VOLUME DISPATCHER
# =========================================================

def handle_volume_command(text: str):
    norm = normalize(text)
    if norm in {"volume up", "increase volume", "louder", "turn it up"}:
        return pc_volume_up()
    if norm in {"volume down", "decrease volume", "softer", "lower volume", "turn it down"}:
        return pc_volume_down()
    if norm in {"mute", "mute pc", "mute audio", "silence"}:
        return pc_volume_mute()
    if norm in {"unmute", "unmute pc", "unmute audio"}:
        return pc_volume_unmute()
    return None


# =========================================================
# SYSTEM & UTILITIES DISPATCHER
# =========================================================

def handle_system_command(text: str):
    norm = normalize(text)

    # Screenshots
    if norm in {"take a screenshot", "take screenshot", "capture screen", "screenshot"}:
        return take_screenshot()

    # Clipboard
    if norm in {"read clipboard", "what is on my clipboard", "clipboard content", "check clipboard"}:
        return get_clipboard_text()
    if norm in {"clear clipboard", "empty clipboard"}:
        return clear_clipboard()
    match = re.match(r"^copy\s+(.+?)\s+to clipboard$", norm)
    if match:
        return set_clipboard_text(match.group(1))

    # Power State
    if norm in {"lock pc", "lock the pc", "lock computer"}:
        return lock_pc()
    if norm in {"shutdown pc", "turn off pc", "turn off computer"}:
        return shutdown_pc()
    if norm in {"restart pc", "restart computer", "reboot pc"}:
        return restart_pc()
    if norm in {"sleep pc", "put pc to sleep"}:
        return sleep_pc()
    if norm in {"sign out", "log out", "sign me out"}:
        return sign_out()
    if norm in {"cancel shutdown", "abort shutdown"}:
        return cancel_shutdown()

    # Telemetry
    if norm in {"system info", "system information", "pc specs", "specs"}:
        return get_system_information()
    if norm in {"cpu usage", "cpu", "processor usage"}:
        return get_cpu_information()
    if norm in {"ram usage", "ram", "memory usage"}:
        return get_memory_information()
    if norm in {"storage", "storage usage", "disk space", "disk usage"}:
        return get_storage_information()
    if norm in {"battery", "battery percentage", "battery status", "power status"}:
        return get_battery_information()
    if norm in {"ip address", "network info", "network status", "what is my ip"}:
        return get_network_information()

    # Window Management
    match = re.match(r"^(?:close|quit|exit)\s+(.+)$", norm)
    if match:
        return close_application(match.group(1))

    match = re.match(r"^(?:minimize|minimise)\s+(.+)$", norm)
    if match:
        return minimize_application(match.group(1))

    match = re.match(r"^(?:maximize|maximise)\s+(.+)$", norm)
    if match:
        return maximize_application(match.group(1))

    match = re.match(r"^(?:switch to|switch app to|focus)\s+(.+)$", norm)
    if match:
        return activate_application(match.group(1))

    return None


# =========================================================
# BROWSER DISPATCHER
# =========================================================

def handle_browser_command(text: str):
    norm = normalize(text)

    if norm in {"new tab", "open new tab"}:
        return new_tab()
    if norm in {"close tab", "close current tab"}:
        return close_active_tab()
    if norm in {"refresh", "reload tab", "refresh page"}:
        return browser_action("refresh")
    if norm in {"go back", "browser back"}:
        return browser_action("back")
    if norm in {"go forward", "browser forward"}:
        return browser_action("forward")

    # Search & Direct Navigation
    match = re.match(r"^(?:google|search for|search google for)\s+(.+)$", norm)
    if match:
        return browser_search(match.group(1), engine="google")

    match = re.match(r"^(?:open website|open url|go to)\s+(https?://\S+|\S+\.\S+)$", norm)
    if match:
        return open_url(match.group(1))

    return None


# =========================================================
# MEDIA DISPATCHER
# =========================================================

def handle_media_command(text: str):
    norm = normalize(text)

    # Spotify Search & Play
    match = re.match(r"^(?:play|listen to)\s+(.+)\s+on spotify$", norm)
    if match:
        return play_spotify(match.group(1))

    # YouTube Search & Play
    match = re.match(r"^(?:play|watch)\s+(.+)\s+on youtube$", norm)
    if match:
        return browser_search(match.group(1), engine="youtube")

    # Target controls
    if norm.startswith("spotify "):
        action = norm.replace("spotify ", "").strip()
        if action in {"pause", "resume", "play", "next", "previous"}:
            return spotify_control("resume" if action == "play" else action)

    if norm.startswith("youtube "):
        action = norm.replace("youtube ", "").strip()
        if action in {"pause", "resume", "play", "stop", "next", "previous"}:
            return youtube_control("resume" if action == "play" else action)

    # Generic Playback fallback
    if norm in {"pause", "pause music", "pause playback"}:
        res = spotify_control("pause")
        return res if "could not" not in res and "No open" not in res else youtube_control("pause")

    if norm in {"resume", "resume music", "play music"}:
        res = spotify_control("resume")
        return res if "could not" not in res and "No open" not in res else youtube_control("resume")

    if norm in {"next song", "next track"}:
        return spotify_control("next")

    if norm in {"previous song", "previous track"}:
        return spotify_control("previous")

    return None


# =========================================================
# FILE & DIRECTORY DISPATCHER
# =========================================================

def handle_file_command(text: str):
    norm = normalize(text)

    match = re.match(r"^(?:find file|locate file|search file|open file|find)\s+(.+)$", norm)
    if match:
        return find_and_open_file(match.group(1).strip())

    match = re.match(r"^create folder\s+(.+?)(?:\s+on\s+(\w+))?$", norm)
    if match:
        folder_name = match.group(1)
        location = match.group(2) or "desktop"
        return create_folder(folder_name, location)

    match = re.match(r"^create file\s+(.+?)(?:\s+on\s+(\w+))?$", norm)
    if match:
        file_name = match.group(1)
        location = match.group(2) or "desktop"
        return create_file(file_name, location)

    match = re.match(r"^(?:delete file|delete folder|delete)\s+(.+)$", norm)
    if match:
        return delete_item(match.group(1))

    match = re.match(r"^rename\s+(.+?)\s+to\s+(.+)$", norm)
    if match:
        return rename_item(match.group(1), match.group(2))

    return None


# =========================================================
# APPLICATION LAUNCH DISPATCHER (DYNAMIC)
# =========================================================

def handle_application_command(text: str):
    norm = normalize(text)
    match = re.match(r"^(?:open|launch|start)\s+(.+)$", norm)
    if match:
        return open_application(match.group(1).strip())
    return None


# =========================================================
# MASTER DISPATCHER ENTRYPOINT
# =========================================================

def handle_command(text: str):
    if not text or not text.strip():
        return None

    # 1. Volume
    res = handle_volume_command(text)
    if res is not None:
        return res

    # 2. System, Power, Window & Utilities
    res = handle_system_command(text)
    if res is not None:
        return res

    # 3. Browser
    res = handle_browser_command(text)
    if res is not None:
        return res

    # 4. Media
    res = handle_media_command(text)
    if res is not None:
        return res

    # 5. Files
    res = handle_file_command(text)
    if res is not None:
        return res

    # 6. Applications (Dynamic Indexer)
    res = handle_application_command(text)
    if res is not None:
        return res

    # 7. AI Brain Fallback
    return None
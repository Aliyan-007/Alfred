import os
import re
from pathlib import Path
from urllib.parse import quote_plus

from tools import network, bluetooth, display, hardware

from tools.system import (
    open_application,
    close_application,
    restart_application,
    minimize_application,
    maximize_application,
    activate_application,
    lock_pc,
    shutdown_pc,
    restart_pc,
    sleep_pc,
    sign_out,
    cancel_shutdown,
    empty_recycle_bin,
    take_screenshot,
    get_clipboard_text,
    set_clipboard_text,
    clear_clipboard,
    open_settings,
    get_drive_information,
    get_storage_remaining,
    record_screen,
    get_storage_information,
)

from tools.file_manager import (
    find_and_open_file,
    create_folder,
    create_file,
    delete_item,
    rename_item,
    open_folder,
    search_files,
    find_file_by_name,
    copy_file,
    move_file,
)

from tools.browser import (
    browser_search,
    open_web_destination,
    new_tab,
    close_active_tab,
    browser_action,
)

from tools.media import (
    pc_volume_up,
    pc_volume_down,
    pc_volume_mute,
    pc_volume_unmute,
)

from tools.spotify import (
    play_spotify,
    spotify_control,
)


# =========================================================
# NORMALIZATION
# =========================================================

def normalize(text: str) -> str:
    """
    Normalize spoken text so command matching is more reliable.
    """
    text = text.lower().strip()

    # Keep letters, numbers, spaces and common path/url characters.
    text = re.sub(r"[^\w\s./:\\-]", "", text)

    return re.sub(r"\s+", " ", text).strip()


# =========================================================
# VOLUME & HARDWARE
# =========================================================

def handle_volume_command(text: str):
    norm = normalize(text)

    # Volume
    if norm in {
        "volume up",
        "increase volume",
        "turn volume up",
        "louder",
        "turn it up",
    }:
        return pc_volume_up()

    if norm in {
        "volume down",
        "decrease volume",
        "turn volume down",
        "softer",
        "lower volume",
        "turn it down",
    }:
        return pc_volume_down()

    if norm in {
        "mute",
        "mute pc",
        "mute audio",
        "mute computer",
        "silence",
    }:
        return pc_volume_mute()

    if norm in {
        "unmute",
        "unmute pc",
        "unmute audio",
        "unmute computer",
    }:
        return pc_volume_unmute()

    # Brightness
    if norm in {
        "brightness up",
        "increase brightness",
        "turn brightness up",
        "brighter",
    }:
        return display.adjust_brightness(15)

    if norm in {
        "brightness down",
        "decrease brightness",
        "turn brightness down",
        "dim screen",
        "dimmer",
    }:
        return display.adjust_brightness(-15)

    match = re.match(r"^set brightness to (\d+)$", norm)
    if match:
        value = max(0, min(100, int(match.group(1))))
        return display.set_brightness(value)

    return None


# =========================================================
# SYSTEM / POWER / WINDOWS
# =========================================================

def handle_system_command(text: str):
    norm = normalize(text)

    # -----------------------------------------------------
    # SCREENSHOT
    # -----------------------------------------------------

    if norm in {
        "take a screenshot",
        "take screenshot",
        "capture screen",
        "capture screenshot",
        "screenshot",
    }:
        return take_screenshot()

    # -----------------------------------------------------
    # CLIPBOARD
    # -----------------------------------------------------

    if norm in {
        "read clipboard",
        "what is on my clipboard",
        "clipboard content",
        "check clipboard",
        "show clipboard",
    }:
        return get_clipboard_text()

    if norm in {
        "clear clipboard",
        "empty clipboard",
    }:
        return clear_clipboard()

    match = re.match(
        r"^copy (.+?) to clipboard$",
        norm,
    )

    if match:
        return set_clipboard_text(match.group(1))

    # -----------------------------------------------------
    # RECYCLE BIN
    # -----------------------------------------------------

    if norm in {
        "empty recycle bin",
        "clean recycle bin",
        "clear recycle bin",
    }:
        return empty_recycle_bin()

    # -----------------------------------------------------
    # POWER
    # -----------------------------------------------------

    if norm in {
        "lock pc",
        "lock the pc",
        "lock computer",
        "lock my computer",
    }:
        return lock_pc()

    if norm in {
        "shutdown pc",
        "shutdown computer",
        "turn off pc",
        "turn off computer",
        "shut down pc",
        "shut down computer",
    }:
        return shutdown_pc()

    if norm in {
        "restart pc",
        "restart computer",
        "reboot pc",
        "reboot computer",
    }:
        return restart_pc()

    if norm in {
        "sleep pc",
        "sleep computer",
        "put pc to sleep",
        "put computer to sleep",
    }:
        return sleep_pc()

    if norm in {
        "sign out",
        "sign me out",
        "log out",
        "logout",
    }:
        return sign_out()

    if norm in {
        "cancel shutdown",
        "abort shutdown",
        "cancel shut down",
    }:
        return cancel_shutdown()

    # -----------------------------------------------------
    # SYSTEM INFORMATION
    # -----------------------------------------------------

    if norm in {
        "system info",
        "system information",
        "pc specs",
        "computer specs",
        "computer information",
        "specs",
    }:
        return hardware.get_system_information()

    if norm in {
        "cpu usage",
        "cpu",
        "processor usage",
        "processor",
    }:
        return hardware.get_cpu_information()

    if norm in {
        "ram usage",
        "ram",
        "memory usage",
        "memory",
    }:
        return hardware.get_memory_information()

    if norm in {
        "storage",
        "storage usage",
        "disk space",
        "disk usage",
        "hard drive space",
    }:
        return hardware.get_storage_information()

    if norm in {
        "battery",
        "battery percentage",
        "battery status",
        "power status",
    }:
        return hardware.get_battery_information()

    if norm in {
        "ip address",
        "network info",
        "network status",
        "network information",
        "show network status",
        "what is my ip",
    }:
        return network.get_network_information()

    if norm in {
        "drive list",
        "show drives",
        "list drives",
        "drive information",
    }:
        return get_drive_information()

    if norm in {
        "free space",
        "storage remaining",
        "remaining storage",
        "show free space",
        "how much space is left",
    }:
        return get_storage_remaining()

    if norm in {
        "storage settings",
        "show storage settings",
        "open storage settings",
    }:
        return open_settings("storage")

    # -----------------------------------------------------
    # SETTINGS / SYSTEM TOOLS
    # -----------------------------------------------------

    if norm in {
        "settings",
        "open settings",
        "windows settings",
    }:
        return open_settings("settings")

    if norm in {
        "screen recording",
        "record screen",
        "start screen recording",
    }:
        return record_screen()

    settings_map = {
        "display settings": "display",
        "sound settings": "sound",
        "network settings": "network",
        "wifi settings": "wifi",
        "bluetooth settings": "bluetooth",
        "personalization settings": "personalization",
        "apps settings": "apps",
        "windows update": "update",
        "task manager": "task manager",
        "device manager": "device manager",
        "control panel": "control panel",
    }
    if norm in settings_map:
        return open_settings(settings_map[norm])

    if norm in {"wifi status", "wi fi status", "show wifi", "what is my wifi", "wifi info"}:
        return network.get_wifi_status()
    if norm in {"list wifi networks", "show available networks", "wifi networks", "available networks"}:
        return network.list_wifi_networks()
    if norm in {"connected wifi", "show connected wifi", "current wifi", "what wifi am i on"}:
        return network.get_connected_wifi()
    if norm in {"wifi on", "turn wifi on", "enable wifi"}:
        return network.toggle_wifi(True)
    if norm in {"wifi off", "turn wifi off", "disable wifi"}:
        return network.toggle_wifi(False)
    if norm in {"disconnect wifi", "turn wifi off now", "disconnect from wifi"}:
        return network.disconnect_wifi()
    if norm in {"bluetooth status", "is bluetooth on", "show bluetooth", "bluetooth info"}:
        return bluetooth.get_bluetooth_status()
    if norm in {"list bluetooth devices", "show bluetooth devices", "bluetooth devices", "what bluetooth devices are available"}:
        return bluetooth.list_bluetooth_devices()
    if norm in {"bluetooth on", "turn bluetooth on", "enable bluetooth"}:
        return bluetooth.toggle_bluetooth(True)
    if norm in {"bluetooth off", "turn bluetooth off", "disable bluetooth"}:
        return bluetooth.toggle_bluetooth(False)
    if norm in {"airplane mode on", "turn airplane mode on", "enable airplane mode"}:
        return network.toggle_airplane_mode(True)
    if norm in {"airplane mode off", "turn airplane mode off", "disable airplane mode"}:
        return network.toggle_airplane_mode(False)

    match = re.match(r"^(?:connect to|join) wifi\s+(.+)$", norm)
    if match:
        return network.connect_to_wifi_network(match.group(1).strip())

    match = re.match(r"^(?:connect to|pair with|connect bluetooth to)\s+(.+)$", norm)
    if match:
        return bluetooth.connect_bluetooth_device(match.group(1).strip())

    match = re.match(r"^(?:disconnect|disconnect bluetooth from)\s+(.+)$", norm)
    if match:
        return bluetooth.disconnect_bluetooth_device(match.group(1).strip())

    if norm in {"gpu", "gpu information", "graphics info", "graphics card", "video card"}:
        return hardware.get_gpu_information()
    if norm in {"running apps", "running applications", "list apps", "processes"}:
        return hardware.get_running_applications()
    if norm in {"time", "date", "time and date", "current time", "current date", "what time is it", "what date is it"}:
        return hardware.get_current_datetime()

    if norm in {"full network status", "show full network status", "network diagnostics"}:
        return network.get_network_status()

    # -----------------------------------------------------
    # APPLICATION CONTROL
    # -----------------------------------------------------

    if norm in {"close app", "close active app", "quit app"}:
        hwnd = None
        try:
            import ctypes
            hwnd = ctypes.windll.user32.GetForegroundWindow()
        except Exception:
            hwnd = None
        if hwnd is None:
            return "I couldn't find the active app to close, Sir."
        try:
            import ctypes
            ctypes.windll.user32.PostMessageW(hwnd, 0x0010, 0, 0)
            return "Closed the active app, Sir."
        except Exception as error:
            return f"I couldn't close the active app, Sir. {error}"

    if norm in {"minimize app", "minimize active app"}:
        try:
            import ctypes
            hwnd = ctypes.windll.user32.GetForegroundWindow()
            ctypes.windll.user32.ShowWindow(hwnd, 6)
            return "Minimized the active app, Sir."
        except Exception as error:
            return f"I couldn't minimize the active app, Sir. {error}"

    if norm in {"maximize app", "maximize active app"}:
        try:
            import ctypes
            hwnd = ctypes.windll.user32.GetForegroundWindow()
            ctypes.windll.user32.ShowWindow(hwnd, 3)
            ctypes.windll.user32.SetForegroundWindow(hwnd)
            return "Maximized the active app, Sir."
        except Exception as error:
            return f"I couldn't maximize the active app, Sir. {error}"

    if norm in {"switch app", "switch active app", "focus app"}:
        try:
            import ctypes
            hwnd = ctypes.windll.user32.GetForegroundWindow()
            ctypes.windll.user32.ShowWindow(hwnd, 9)
            ctypes.windll.user32.SetForegroundWindow(hwnd)
            return "Focused the active app, Sir."
        except Exception as error:
            return f"I couldn't switch to the active app, Sir. {error}"

    # Restart application
    match = re.match(
        r"^restart(?: app| application)? (.+)$",
        norm,
    )

    if match:
        target = match.group(1).strip()

        if target not in {
            "pc",
            "computer",
            "windows",
        }:
            return restart_application(target)

    # Close application
    match = re.match(
        r"^(?:close|quit|exit)(?: app| application)? (.+)$",
        norm,
    )

    if match:
        return close_application(match.group(1).strip())

    # Minimize application
    match = re.match(
        r"^(?:minimize|minimise)(?: app| application)? (.+)$",
        norm,
    )

    if match:
        return minimize_application(match.group(1).strip())

    # Maximize application
    match = re.match(
        r"^(?:maximize|maximise)(?: app| application)? (.+)$",
        norm,
    )

    if match:
        return maximize_application(match.group(1).strip())

    # Focus / switch application
    match = re.match(
        r"^(?:switch to|switch app to|focus|activate)(?: app)? (.+)$",
        norm,
    )

    if match:
        return activate_application(match.group(1).strip())

    return None


# =========================================================
# BROWSER & WEB SEARCH
# =========================================================

def handle_browser_command(text: str):
    norm = normalize(text)

    # -----------------------------------------------------
    # OPEN BROWSER
    # -----------------------------------------------------

    if norm in {
        "open browser",
        "open brave",
        "open chrome",
        "launch browser",
    }:
        return open_web_destination("https://www.google.com")

    # -----------------------------------------------------
    # TABS
    # -----------------------------------------------------

    if norm in {
        "new tab",
        "open new tab",
        "create new tab",
    }:
        return new_tab()

    if norm in {
        "close tab",
        "close current tab",
        "close this tab",
    }:
        return close_active_tab()

    # -----------------------------------------------------
    # NAVIGATION
    # -----------------------------------------------------

    if norm in {
        "refresh",
        "reload",
        "reload tab",
        "refresh page",
        "reload page",
    }:
        return browser_action("refresh")

    if norm in {
        "go back",
        "browser back",
        "back",
    }:
        return browser_action("back")

    if norm in {
        "go forward",
        "browser forward",
        "forward",
    }:
        return browser_action("forward")

    # -----------------------------------------------------
    # WIKIPEDIA
    # -----------------------------------------------------

    match = re.match(
        r"^(?:search wikipedia for|wikipedia)\s+(.+)$",
        norm,
    )

    if match:
        return browser_search(match.group(1), engine="wikipedia")

    match = re.match(r"^(?:image search|images for|search images for)\s+(.+)$", norm)
    if match:
        return browser_search(match.group(1), engine="image")

    match = re.match(r"^(?:news search|search news for|news for)\s+(.+)$", norm)
    if match:
        return browser_search(match.group(1), engine="news")

    if norm in {"downloads", "open downloads", "show downloads"}:
        return open_web_destination("https://downloads")

    # -----------------------------------------------------
    # GOOGLE / WEB SEARCH
    # -----------------------------------------------------

    match = re.match(
        r"^(?:google|search for|search google for|search web for)\s+(.+)$",
        norm,
    )

    if match:
        return browser_search(
            match.group(1),
            engine="google",
        )

    # -----------------------------------------------------
    # DIRECT WEBSITE
    # -----------------------------------------------------

    match = re.match(
        r"^(?:open website|open url|go to)\s+(.+)$",
        norm,
    )

    if match:
        destination = match.group(1).strip()

        # If user says "youtube.com", etc.
        if not re.match(r"^https?://", destination):
            destination = "https://" + destination

        return open_web_destination(destination)

    return None


# =========================================================
# MEDIA & STREAMING
# =========================================================

def handle_media_command(text: str):
    norm = normalize(text)

    # -----------------------------------------------------
    # SPOTIFY
    # -----------------------------------------------------

    match = re.match(
        r"^(?:play|listen to)\s+(.+?)(?:\s+on spotify)?$",
        norm,
    )

    if match and "youtube" not in norm:
        query = match.group(1).strip()

        # Don't treat generic commands as songs.
        if query not in {
            "music",
            "song",
            "spotify",
        }:
            return play_spotify(query)

    # -----------------------------------------------------
    # YOUTUBE SEARCH
    # -----------------------------------------------------

    match = re.match(
        r"^(?:search youtube for|search youtube|on youtube search|"
        r"on youtube search about|search about)\s+(.+)$",
        norm,
    )

    if match:
        query = match.group(1).strip()

        return browser_search(
            query,
            engine="youtube",
        )

    # -----------------------------------------------------
    # YOUTUBE PLAY
    # -----------------------------------------------------

    match = re.match(
        r"^(?:play|watch)\s+(.+?)\s+on youtube$",
        norm,
    )

    if match:
        return browser_search(
            match.group(1).strip(),
            engine="youtube",
        )

    # -----------------------------------------------------
    # SPOTIFY CONTROLS
    # -----------------------------------------------------

    if norm in {
        "pause",
        "pause music",
        "pause playback",
        "pause song",
    }:
        return spotify_control("pause")

    if norm in {
        "resume",
        "resume music",
        "resume playback",
        "play music",
    }:
        return spotify_control("resume")

    if norm in {
        "next",
        "next song",
        "next track",
        "skip song",
        "skip track",
    }:
        return spotify_control("next")

    if norm in {
        "previous",
        "previous song",
        "previous track",
        "last song",
    }:
        return spotify_control("previous")

    return None


# =========================================================
# FILES & DIRECTORIES
# =========================================================

def handle_file_command(text: str):
    norm = normalize(text)

    # -----------------------------------------------------
    # QUICK FOLDERS
    # -----------------------------------------------------

    quick_folders = {
        "downloads": Path.home() / "Downloads",
        "documents": Path.home() / "Documents",
        "desktop": Path.home() / "Desktop",
        "pictures": Path.home() / "Pictures",
        "videos": Path.home() / "Videos",
        "music": Path.home() / "Music",
    }

    match = re.match(
        r"^open (downloads|documents|desktop|pictures|videos|music)"
        r"(?: folder)?$",
        norm,
    )

    if match:
        folder_name = match.group(1)
        folder_path = quick_folders.get(folder_name)

        if folder_path and folder_path.exists():
            os.startfile(str(folder_path))

            return (
                f"Opened {folder_name.capitalize()} folder, Sir."
            )

    match = re.match(r"^open folder\s+(.+)$", norm)
    if match:
        return open_folder(match.group(1).strip())

    # -----------------------------------------------------
    # FIND / OPEN FILE
    # -----------------------------------------------------

    match = re.match(
        r"^(?:find file|locate file|search file|open file|find)\s+(.+)$",
        norm,
    )

    if match:
        return find_and_open_file(
            match.group(1).strip()
        )

    match = re.match(r"^(?:search files|search for files)\s+(.+)$", norm)
    if match:
        return str(search_files(match.group(1).strip(), max_results=10))

    match = re.match(r"^find file by name\s+(.+)$", norm)
    if match:
        return str(find_file_by_name(match.group(1).strip(), max_results=10))

    # -----------------------------------------------------
    # CREATE FOLDER
    # -----------------------------------------------------

    match = re.match(
        r"^create folder\s+(.+?)(?:\s+on\s+(\w+))?$",
        norm,
    )

    if match:
        name = match.group(1).strip()
        location = match.group(2) or "desktop"

        return create_folder(
            name,
            location,
        )

    # -----------------------------------------------------
    # CREATE FILE
    # -----------------------------------------------------

    match = re.match(
        r"^create file\s+(.+?)(?:\s+on\s+(\w+))?$",
        norm,
    )

    if match:
        name = match.group(1).strip()
        location = match.group(2) or "desktop"

        return create_file(
            name,
            location,
        )

    # -----------------------------------------------------
    # DELETE
    # -----------------------------------------------------

    match = re.match(
        r"^(?:delete file|delete folder|delete)\s+(.+)$",
        norm,
    )

    if match:
        return delete_item(
            match.group(1).strip()
        )

    # -----------------------------------------------------
    # RENAME
    # -----------------------------------------------------

    match = re.match(
        r"^rename\s+(.+?)\s+to\s+(.+)$",
        norm,
    )

    if match:
        return rename_item(
            match.group(1).strip(),
            match.group(2).strip(),
        )

    match = re.match(r"^copy\s+(.+?)\s+to\s+(.+)$", norm)
    if match:
        return copy_file(match.group(1).strip(), match.group(2).strip())

    match = re.match(r"^move\s+(.+?)\s+to\s+(.+)$", norm)
    if match:
        return move_file(match.group(1).strip(), match.group(2).strip())

    return None


# =========================================================
# APPLICATION LAUNCHER
# =========================================================

def handle_application_command(text: str):
    norm = normalize(text)

    cleaned = re.sub(
        r"^(?:i want to|please|can you|could you)\s+",
        "",
        norm,
    )

    # "open X on brave" / "open X on chrome"
    cleaned = re.sub(
        r"\s+on\s+(?:brave|browser|chrome)$",
        "",
        cleaned,
    )

    match = re.match(
        r"^(?:open|launch|start)\s+(.+)$",
        cleaned,
    )

    if match:
        target = match.group(1).strip()

        return open_application(target)

    return None


# =========================================================
# MASTER DISPATCHER
# =========================================================

def handle_command(text: str):
    """
    Main local command dispatcher.

    Returns:
        Command result if handled locally.
        None if the command should fall through to the AI brain.
    """

    if not text or not text.strip():
        return None

    # 1. Volume / brightness
    result = handle_volume_command(text)

    if result is not None:
        return result

    # 2. System / power / windows
    result = handle_system_command(text)

    if result is not None:
        return result

    # 3. Browser / web
    result = handle_browser_command(text)

    if result is not None:
        return result

    # 4. Media / Spotify / YouTube
    result = handle_media_command(text)

    if result is not None:
        return result

    # 5. Files / folders
    result = handle_file_command(text)

    if result is not None:
        return result

    # 6. Applications
    result = handle_application_command(text)

    if result is not None:
        return result

    # Nothing matched locally.
    # main.py can send it to the AI brain.
    return None
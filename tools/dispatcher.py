import re

from tools.system import open_application
from tools.file_finder import find_and_open_file

from tools.spotify import (
    play_spotify,
    spotify_control,
)

from tools.youtube import (
    play_youtube,
    youtube_control,
)

from tools.media import (
    pc_volume_up,
    pc_volume_down,
    pc_volume_mute,
    pc_volume_unmute,
)
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
)

# =========================================================
# APPLICATION ALIASES
# =========================================================

APP_ALIASES = {
    "notepad": "notepad",
    "calculator": "calculator",
    "calc": "calculator",
    "explorer": "explorer",
    "file explorer": "file explorer",
    "chrome": "chrome",
    "brave": "brave",
    "brave browser": "brave",
    "vscode": "vscode",
    "vs code": "vs code",
    "visual studio code": "vscode",
}


# =========================================================
# NORMALIZE TEXT
# =========================================================

def normalize_text(
    text: str,
) -> str:
    return (
        text
        .lower()
        .strip()
    )


# =========================================================
# MEDIA PLAY COMMANDS
# =========================================================

def handle_media_play(
    text: str,
):
    """
    Handle commands such as:

        play Blinding Lights on Spotify
        play Spider-Man trailer on YouTube
        watch Sidemen on YouTube
    """

    normalized = normalize_text(
        text
    )

    # -----------------------------------------------------
    # Spotify
    # -----------------------------------------------------

    match = re.match(
        r"^\s*(?:play|listen to|put on)\s+(.+?)"
        r"\s+(?:on|in)\s+spotify\s*$",
        normalized,
        re.IGNORECASE,
    )

    if match:

        query = match.group(1).strip()

        return play_spotify(
            query
        )

    match = re.match(
        r"^\s*(?:search|find)\s+spotify\s+for\s+(.+?)\s*$",
        normalized,
        re.IGNORECASE,
    )

    if match:

        query = match.group(1).strip()

        return play_spotify(
            query
        )

    # -----------------------------------------------------
    # YouTube
    # -----------------------------------------------------

    match = re.match(
        r"^\s*(?:play|watch)\s+(.+?)"
        r"\s+(?:on|in)\s+youtube\s*$",
        normalized,
        re.IGNORECASE,
    )

    if match:

        query = match.group(1).strip()

        return play_youtube(
            query
        )

    match = re.match(
        r"^\s*(?:search|find)\s+youtube\s+for\s+(.+?)\s*$",
        normalized,
        re.IGNORECASE,
    )

    if match:

        query = match.group(1).strip()

        return play_youtube(
            query
        )

    return None


# =========================================================
# EXPLICIT SPOTIFY CONTROLS
# =========================================================

def handle_spotify_control(
    text: str,
):
    normalized = normalize_text(
        text
    )

    patterns = {

        "pause": [
            r"^pause spotify$",
            r"^pause spotify music$",
            r"^stop spotify$",
        ],

        "resume": [
            r"^resume spotify$",
            r"^resume spotify music$",
            r"^play spotify$",
            r"^continue spotify$",
        ],

        "next": [
            r"^next song on spotify$",
            r"^next on spotify$",
            r"^skip song on spotify$",
            r"^skip on spotify$",
        ],

        "previous": [
            r"^previous song on spotify$",
            r"^previous on spotify$",
            r"^go back on spotify$",
        ],
    }

    for action, expressions in patterns.items():

        if any(
            re.match(
                pattern,
                normalized,
            )
            for pattern in expressions
        ):

            return spotify_control(
                action
            )

    return None


# =========================================================
# EXPLICIT YOUTUBE CONTROLS
# =========================================================

def handle_youtube_control(
    text: str,
):
    normalized = normalize_text(
        text
    )

    patterns = {

        "pause": [
            r"^pause youtube$",
            r"^pause youtube video$",
            r"^pause the video$",
        ],

        "resume": [
            r"^resume youtube$",
            r"^resume youtube video$",
            r"^resume the video$",
            r"^continue youtube$",
            r"^continue the video$",
        ],

        "play": [
            r"^play youtube$",
            r"^play the video$",
        ],

        "stop": [
            r"^stop youtube$",
            r"^stop the video$",
        ],

        "next": [
            r"^next video on youtube$",
            r"^next on youtube$",
            r"^skip youtube video$",
        ],

        "previous": [
            r"^previous video on youtube$",
            r"^previous on youtube$",
            r"^go back on youtube$",
        ],

        "volume_up": [
            r"^youtube volume up$",
            r"^increase youtube volume$",
            r"^make youtube louder$",
        ],

        "volume_down": [
            r"^youtube volume down$",
            r"^decrease youtube volume$",
            r"^make youtube quieter$",
        ],

        "fullscreen": [
            r"^fullscreen youtube$",
            r"^youtube fullscreen$",
            r"^put youtube in fullscreen$",
            r"^make youtube fullscreen$",
            r"^fullscreen the video$",
            r"^make the video fullscreen$",
            r"^make this video fullscreen$",
        ],
    }

    for action, expressions in patterns.items():

        if any(
            re.match(
                pattern,
                normalized,
            )
            for pattern in expressions
        ):

            return youtube_control(
                action
            )

    return None


# =========================================================
# GENERIC MEDIA CONTROLS
# =========================================================

def handle_generic_media_control(
    text: str,
):
    """
    Handle simple commands without an explicit service.

    Examples:

        pause
        resume
        next
        previous
    """

    normalized = normalize_text(
        text
    )

    # We deliberately do not guess between Spotify and
    # YouTube here unless the command is completely generic.
    #
    # Your AI brain can make the intelligent decision for
    # natural-language commands.

    if normalized in {
        "pause",
        "pause music",
    }:

        return spotify_control(
            "pause"
        )

    if normalized in {
        "resume",
        "resume music",
        "continue",
        "continue playing",
    }:

        return spotify_control(
            "resume"
        )

    if normalized in {
        "next",
        "next song",
        "next track",
    }:

        return spotify_control(
            "next"
        )

    if normalized in {
        "previous",
        "previous song",
        "previous track",
    }:

        return spotify_control(
            "previous"
        )

    return None


# =========================================================
# PC MASTER VOLUME
# =========================================================

def handle_pc_volume(
    text: str,
):
    normalized = normalize_text(
        text
    )

    # -----------------------------------------------------
    # Volume up
    # -----------------------------------------------------

    if normalized in {
        "volume up",
        "increase volume",
        "turn volume up",
        "turn the volume up",
        "make it louder",
        "make the computer louder",
        "make the pc louder",
        "louder",
        "increase pc volume",
        "increase computer volume",
    }:

        return pc_volume_up()

    # -----------------------------------------------------
    # Volume down
    # -----------------------------------------------------

    if normalized in {
        "volume down",
        "decrease volume",
        "turn volume down",
        "turn the volume down",
        "make it quieter",
        "make the computer quieter",
        "make the pc quieter",
        "quieter",
        "lower the volume",
        "decrease pc volume",
        "decrease computer volume",
    }:

        return pc_volume_down()

    # -----------------------------------------------------
    # Mute
    # -----------------------------------------------------

    if normalized in {
        "mute",
        "mute pc",
        "mute computer",
        "mute volume",
        "mute the computer",
        "mute the pc",
    }:

        return pc_volume_mute()

    # -----------------------------------------------------
    # Unmute
    # -----------------------------------------------------

    if normalized in {
        "unmute",
        "unmute pc",
        "unmute computer",
        "unmute volume",
        "unmute the computer",
        "unmute the pc",
    }:

        return pc_volume_unmute()

    return None


# =========================================================
# WINDOWS APPLICATION COMMANDS
# =========================================================

def handle_application_command(
    text: str,
):
    """
    Open approved Windows applications.
    """

    match = re.match(
        r"^\s*(?:open|launch|start)\s+(.+?)\s*$",
        text,
        re.IGNORECASE,
    )

    if not match:
        return None

    requested_app = (
        match.group(1)
        .strip()
        .lower()
    )

    app = APP_ALIASES.get(
        requested_app
    )

    if app is None:
        return None

    return open_application(
        app
    )

# =========================================================
# WINDOWS SYSTEM COMMANDS
# =========================================================

def handle_system_command(
    text: str,
):

    normalized = normalize_text(
        text
    )

    # -----------------------------------------------------
    # LOCK
    # -----------------------------------------------------

    if normalized in {
        "lock pc",
        "lock the pc",
        "lock computer",
        "lock the computer",
        "lock my pc",
        "lock my computer",
    }:

        return lock_pc()

    # -----------------------------------------------------
    # SHUTDOWN
    # -----------------------------------------------------

    if normalized in {
        "shutdown",
        "shut down",
        "shutdown pc",
        "shut down pc",
        "shutdown computer",
        "shut down computer",
        "turn off pc",
        "turn off computer",
    }:

        return shutdown_pc()

    # -----------------------------------------------------
    # RESTART
    # -----------------------------------------------------

    if normalized in {
        "restart",
        "restart pc",
        "restart computer",
        "reboot",
        "reboot pc",
        "reboot computer",
    }:

        return restart_pc()

    # -----------------------------------------------------
    # SLEEP
    # -----------------------------------------------------

    if normalized in {
        "sleep",
        "sleep pc",
        "sleep computer",
        "put pc to sleep",
        "put computer to sleep",
    }:

        return sleep_pc()

    # -----------------------------------------------------
    # SIGN OUT
    # -----------------------------------------------------

    if normalized in {
        "sign out",
        "sign me out",
        "log out",
        "log me out",
    }:

        return sign_out()

    # -----------------------------------------------------
    # CANCEL SHUTDOWN
    # -----------------------------------------------------

    if normalized in {
        "cancel shutdown",
        "cancel the shutdown",
        "abort shutdown",
    }:

        return cancel_shutdown()

    # -----------------------------------------------------
    # SYSTEM INFORMATION
    # -----------------------------------------------------

    if normalized in {
        "system information",
        "system info",
        "pc information",
        "pc info",
        "computer information",
        "computer info",
        "what are my pc specs",
        "show pc specs",
    }:

        return get_system_information()

    # -----------------------------------------------------
    # CPU
    # -----------------------------------------------------

    if normalized in {
        "cpu usage",
        "cpu status",
        "processor usage",
        "how much cpu am i using",
    }:

        return get_cpu_information()

    # -----------------------------------------------------
    # RAM
    # -----------------------------------------------------

    if normalized in {
        "ram usage",
        "ram status",
        "memory usage",
        "memory status",
        "how much ram am i using",
    }:

        return get_memory_information()

    # -----------------------------------------------------
    # STORAGE
    # -----------------------------------------------------

    if normalized in {
        "storage",
        "storage usage",
        "disk usage",
        "disk space",
        "how much storage do i have",
        "how much storage is left",
    }:

        return get_storage_information()

    # -----------------------------------------------------
    # CLOSE APPLICATION
    # -----------------------------------------------------

    match = re.match(
        r"^(?:close|quit|exit)\s+(.+)$",
        normalized,
    )

    if match:

        application = match.group(
            1
        ).strip()

        return close_application(
            application
        )

    # -----------------------------------------------------
    # MINIMIZE APPLICATION
    # -----------------------------------------------------

    match = re.match(
        r"^(?:minimize|minimise)\s+(.+)$",
        normalized,
    )

    if match:

        application = match.group(
            1
        ).strip()

        return minimize_application(
            application
        )

    # -----------------------------------------------------
    # MAXIMIZE APPLICATION
    # -----------------------------------------------------

    match = re.match(
        r"^(?:maximize|maximise)\s+(.+)$",
        normalized,
    )

    if match:

        application = match.group(
            1
        ).strip()

        return maximize_application(
            application
        )

    # -----------------------------------------------------
    # SWITCH APPLICATION
    # -----------------------------------------------------

    match = re.match(
        r"^(?:switch to|go to|bring up)\s+(.+)$",
        normalized,
    )

    if match:

        application = match.group(
            1
        ).strip()

        return activate_application(
            application
        )

    return None
# =========================================================
# MAIN DISPATCHER
# =========================================================

def handle_command(
    user_input: str,
):
    """
    Route exact/local commands.

    Natural-language commands that do not match these
    patterns are passed to the AI brain by main.py.
    """

    if not user_input:
        return None

    text = user_input.strip()

    # =====================================================
    # WINDOWS SYSTEM
    # =====================================================

    result = handle_system_command(
        text
    )

    if result is not None:
        return result

    # =====================================================
    # PC VOLUME
    # =====================================================

    result = handle_pc_volume(
        text
    )

    if result is not None:
        return result

    # =====================================================
    # SPOTIFY PLAY
    # =====================================================

    result = handle_media_play(
        text
    )

    if result is not None:
        return result

    # =====================================================
    # EXPLICIT SPOTIFY CONTROLS
    # =====================================================

    result = handle_spotify_control(
        text
    )

    if result is not None:
        return result

    # =====================================================
    # EXPLICIT YOUTUBE CONTROLS
    # =====================================================

    result = handle_youtube_control(
        text
    )

    if result is not None:
        return result

    # =====================================================
    # GENERIC MEDIA
    # =====================================================

    result = handle_generic_media_control(
        text
    )

    if result is not None:
        return result

    # =====================================================
    # WINDOWS APPLICATION
    # =====================================================

    result = handle_application_command(
        text
    )

    if result is not None:
        return result

    # =====================================================
    # NO EXACT COMMAND
    # =====================================================
    
    # =====================================================
    # FILE COMMAND
    # =====================================================

    result = handle_file_command(
        text
    )

    if result is not None:
        return result
    
    return None

def handle_file_command(
    text: str,
):
    normalized = normalize_text(text)

    patterns = [
        r"^find (.+)$",
        r"^locate (.+)$",
        r"^open file (.+)$",
        r"^open the file (.+)$",
        r"^find file (.+)$",
        r"^find the file (.+)$",
    ]

    for pattern in patterns:

        match = re.match(
            pattern,
            normalized,
            re.IGNORECASE,
        )

        if match:

            query = match.group(1).strip()

            # Prevent ordinary "find/open" application
            # commands from being treated as file requests.
            if not query:
                return None

            return find_and_open_file(
                query
            )

        

    return None
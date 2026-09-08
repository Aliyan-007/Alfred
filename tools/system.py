import os
import subprocess
import time
from pathlib import Path


# =========================================================
# APPLICATIONS
# =========================================================

APPLICATIONS = {
    "notepad": ["notepad.exe"],
    "calculator": ["calc.exe"],
    "calc": ["calc.exe"],

    "file explorer": ["explorer.exe"],
    "explorer": ["explorer.exe"],

    "chrome": [
        "cmd",
        "/c",
        "start",
        "",
        "chrome",
    ],

    "brave": [
        r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe"
    ],

    "edge": [
        "cmd",
        "/c",
        "start",
        "",
        "msedge",
    ],

    "vscode": ["code"],
    "vs code": ["code"],

    "visual studio code": ["code"],

    "task manager": [
        "taskmgr.exe"
    ],

    "control panel": [
        "control.exe"
    ],

    "settings": [
        "cmd",
        "/c",
        "start",
        "",
        "ms-settings:"
    ],

    "command prompt": [
        "cmd.exe"
    ],

    "cmd": [
        "cmd.exe"
    ],

    "powershell": [
        "powershell.exe"
    ],

    "terminal": [
        "wt.exe"
    ],
}


# =========================================================
# NORMALIZE
# =========================================================

def normalize_text(text: str) -> str:
    return (
        text
        .lower()
        .strip()
    )


# =========================================================
# OPEN APPLICATION
# =========================================================

def open_application(application: str) -> str:

    application = normalize_text(
        application
    )

    command = APPLICATIONS.get(
        application
    )

    if command is None:
        return (
            f"I don't have permission to open "
            f"'{application}', Sir."
        )

    try:

        subprocess.Popen(
            command,
            shell=False,
        )

        return (
            f"Opened {application}, Sir."
        )

    except Exception as error:

        return (
            f"I couldn't open {application}, Sir. "
            f"{error}"
        )


# =========================================================
# FIND WINDOW
# =========================================================

def _get_windows():

    try:

        import ctypes
        from ctypes import wintypes

        user32 = ctypes.windll.user32

        windows = []

        EnumWindowsProc = ctypes.WINFUNCTYPE(
            ctypes.c_bool,
            wintypes.HWND,
            wintypes.LPARAM,
        )

        def callback(hwnd, _):

            if not user32.IsWindowVisible(hwnd):
                return True

            length = user32.GetWindowTextLengthW(
                hwnd
            )

            if length <= 0:
                return True

            buffer = ctypes.create_unicode_buffer(
                length + 1
            )

            user32.GetWindowTextW(
                hwnd,
                buffer,
                length + 1,
            )

            title = buffer.value.strip()

            if title:
                windows.append(
                    (hwnd, title)
                )

            return True

        user32.EnumWindows(
            EnumWindowsProc(callback),
            0,
        )

        return windows

    except Exception:
        return []


# =========================================================
# FIND WINDOW BY NAME
# =========================================================

def find_window(
    application: str,
):

    wanted = normalize_text(
        application
    )

    for hwnd, title in _get_windows():

        if wanted in normalize_text(title):
            return hwnd

    return None


# =========================================================
# ACTIVATE APPLICATION
# =========================================================

def activate_application(
    application: str,
) -> str:

    hwnd = find_window(
        application
    )

    if hwnd is None:
        return (
            f"I couldn't find an open window for "
            f"{application}, Sir."
        )

    try:

        import ctypes

        ctypes.windll.user32.ShowWindow(
            hwnd,
            9,  # SW_RESTORE
        )

        ctypes.windll.user32.SetForegroundWindow(
            hwnd
        )

        return (
            f"Switched to {application}, Sir."
        )

    except Exception as error:

        return (
            f"I couldn't switch to {application}, Sir. "
            f"{error}"
        )


# =========================================================
# CLOSE APPLICATION
# =========================================================

def close_application(
    application: str,
) -> str:

    hwnd = find_window(
        application
    )

    if hwnd is None:
        return (
            f"I couldn't find an open window for "
            f"{application}, Sir."
        )

    try:

        import ctypes

        WM_CLOSE = 0x0010

        ctypes.windll.user32.PostMessageW(
            hwnd,
            WM_CLOSE,
            0,
            0,
        )

        return (
            f"Closed {application}, Sir."
        )

    except Exception as error:

        return (
            f"I couldn't close {application}, Sir. "
            f"{error}"
        )


# =========================================================
# MINIMIZE APPLICATION
# =========================================================

def minimize_application(
    application: str,
) -> str:

    hwnd = find_window(
        application
    )

    if hwnd is None:
        return (
            f"I couldn't find {application}, Sir."
        )

    try:

        import ctypes

        ctypes.windll.user32.ShowWindow(
            hwnd,
            6,  # SW_MINIMIZE
        )

        return (
            f"Minimized {application}, Sir."
        )

    except Exception as error:

        return (
            f"I couldn't minimize {application}, Sir. "
            f"{error}"
        )


# =========================================================
# MAXIMIZE APPLICATION
# =========================================================

def maximize_application(
    application: str,
) -> str:

    hwnd = find_window(
        application
    )

    if hwnd is None:
        return (
            f"I couldn't find {application}, Sir."
        )

    try:

        import ctypes

        ctypes.windll.user32.ShowWindow(
            hwnd,
            3,  # SW_MAXIMIZE
        )

        ctypes.windll.user32.SetForegroundWindow(
            hwnd
        )

        return (
            f"Maximized {application}, Sir."
        )

    except Exception as error:

        return (
            f"I couldn't maximize {application}, Sir. "
            f"{error}"
        )


# =========================================================
# LOCK PC
# =========================================================

def lock_pc():

    try:

        import ctypes

        ctypes.windll.user32.LockWorkStation()

        return (
            "The PC is locked, Sir."
        )

    except Exception as error:

        return (
            f"I couldn't lock the PC, Sir. "
            f"{error}"
        )


# =========================================================
# SHUTDOWN
# =========================================================

def shutdown_pc(
    delay_seconds: int = 0,
):

    try:

        subprocess.Popen(
            [
                "shutdown",
                "/s",
                "/t",
                str(delay_seconds),
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

        return (
            "The PC is shutting down, Sir."
        )

    except Exception as error:

        return (
            f"I couldn't shut down the PC, Sir. "
            f"{error}"
        )


# =========================================================
# RESTART
# =========================================================

def restart_pc(
    delay_seconds: int = 0,
):

    try:

        subprocess.Popen(
            [
                "shutdown",
                "/r",
                "/t",
                str(delay_seconds),
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

        return (
            "The PC is restarting, Sir."
        )

    except Exception as error:

        return (
            f"I couldn't restart the PC, Sir. "
            f"{error}"
        )


# =========================================================
# SLEEP
# =========================================================

def sleep_pc():

    try:

        subprocess.Popen(
            [
                "rundll32.exe",
                "powrprof.dll,SetSuspendState",
                "0",
                "1",
                "0",
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

        return (
            "Putting the PC to sleep, Sir."
        )

    except Exception as error:

        return (
            f"I couldn't put the PC to sleep, Sir. "
            f"{error}"
        )


# =========================================================
# SIGN OUT
# =========================================================

def sign_out():

    try:

        subprocess.Popen(
            [
                "shutdown",
                "/l",
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

        return (
            "Signing you out, Sir."
        )

    except Exception as error:

        return (
            f"I couldn't sign you out, Sir. "
            f"{error}"
        )


# =========================================================
# CANCEL SHUTDOWN
# =========================================================

def cancel_shutdown():

    try:

        subprocess.Popen(
            [
                "shutdown",
                "/a",
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

        return (
            "The scheduled shutdown has been cancelled, Sir."
        )

    except Exception as error:

        return (
            f"I couldn't cancel the shutdown, Sir. "
            f"{error}"
        )


# =========================================================
# SYSTEM INFORMATION
# =========================================================

def get_system_information():

    try:

        import platform

        return (
            f"Operating system: {platform.system()} "
            f"{platform.release()}. "
            f"Computer: {platform.node()}. "
            f"Processor: {platform.processor()}."
        )

    except Exception as error:

        return (
            f"I couldn't read the system information, Sir. "
            f"{error}"
        )


# =========================================================
# RAM INFORMATION
# =========================================================

def get_memory_information():

    try:

        import psutil

        memory = psutil.virtual_memory()

        used_gb = memory.used / (
            1024 ** 3
        )

        total_gb = memory.total / (
            1024 ** 3
        )

        percent = memory.percent

        return (
            f"RAM usage is {percent:.0f} percent. "
            f"{used_gb:.1f} GB of "
            f"{total_gb:.1f} GB is currently in use, Sir."
        )

    except ImportError:

        return (
            "The psutil package is required for RAM "
            "information, Sir."
        )

    except Exception as error:

        return (
            f"I couldn't read RAM usage, Sir. "
            f"{error}"
        )


# =========================================================
# CPU INFORMATION
# =========================================================

def get_cpu_information():

    try:

        import psutil

        usage = psutil.cpu_percent(
            interval=0.5
        )

        cores = psutil.cpu_count(
            logical=True
        )

        return (
            f"CPU usage is {usage:.0f} percent "
            f"across {cores} logical processors, Sir."
        )

    except ImportError:

        return (
            "The psutil package is required for CPU "
            "information, Sir."
        )

    except Exception as error:

        return (
            f"I couldn't read CPU usage, Sir. "
            f"{error}"
        )


# =========================================================
# STORAGE INFORMATION
# =========================================================

def get_storage_information():

    try:

        import psutil

        total = 0
        used = 0

        for partition in psutil.disk_partitions():

            try:

                usage = psutil.disk_usage(
                    partition.mountpoint
                )

                total += usage.total
                used += usage.used

            except Exception:
                continue

        if total == 0:
            return (
                "I couldn't read the storage information, Sir."
            )

        total_gb = total / (
            1024 ** 3
        )

        used_gb = used / (
            1024 ** 3
        )

        percent = (
            used / total
        ) * 100

        return (
            f"Storage usage is {percent:.0f} percent. "
            f"{used_gb:.1f} GB of {total_gb:.1f} GB "
            f"is currently used, Sir."
        )

    except ImportError:

        return (
            "The psutil package is required for "
            "storage information, Sir."
        )

    except Exception as error:

        return (
            f"I couldn't read storage information, Sir. "
            f"{error}"
        )


# =========================================================
# TEST
# =========================================================

if __name__ == "__main__":

    print(
        open_application("notepad")
    )

    time.sleep(1)

    print(
        get_system_information()
    )

    print(
        get_cpu_information()
    )

    print(
        get_memory_information()
    )

    print(
        get_storage_information()
    )
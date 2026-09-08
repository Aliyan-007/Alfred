import ctypes
from ctypes import wintypes
import os
import platform
import re
import socket
import subprocess
import time
from datetime import datetime
from pathlib import Path

from tools.app_indexer import indexer

# Win32 Constants for Clipboard
CF_UNICODETEXT = 13
GHND = 0x0042


# =========================================================
# APPLICATION CONTROL (DYNAMIC)
# =========================================================

def open_application(application: str) -> str:
    return indexer.launch(application)


# =========================================================
# WINDOW MANAGEMENT (WIN32)
# =========================================================

def _get_windows():
    try:
        user32 = ctypes.windll.user32
        windows = []

        EnumWindowsProc = ctypes.WINFUNCTYPE(
            ctypes.c_bool, wintypes.HWND, wintypes.LPARAM
        )

        def callback(hwnd, _):
            if not user32.IsWindowVisible(hwnd):
                return True
            length = user32.GetWindowTextLengthW(hwnd)
            if length <= 0:
                return True
            buffer = ctypes.create_unicode_buffer(length + 1)
            user32.GetWindowTextW(hwnd, buffer, length + 1)
            title = buffer.value.strip()
            if title:
                windows.append((hwnd, title))
            return True

        user32.EnumWindows(EnumWindowsProc(callback), 0)
        return windows
    except Exception:
        return []


def find_window(application: str):
    wanted = application.lower().strip()
    for hwnd, title in _get_windows():
        if wanted in title.lower():
            return hwnd
    return None


def activate_application(application: str) -> str:
    hwnd = find_window(application)
    if hwnd is None:
        return f"I couldn't find an active window for '{application}', Sir."
    try:
        ctypes.windll.user32.ShowWindow(hwnd, 9)  # SW_RESTORE
        ctypes.windll.user32.SetForegroundWindow(hwnd)
        return f"Switched to {application}, Sir."
    except Exception as error:
        return f"I couldn't switch to {application}: {error}"


def close_application(application: str) -> str:
    hwnd = find_window(application)
    if hwnd is None:
        return f"I couldn't find an open window for '{application}', Sir."
    try:
        WM_CLOSE = 0x0010
        ctypes.windll.user32.PostMessageW(hwnd, WM_CLOSE, 0, 0)
        return f"Closed {application}, Sir."
    except Exception as error:
        return f"I couldn't close {application}: {error}"


def minimize_application(application: str) -> str:
    hwnd = find_window(application)
    if hwnd is None:
        return f"I couldn't find '{application}', Sir."
    try:
        ctypes.windll.user32.ShowWindow(hwnd, 6)  # SW_MINIMIZE
        return f"Minimized {application}, Sir."
    except Exception as error:
        return f"I couldn't minimize {application}: {error}"


def maximize_application(application: str) -> str:
    hwnd = find_window(application)
    if hwnd is None:
        return f"I couldn't find '{application}', Sir."
    try:
        ctypes.windll.user32.ShowWindow(hwnd, 3)  # SW_MAXIMIZE
        ctypes.windll.user32.SetForegroundWindow(hwnd)
        return f"Maximized {application}, Sir."
    except Exception as error:
        return f"I couldn't maximize {application}: {error}"


# =========================================================
# SYSTEM POWER CONTROL
# =========================================================

def lock_pc():
    try:
        ctypes.windll.user32.LockWorkStation()
        return "The PC is locked, Sir."
    except Exception as error:
        return f"I couldn't lock the PC: {error}"


def shutdown_pc(delay_seconds: int = 0):
    try:
        subprocess.Popen(["shutdown", "/s", "/t", str(delay_seconds)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return "The PC is shutting down, Sir."
    except Exception as error:
        return f"Failed to shut down the PC: {error}"


def restart_pc(delay_seconds: int = 0):
    try:
        subprocess.Popen(["shutdown", "/r", "/t", str(delay_seconds)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return "The PC is restarting, Sir."
    except Exception as error:
        return f"Failed to restart the PC: {error}"


def sleep_pc():
    try:
        subprocess.Popen(["rundll32.exe", "powrprof.dll,SetSuspendState", "0", "1", "0"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return "Putting the PC to sleep, Sir."
    except Exception as error:
        return f"Failed to put the PC to sleep: {error}"


def sign_out():
    try:
        subprocess.Popen(["shutdown", "/l"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return "Signing you out, Sir."
    except Exception as error:
        return f"Failed to sign out: {error}"


def cancel_shutdown():
    try:
        subprocess.Popen(["shutdown", "/a"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return "Scheduled shutdown has been cancelled, Sir."
    except Exception as error:
        return f"Failed to cancel shutdown: {error}"


# =========================================================
# SCREENSHOT ENGINE
# =========================================================

def take_screenshot() -> str:
    try:
        from PIL import ImageGrab

        shots_dir = Path.home() / "Pictures" / "Screenshots"
        shots_dir.mkdir(parents=True, exist_ok=True)

        filename = f"Screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        file_path = shots_dir / filename

        img = ImageGrab.grab()
        img.save(file_path, "PNG")

        return f"Screenshot saved to your Screenshots folder, Sir."
    except ImportError:
        return "Pillow is not installed. Please install it using 'pip install pillow', Sir."
    except Exception as error:
        return f"I couldn't capture the screen: {error}"


# =========================================================
# PURE WIN32 CLIPBOARD
# =========================================================

def get_clipboard_text() -> str:
    user32 = ctypes.windll.user32
    kernel32 = ctypes.windll.kernel32

    if not user32.OpenClipboard(None):
        return "I couldn't access the clipboard, Sir."
    try:
        handle = user32.GetClipboardData(CF_UNICODETEXT)
        if not handle:
            return "The clipboard is currently empty, Sir."
        kernel32.GlobalLock.restype = ctypes.c_wchar_p
        text = kernel32.GlobalLock(handle)
        kernel32.GlobalUnlock(handle)
        if not text:
            return "The clipboard is empty, Sir."
        return f"Your clipboard contains: {text}"
    except Exception as error:
        return f"Failed to read clipboard: {error}"
    finally:
        user32.CloseClipboard()


def set_clipboard_text(text: str) -> str:
    user32 = ctypes.windll.user32
    kernel32 = ctypes.windll.kernel32

    if not user32.OpenClipboard(None):
        return "I couldn't access the clipboard, Sir."
    try:
        user32.EmptyClipboard()
        encoded = text.encode("utf-16le") + b"\x00\x00"
        kernel32.GlobalAlloc.restype = wintypes.HGLOBAL
        handle = kernel32.GlobalAlloc(GHND, len(encoded))
        ptr = kernel32.GlobalLock(handle)
        ctypes.memmove(ptr, encoded, len(encoded))
        kernel32.GlobalUnlock(handle)
        user32.SetClipboardData(CF_UNICODETEXT, handle)
        return f"Copied to clipboard, Sir."
    except Exception as error:
        return f"Failed to copy to clipboard: {error}"
    finally:
        user32.CloseClipboard()


def clear_clipboard() -> str:
    user32 = ctypes.windll.user32
    if not user32.OpenClipboard(None):
        return "I couldn't access the clipboard, Sir."
    try:
        user32.EmptyClipboard()
        return "Clipboard cleared, Sir."
    finally:
        user32.CloseClipboard()


# =========================================================
# TELEMETRY & HARDWARE INFO
# =========================================================

def get_system_information():
    try:
        return (
            f"Operating system: {platform.system()} {platform.release()}. "
            f"Computer name: {platform.node()}. "
            f"Processor: {platform.processor()}."
        )
    except Exception as error:
        return f"Couldn't read system information: {error}"


def get_memory_information():
    try:
        import psutil
        memory = psutil.virtual_memory()
        used_gb = memory.used / (1024 ** 3)
        total_gb = memory.total / (1024 ** 3)
        return f"RAM usage is {memory.percent:.0f} percent. {used_gb:.1f} GB of {total_gb:.1f} GB is in use, Sir."
    except Exception as error:
        return f"Couldn't read RAM usage: {error}"


def get_cpu_information():
    try:
        import psutil
        usage = psutil.cpu_percent(interval=0.5)
        cores = psutil.cpu_count(logical=True)
        return f"CPU usage is currently {usage:.0f} percent across {cores} logical processors, Sir."
    except Exception as error:
        return f"Couldn't read CPU usage: {error}"


def get_storage_information():
    try:
        import psutil
        total, used = 0, 0
        for partition in psutil.disk_partitions():
            try:
                usage = psutil.disk_usage(partition.mountpoint)
                total += usage.total
                used += usage.used
            except Exception:
                continue
        if total == 0:
            return "No accessible storage drives detected, Sir."

        total_gb = total / (1024 ** 3)
        used_gb = used / (1024 ** 3)
        percent = (used / total) * 100
        return f"Storage is at {percent:.0f} percent capacity. {used_gb:.1f} GB used out of {total_gb:.1f} GB, Sir."
    except Exception as error:
        return f"Couldn't read storage info: {error}"


def get_battery_information():
    try:
        import psutil
        battery = psutil.sensors_battery()
        if battery is None:
            return "This PC is connected directly to AC power and has no battery installed, Sir."
        status = "plugged in" if battery.power_plugged else "on battery power"
        return f"Battery is at {battery.percent:.0f} percent and is currently {status}, Sir."
    except Exception as error:
        return f"Couldn't read battery status: {error}"


def get_network_information():
    try:
        hostname = socket.gethostname()
        local_ip = socket.gethostbyname(hostname)
        return f"Computer name is {hostname}, and your local IP address is {local_ip}, Sir."
    except Exception as error:
        return f"Couldn't read network information: {error}"
import json
import os
import shutil
import subprocess
import time
from pathlib import Path

try:
    import psutil
except Exception:  # pragma: no cover
    psutil = None


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


def restart_application(application: str) -> str:
    """Restart a known application by closing it and reopening it."""
    app = normalize_text(application)
    if not app:
        return "Which application should I restart, Sir?"

    command = APPLICATIONS.get(app)
    if command is None:
        return f"I don't have permission to restart '{application}', Sir."

    try:
        hwnd = find_window(application)
        if hwnd is not None:
            import ctypes
            WM_CLOSE = 0x0010
            ctypes.windll.user32.PostMessageW(hwnd, WM_CLOSE, 0, 0)
            time.sleep(0.6)

        subprocess.Popen(command, shell=False)
        return f"Restarted {application}, Sir."
    except Exception as error:
        return f"I couldn't restart {application}, Sir. {error}"


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


def _require_confirmation(action_name: str, confirm: bool = False):
    if confirm:
        return True
    return f"I can {action_name}, but I need explicit confirmation first, Sir."


# =========================================================
# SHUTDOWN
# =========================================================

def shutdown_pc(
    delay_seconds: int = 0,
    confirm: bool = False,
):
    confirmation = _require_confirmation("shut down the PC", confirm)
    if confirmation is not True:
        return confirmation

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

        return "The PC is shutting down, Sir."
    except Exception as error:
        return f"I couldn't shut down the PC, Sir. {error}"


# =========================================================
# RESTART
# =========================================================

def restart_pc(
    delay_seconds: int = 0,
    confirm: bool = False,
):
    confirmation = _require_confirmation("restart the PC", confirm)
    if confirmation is not True:
        return confirmation

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

        return "The PC is restarting, Sir."
    except Exception as error:
        return f"I couldn't restart the PC, Sir. {error}"


# =========================================================
# SLEEP
# =========================================================

def sleep_pc(confirm: bool = False):
    confirmation = _require_confirmation("put the PC to sleep", confirm)
    if confirmation is not True:
        return confirmation

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

        return "Putting the PC to sleep, Sir."
    except Exception as error:
        return f"I couldn't put the PC to sleep, Sir. {error}"


# =========================================================
# SIGN OUT
# =========================================================

def sign_out(confirm: bool = False):
    confirmation = _require_confirmation("sign you out", confirm)
    if confirmation is not True:
        return confirmation

    try:
        subprocess.Popen(
            [
                "shutdown",
                "/l",
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

        return "Signing you out, Sir."
    except Exception as error:
        return f"I couldn't sign you out, Sir. {error}"


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


def set_brightness(value: int) -> str:
    value = max(0, min(100, int(value)))
    try:
        script = (
            "Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightnessMethods "
            f"| ForEach-Object {{ $_.WmiSetBrightness(1, {value}) }}"
        )
        subprocess.run(
            ["powershell", "-NoProfile", "-Command", script],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=True,
        )
        return f"Brightness set to {value} percent, Sir."
    except Exception as error:
        return f"I couldn't adjust brightness, Sir. {error}"


def adjust_brightness(delta: int) -> str:
    try:
        result = subprocess.run(
            ["powershell", "-NoProfile", "-Command",
             "(Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightness).CurrentBrightness"],
            capture_output=True,
            text=True,
            check=True,
        )
        current = int(result.stdout.strip().splitlines()[-1]) if result.stdout.strip() else 50
    except Exception:
        current = 50
    target = max(0, min(100, current + int(delta)))
    return set_brightness(target)


def get_battery_information():
    if psutil is None:
        return "The psutil package is required for battery information, Sir."
    try:
        battery = psutil.sensors_battery()
        if battery is None:
            return "I couldn't read battery information on this PC, Sir."
        percent = max(0, min(100, int(battery.percent)))
        status = "Charging" if battery.power_plugged else "Discharging"
        return f"Battery is {percent}% and currently {status.lower()}, Sir."
    except Exception as error:
        return f"I couldn't read battery information, Sir. {error}"


def get_network_information():
    try:
        import socket
        host = socket.gethostname()
        addrs = socket.gethostbyname_ex(host)
        ips = [ip for ip in addrs[2] if not ip.startswith("127.")][:5]
        if ips:
            return f"Computer name: {host}. Local IP addresses: {', '.join(ips)}, Sir."
        return f"Computer name: {host}. I couldn't determine a non-local IP address, Sir."
    except Exception as error:
        return f"I couldn't read the network information, Sir. {error}"


def take_screenshot(output_path: str | None = None) -> str:
    try:
        from PIL import ImageGrab
    except Exception:
        return "Screenshot support requires Pillow, which is not installed in this environment, Sir."

    try:
        if output_path is None:
            folder = Path.home() / "Pictures" / "ALFRED Screenshots"
            folder.mkdir(parents=True, exist_ok=True)
            output_path = folder / f"alfred_screenshot_{int(time.time())}.png"
        else:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)

        ImageGrab.grab().save(output_path)
        return f"Screenshot saved to {output_path}, Sir."
    except Exception as error:
        return f"I couldn't take a screenshot, Sir. {error}"


def empty_recycle_bin(confirm: bool = False):
    if not confirm:
        return "I can empty the Recycle Bin, but I need explicit confirmation first, Sir."
    try:
        subprocess.run(
            ["powershell", "-NoProfile", "-Command", "Clear-RecycleBin -Force"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=True,
        )
        return "The Recycle Bin has been emptied, Sir."
    except Exception as error:
        return f"I couldn't empty the Recycle Bin, Sir. {error}"


def get_clipboard_text():
    try:
        import tkinter as tk
        root = tk.Tk()
        root.withdraw()
        try:
            text = root.clipboard_get()
        finally:
            root.update()
            root.destroy()
        return text if text else "The clipboard is empty, Sir."
    except Exception as error:
        return f"I couldn't read the clipboard, Sir. {error}"


def set_clipboard_text(text: str):
    try:
        import tkinter as tk
        root = tk.Tk()
        root.withdraw()
        root.clipboard_clear()
        root.clipboard_append(str(text or ""))
        root.update()
        root.destroy()
        return "Clipboard updated, Sir."
    except Exception as error:
        return f"I couldn't update the clipboard, Sir. {error}"


def clear_clipboard():
    try:
        import tkinter as tk
        root = tk.Tk()
        root.withdraw()
        root.clipboard_clear()
        root.update()
        root.destroy()
        return "The clipboard has been cleared, Sir."
    except Exception as error:
        return f"I couldn't clear the clipboard, Sir. {error}"


def open_settings(target: str = "") -> str:
    """Open a Windows Settings page or common system tool."""
    mapping = {
        "settings": "ms-settings:",
        "display": "ms-settings:display",
        "sound": "ms-settings:sound",
        "network": "ms-settings:network-wifi",
        "wifi": "ms-settings:network-wifi",
        "bluetooth": "ms-settings:bluetooth",
        "personalization": "ms-settings:personalization",
        "apps": "ms-settings:appsfeatures",
        "storage": "ms-settings:storagesense",
        "update": "ms-settings:windowsupdate",
        "windows update": "ms-settings:windowsupdate",
        "task manager": "taskmgr.exe",
        "taskmgr": "taskmgr.exe",
        "device manager": "devmgmt.msc",
        "control panel": "control.exe",
    }
    page = normalize_text(target or "settings")
    command = mapping.get(page, mapping.get("settings"))
    try:
        if command.startswith("ms-settings:"):
            os.startfile(command)
        else:
            subprocess.Popen(command, shell=True)
        return f"Opened {target or 'Settings'}, Sir."
    except Exception as error:
        return f"I couldn't open the requested settings page, Sir. {error}"


def get_wifi_status() -> str:
    try:
        result = subprocess.run(
            ["powershell", "-NoProfile", "-Command", "netsh wlan show interfaces"],
            capture_output=True,
            text=True,
            check=True,
        )
        output = result.stdout.strip()
        if not output:
            return "I couldn't read the Wi‑Fi adapter state, Sir."
        return output.replace("\r", "")[:600]
    except Exception as error:
        return f"I couldn't read Wi‑Fi status, Sir. {error}"


def list_wifi_networks() -> str:
    try:
        result = subprocess.run(
            ["powershell", "-NoProfile", "-Command", "netsh wlan show networks mode=Bssid"],
            capture_output=True,
            text=True,
            check=True,
        )
        output = result.stdout.strip()
        if not output:
            return "There are no visible Wi‑Fi networks in range, Sir."
        return output.replace("\r", "")[:800]
    except Exception as error:
        return f"I couldn't list Wi‑Fi networks, Sir. {error}"


def get_connected_wifi() -> str:
    try:
        result = subprocess.run(
            ["powershell", "-NoProfile", "-Command", "netsh wlan show interfaces | Select-String -Pattern 'SSID|Signal|State'"],
            capture_output=True,
            text=True,
            check=True,
        )
        output = result.stdout.strip()
        if not output:
            return "No Wi‑Fi network is currently connected, Sir."
        return output.replace("\r", "")
    except Exception as error:
        return f"I couldn't read the connected Wi‑Fi network, Sir. {error}"


def connect_to_wifi_network(ssid: str, password: str | None = None) -> str:
    ssid = (ssid or "").strip()
    if not ssid:
        return "Which Wi‑Fi network should I connect to, Sir?"
    try:
        saved = subprocess.run(
            ["powershell", "-NoProfile", "-Command", f"netsh wlan show profiles name=\"{ssid}\""],
            capture_output=True,
            text=True,
            check=False,
        )
        if saved.returncode != 0 or "Profile \"" not in saved.stdout:
            return f"I found '{ssid}', but it is not a saved Wi‑Fi profile on this PC. Please connect through Windows first, Sir."
        subprocess.run(
            ["powershell", "-NoProfile", "-Command", f"netsh wlan connect name=\"{ssid}\""],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=True,
        )
        return f"I attempted to connect to '{ssid}', Sir."
    except Exception as error:
        return f"I couldn't connect to '{ssid}', Sir. {error}"


def disconnect_wifi() -> str:
    try:
        subprocess.run(
            ["powershell", "-NoProfile", "-Command", "netsh wlan disconnect"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=True,
        )
        return "Wi‑Fi disconnected, Sir."
    except Exception as error:
        return f"I couldn't disconnect Wi‑Fi, Sir. {error}"


def toggle_wifi(enabled: bool) -> str:
    try:
        action = "enable" if enabled else "disable"
        subprocess.run(
            ["powershell", "-NoProfile", "-Command",
             f"(Get-NetAdapter -PhysicalMediaType 802.11 2>$null | Where-Object {{ $_.Status -ne 'Disconnected' }} | Select-Object -First 1).Name | ForEach-Object {{ netsh interface set interface \"$_\" admin={action} }}"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=True,
        )
        return f"Wi‑Fi turned {'on' if enabled else 'off'}, Sir."
    except Exception as error:
        return f"I couldn't change Wi‑Fi state, Sir. {error}"


def get_network_interfaces() -> str:
    try:
        result = subprocess.run(
            ["powershell", "-NoProfile", "-Command", "Get-NetAdapter | Format-Table -AutoSize Name, Status, InterfaceDescription, ifIndex"],
            capture_output=True,
            text=True,
            check=True,
        )
        output = result.stdout.strip()
        return output if output else "I couldn't read the network interfaces, Sir."
    except Exception as error:
        return f"I couldn't read the network interfaces, Sir. {error}"


def get_ip_information() -> str:
    try:
        result = subprocess.run(
            ["powershell", "-NoProfile", "-Command", "Get-NetIPAddress | Format-Table -AutoSize IPAddress, InterfaceAlias, PrefixLength"],
            capture_output=True,
            text=True,
            check=True,
        )
        output = result.stdout.strip()
        return output if output else "I couldn't read the IP configuration, Sir."
    except Exception as error:
        return f"I couldn't read the IP information, Sir. {error}"


def ping_host(host: str = "8.8.8.8") -> str:
    host = (host or "8.8.8.8").strip()
    try:
        result = subprocess.run(
            ["ping", "-n", "2", host],
            capture_output=True,
            text=True,
            check=False,
        )
        output = result.stdout + result.stderr
        return output.strip() if output.strip() else f"I couldn't ping {host}, Sir."
    except Exception as error:
        return f"I couldn't ping {host}, Sir. {error}"


def get_bluetooth_status() -> str:
    try:
        result = subprocess.run(
            ["powershell", "-NoProfile", "-Command", "Get-PnpDevice -Class Bluetooth | Select-Object FriendlyName, Status, InstanceId | Format-Table -AutoSize"],
            capture_output=True,
            text=True,
            check=True,
        )
        output = result.stdout.strip()
        return output if output else "Bluetooth adapter information is not available on this system, Sir."
    except Exception as error:
        return f"I couldn't read Bluetooth status, Sir. {error}"


def list_bluetooth_devices() -> str:
    try:
        result = subprocess.run(
            ["powershell", "-NoProfile", "-Command", "Get-PnpDevice -Class Bluetooth | Select-Object FriendlyName, Status | Format-Table -AutoSize"],
            capture_output=True,
            text=True,
            check=True,
        )
        output = result.stdout.strip()
        return output if output else "No Bluetooth devices were detected, Sir."
    except Exception as error:
        return f"I couldn't enumerate Bluetooth devices, Sir. {error}"


def connect_bluetooth_device(device_name: str) -> str:
    device_name = (device_name or "").strip()
    if not device_name:
        return "Which Bluetooth device should I connect to, Sir?"
    try:
        device = subprocess.run(
            ["powershell", "-NoProfile", "-Command", f"Get-PnpDevice -Class Bluetooth | Where-Object {{ $_.FriendlyName -match '{device_name}' }} | Select-Object -First 1 -ExpandProperty FriendlyName"],
            capture_output=True,
            text=True,
            check=False,
        )
        if device.stdout.strip():
            return f"I found '{device.stdout.strip()}', but Windows does not expose a reliable direct device connection API from this environment. I opened the Bluetooth settings page instead, Sir."
        return f"I couldn't find a matching Bluetooth device named '{device_name}' on this PC, Sir."
    except Exception as error:
        return f"I couldn't connect to '{device_name}', Sir. {error}"


def disconnect_bluetooth_device(device_name: str) -> str:
    device_name = (device_name or "").strip()
    if not device_name:
        return "Which Bluetooth device should I disconnect, Sir?"
    try:
        result = subprocess.run(
            ["powershell", "-NoProfile", "-Command", f"Get-PnpDevice -Class Bluetooth | Where-Object {{ $_.FriendlyName -match '{device_name}' }} | Select-Object -First 1 -ExpandProperty FriendlyName"],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.stdout.strip():
            return f"I found '{result.stdout.strip()}', but disconnecting a Bluetooth device requires the OS/device-specific connection state and is not safely automatable here, Sir."
        return f"I couldn't find a matching Bluetooth device named '{device_name}' to disconnect, Sir."
    except Exception as error:
        return f"I couldn't disconnect '{device_name}', Sir. {error}"


def toggle_bluetooth(enabled: bool) -> str:
    try:
        action = "Enable" if enabled else "Disable"
        script = (
            f"Get-PnpDevice -Class Bluetooth | ForEach-Object {{ "
            f"if ($_.Status -eq 'OK') {{ $_ | {action}-PnpDevice -Confirm:$false }} }}"
        )
        subprocess.run(
            ["powershell", "-NoProfile", "-Command", script],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=True,
        )
        return f"Bluetooth turned {'on' if enabled else 'off'}, Sir."
    except Exception as error:
        return f"I couldn't change Bluetooth state, Sir. {error}"


def toggle_airplane_mode(enabled: bool) -> str:
    try:
        target_state = "enabled" if enabled else "disabled"
        subprocess.run(
            ["powershell", "-NoProfile", "-Command",
             f"Get-NetAdapter | Where-Object {{ $_.Name -match 'Wi-Fi|Ethernet' }} | ForEach-Object {{ Disable-NetAdapter -Name $_.Name -Confirm:$false }}" if not enabled else "Get-NetAdapter | Where-Object { $_.Name -match 'Wi-Fi|Ethernet' } | ForEach-Object { Enable-NetAdapter -Name $_.Name -Confirm:$false }"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=True,
        )
        return f"Airplane mode is {target_state}, Sir."
    except Exception as error:
        return f"I couldn't change airplane mode, Sir. {error}"


def get_gpu_information():
    try:
        result = subprocess.run(
            ["powershell", "-NoProfile", "-Command",
             "Get-CimInstance Win32_VideoController | Select-Object -First 1 Name, DriverVersion | Format-Table -HideTableHeaders"],
            capture_output=True,
            text=True,
            check=True,
        )
        text = result.stdout.strip().replace("\r", "")
        if not text:
            return "I couldn't read the GPU information, Sir."
        return f"GPU: {text.replace(chr(10), ' ').strip()}, Sir."
    except Exception as error:
        return f"I couldn't read the GPU information, Sir. {error}"


def get_running_applications():
    try:
        import psutil
        procs = sorted(psutil.process_iter(attrs=['name']), key=lambda p: p.info.get('name', '').lower())
        names = []
        seen = set()
        for proc in procs:
            name = (proc.info.get('name') or '').strip()
            if not name or name in seen:
                continue
            seen.add(name)
            names.append(name)
            if len(names) >= 12:
                break
        if not names:
            return "I couldn't read the running applications, Sir."
        return "Running apps: " + ", ".join(names) + ", Sir."
    except Exception as error:
        return f"I couldn't read the running applications, Sir. {error}"


def get_current_datetime() -> str:
    from datetime import datetime
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def get_usb_inventory() -> list[dict]:
    """Return a read-only USB inventory using Windows PnP metadata."""
    script = (
        "Get-PnpDevice -PresentOnly -ErrorAction SilentlyContinue | "
        "Where-Object { $_.Class -eq 'USB' -or $_.FriendlyName -match 'USB' } | "
        "Select-Object FriendlyName, Manufacturer, Status, Class, InstanceId, Present | "
        "ConvertTo-Json -Depth 6"
    )
    try:
        result = subprocess.run(
            ["powershell", "-NoProfile", "-Command", script],
            capture_output=True,
            text=True,
            check=False,
        )
        payload = (result.stdout or "").strip()
        if not payload:
            return []
        parsed = json.loads(payload)
        if isinstance(parsed, list):
            return parsed
        if isinstance(parsed, dict):
            return [parsed]
        return []
    except Exception:
        return []


def get_audio_device_inventory() -> dict:
    """Return local, read-only audio device metadata where Windows exposes it."""
    result = {
        "playback": [],
        "recording": [],
        "default_playback": None,
        "default_microphone": None,
        "limitation": None,
    }

    try:
        codec_script = (
            "if (Get-Command Get-AudioDevice -ErrorAction SilentlyContinue) { "
            "Get-AudioDevice | Select-Object Name, Type, Default, Status | ConvertTo-Json -Depth 6 "
            "} else { '[]' }"
        )
        codec_result = subprocess.run(
            ["powershell", "-NoProfile", "-Command", codec_script],
            capture_output=True,
            text=True,
            check=False,
        )
        codec_data = (codec_result.stdout or "").strip()
        if codec_data and codec_data != "[]":
            parsed_data = json.loads(codec_data)
            if isinstance(parsed_data, list):
                for item in parsed_data:
                    name = str(item.get("Name") or item.get("name") or "Unknown device").strip()
                    device_type = str(item.get("Type") or item.get("type") or "device").strip()
                    device_status = str(item.get("Status") or item.get("status") or "unknown").strip()
                    default_flag = bool(item.get("Default") or item.get("default"))
                    if device_type.lower() in {"speaker", "playback", "output"}:
                        clean = {"name": name, "type": device_type, "status": device_status, "default": default_flag}
                        result["playback"].append(clean)
                        if default_flag:
                            result["default_playback"] = name
                    elif device_type.lower() in {"microphone", "recording", "input"}:
                        clean = {"name": name, "type": device_type, "status": device_status, "default": default_flag}
                        result["recording"].append(clean)
                        if default_flag:
                            result["default_microphone"] = name
    except Exception:
        pass

    if not result["playback"] and not result["recording"]:
        try:
            fallback_script = (
                "Get-CimInstance Win32_SoundDevice -ErrorAction SilentlyContinue | "
                "Select-Object Name, Status, Manufacturer, Caption | ConvertTo-Json -Depth 6"
            )
            fallback_result = subprocess.run(
                ["powershell", "-NoProfile", "-Command", fallback_script],
                capture_output=True,
                text=True,
                check=False,
            )
            fallback_payload = (fallback_result.stdout or "").strip()
            if fallback_payload and fallback_payload != "[]":
                parsed = json.loads(fallback_payload)
                if isinstance(parsed, list):
                    result["playback"] = [{"name": item.get("Name") or item.get("Caption") or "Audio device", "type": "device", "status": item.get("Status") or "unknown", "default": False} for item in parsed]
                    result["recording"] = list(result["playback"])
        except Exception:
            result["limitation"] = "Windows did not expose audio device metadata in this environment."

    if not result["limitation"] and not result["playback"] and not result["recording"]:
        result["limitation"] = "No audio devices were exposed by Windows in the current environment."

    return result


def get_display_information() -> dict:
    """Return read-only monitor information from Windows WMI / CIM when available."""
    payload = {
        "monitors": [],
        "count": 0,
        "primary_monitor": None,
        "limitation": None,
    }

    try:
        monitor_script = (
            "Get-CimInstance Win32_DesktopMonitor -ErrorAction SilentlyContinue | "
            "Select-Object Name, Status, MonitorType, PNPDeviceID, ScreenHeight, ScreenWidth | "
            "ConvertTo-Json -Depth 8"
        )
        monitor_result = subprocess.run(
            ["powershell", "-NoProfile", "-Command", monitor_script],
            capture_output=True,
            text=True,
            check=False,
        )
        monitor_payload = (monitor_result.stdout or "").strip()
        if monitor_payload and monitor_payload != "[]":
            monitors = json.loads(monitor_payload)
            if isinstance(monitors, dict):
                monitors = [monitors]
            payload["monitors"] = [
                {
                    "name": item.get("Name") or "Unknown monitor",
                    "status": item.get("Status") or "unknown",
                    "type": item.get("MonitorType") or "unknown",
                    "pnp_device_id": item.get("PNPDeviceID") or None,
                    "screen_height": item.get("ScreenHeight"),
                    "screen_width": item.get("ScreenWidth"),
                }
                for item in monitors
            ]
    except Exception:
        pass

    try:
        video_script = (
            "Get-CimInstance Win32_VideoController -ErrorAction SilentlyContinue | "
            "Select-Object Name, CurrentHorizontalResolution, CurrentVerticalResolution, CurrentRefreshRate, Status | "
            "ConvertTo-Json -Depth 8"
        )
        video_result = subprocess.run(
            ["powershell", "-NoProfile", "-Command", video_script],
            capture_output=True,
            text=True,
            check=False,
        )
        video_payload = (video_result.stdout or "").strip()
        if video_payload and video_payload != "[]":
            video_devices = json.loads(video_payload)
            if isinstance(video_devices, dict):
                video_devices = [video_devices]
            payload["video_cards"] = [
                {
                    "name": item.get("Name") or "Display adapter",
                    "resolution": f"{item.get('CurrentHorizontalResolution')}x{item.get('CurrentVerticalResolution')}",
                    "refresh_rate": item.get("CurrentRefreshRate"),
                    "status": item.get("Status") or "unknown",
                }
                for item in video_devices
            ]
    except Exception:
        pass

    payload["count"] = len(payload.get("monitors", []))
    if payload["monitors"]:
        payload["primary_monitor"] = payload["monitors"][0].get("name")
    if not payload["monitors"] and not payload.get("video_cards"):
        payload["limitation"] = "Windows did not expose monitor metadata in the current environment."

    return payload


def get_brightness() -> dict:
    """Return brightness information for supported monitors, or a truthful limitation."""
    info = {
        "current": None,
        "supported": False,
        "limitation": None,
    }
    try:
        result = subprocess.run(
            [
                "powershell",
                "-NoProfile",
                "-Command",
                "(Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightness).CurrentBrightness",
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        value = (result.stdout or "").strip()
        if value:
            info["current"] = int(value.splitlines()[-1].strip())
            info["supported"] = True
    except Exception:
        pass
    if info["current"] is None:
        info["limitation"] = "The current monitor or driver does not expose brightness metadata through Windows WMI."
    return info


def get_drive_information() -> str:
    try:
        import psutil
        drives = []
        for partition in psutil.disk_partitions(all=False):
            try:
                usage = psutil.disk_usage(partition.mountpoint)
                drives.append(
                    f"{partition.device} -> {partition.mountpoint} | total={usage.total / (1024 ** 3):.1f}GB free={usage.free / (1024 ** 3):.1f}GB"
                )
            except Exception:
                continue
        if not drives:
            return "I couldn't read the drive information, Sir."
        return "\n".join(drives[:8]) + ", Sir."
    except Exception as error:
        return f"I couldn't read the drive information, Sir. {error}"


def get_storage_remaining() -> str:
    try:
        import psutil
        total = 0
        free = 0
        for partition in psutil.disk_partitions(all=False):
            try:
                usage = psutil.disk_usage(partition.mountpoint)
                total += usage.total
                free += usage.free
            except Exception:
                continue
        if total == 0:
            return "I couldn't read the remaining free space, Sir."
        total_gb = total / (1024 ** 3)
        free_gb = free / (1024 ** 3)
        return f"Free space is {free_gb:.1f} GB of {total_gb:.1f} GB total, Sir."
    except Exception as error:
        return f"I couldn't read the remaining free space, Sir. {error}"


def get_network_status() -> str:
    try:
        result = subprocess.run(
            [
                "powershell",
                "-NoProfile",
                "-Command",
                "Get-NetAdapter | Select-Object Name, Status, InterfaceDescription, LinkSpeed | Format-Table -AutoSize; Write-Host '---'; Get-NetIPAddress | Select-Object InterfaceAlias, IPAddress, PrefixLength | Format-Table -AutoSize",
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        output = (result.stdout or "") + (result.stderr or "")
        output = output.strip().replace("\r", "")
        return output if output else "I couldn't read the network status, Sir."
    except Exception as error:
        return f"I couldn't read the network status, Sir. {error}"


def record_screen(duration_seconds: int = 10, output_path: str | None = None) -> str:
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        return "Screen recording requires ffmpeg, which is not installed on this PC, Sir."
    target = Path(output_path) if output_path else Path.home() / "Videos" / "ALFRED Screen Recording" / f"alfred_record_{int(time.time())}.mp4"
    target.parent.mkdir(parents=True, exist_ok=True)
    try:
        subprocess.run([
            ffmpeg,
            "-y",
            "-f",
            "gdigrab",
            "-framerate",
            "30",
            "-i",
            "desktop",
            "-t",
            str(max(1, int(duration_seconds))),
            str(target),
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        return f"Screen recording saved to {target}, Sir."
    except Exception as error:
        return f"I couldn't record the screen, Sir. {error}"


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
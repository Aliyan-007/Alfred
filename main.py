import os
import sys
import time
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

from tools.bluetooth import (
    connect_bluetooth_device,
    disconnect_bluetooth_device,
    get_bluetooth_status,
    list_bluetooth_devices,
    toggle_bluetooth,
)
from tools.display import adjust_brightness, open_display_settings, set_brightness
from tools.hardware import (
    get_battery_information,
    get_cpu_information,
    get_current_datetime,
    get_drive_information,
    get_gpu_information,
    get_memory_information,
    get_running_applications,
    get_storage_information,
    get_storage_remaining,
    get_system_information,
)
from tools.network import (
    connect_to_wifi_network,
    disconnect_wifi,
    get_connected_wifi,
    get_ip_information,
    get_network_information,
    get_network_interfaces,
    get_network_status,
    get_wifi_status,
    list_wifi_networks,
    ping_host,
    toggle_airplane_mode,
    toggle_wifi,
)

WAKE_WORD_MODEL = None


def resolve_wake_word_model():
    global WAKE_WORD_MODEL

    if WAKE_WORD_MODEL is not None:
        return WAKE_WORD_MODEL

    candidate_paths = [
        BASE_DIR / "alfred.onnx",
        BASE_DIR / "models" / "alfred.onnx",
        BASE_DIR / "voice" / "alfred.onnx",
        Path("D:/alfred/alfred.onnx"),
    ]

    for candidate in candidate_paths:
        if candidate.exists():
            WAKE_WORD_MODEL = str(candidate)
            break

    if not WAKE_WORD_MODEL:
        print("\n[WARNING] 'alfred.onnx' not found! Falling back to alexa_v0.1")
        WAKE_WORD_MODEL = "alexa_v0.1"
    else:
        print(f"\n[WAKE WORD] Custom model loaded: {WAKE_WORD_MODEL}")

    return WAKE_WORD_MODEL


# =========================================================
# HELPER: SAFE SPEAK
# =========================================================

def _lazy_import(module_name: str, symbol: str):
    module = __import__(module_name, fromlist=[symbol])
    return getattr(module, symbol)


def record_audio(*args, **kwargs):
    return _lazy_import("voice.recorder", "record_audio")(*args, **kwargs)


def transcribe_audio(*args, **kwargs):
    return _lazy_import("voice.stt", "transcribe_audio")(*args, **kwargs)


def handle_command(*args, **kwargs):
    return _lazy_import("tools.dispatcher", "handle_command")(*args, **kwargs)


def handle_local_command(text: str):
    """Compatibility wrapper: route text through the real local dispatcher."""
    return handle_command(text)


def ask_brain(*args, **kwargs):
    return _lazy_import("brain", "ask_brain")(*args, **kwargs)


# =========================================================
# MAIN-LEVEL WINDOWS FEATURE WRAPPERS
# =========================================================

__all__ = [
    "initialize_runtime",
    "process_command",
    "main_loop",
    "handle_local_command",
    "get_wifi_status",
    "list_wifi_networks",
    "get_connected_wifi",
    "connect_to_wifi_network",
    "disconnect_wifi",
    "toggle_wifi",
    "toggle_airplane_mode",
    "get_network_status",
    "get_network_information",
    "get_ip_information",
    "get_bluetooth_status",
    "list_bluetooth_devices",
    "connect_bluetooth_device",
    "disconnect_bluetooth_device",
    "toggle_bluetooth",
    "set_brightness",
    "adjust_brightness",
    "open_display_settings",
    "get_system_information",
    "get_cpu_information",
    "get_memory_information",
    "get_storage_information",
    "get_storage_remaining",
    "get_battery_information",
    "get_gpu_information",
    "get_running_applications",
    "get_current_datetime",
]


def get_wifi_status():
    return _lazy_import("tools.network", "get_wifi_status")()


def list_wifi_networks():
    return _lazy_import("tools.network", "list_wifi_networks")()


def get_connected_wifi():
    return _lazy_import("tools.network", "get_connected_wifi")()


def connect_to_wifi_network(ssid: str, password: str | None = None):
    return _lazy_import("tools.network", "connect_to_wifi_network")(ssid, password)


def disconnect_wifi():
    return _lazy_import("tools.network", "disconnect_wifi")()


def toggle_wifi(enabled: bool):
    return _lazy_import("tools.network", "toggle_wifi")(enabled)


def toggle_airplane_mode(enabled: bool):
    return _lazy_import("tools.network", "toggle_airplane_mode")(enabled)


def get_network_status():
    return _lazy_import("tools.network", "get_network_status")()


def get_network_information():
    return _lazy_import("tools.network", "get_network_information")()


def get_ip_information():
    return _lazy_import("tools.network", "get_ip_information")()


def get_bluetooth_status():
    return _lazy_import("tools.bluetooth", "get_bluetooth_status")()


def list_bluetooth_devices():
    return _lazy_import("tools.bluetooth", "list_bluetooth_devices")()


def connect_bluetooth_device(device_name: str):
    return _lazy_import("tools.bluetooth", "connect_bluetooth_device")(device_name)


def disconnect_bluetooth_device(device_name: str):
    return _lazy_import("tools.bluetooth", "disconnect_bluetooth_device")(device_name)


def toggle_bluetooth(enabled: bool):
    return _lazy_import("tools.bluetooth", "toggle_bluetooth")(enabled)


def get_system_information():
    return _lazy_import("tools.hardware", "get_system_information")()


def get_cpu_information():
    return _lazy_import("tools.hardware", "get_cpu_information")()


def get_memory_information():
    return _lazy_import("tools.hardware", "get_memory_information")()


def get_storage_information():
    return _lazy_import("tools.hardware", "get_storage_information")()


def get_storage_remaining():
    return _lazy_import("tools.hardware", "get_storage_remaining")()


def get_battery_information():
    return _lazy_import("tools.hardware", "get_battery_information")()


def get_gpu_information():
    return _lazy_import("tools.hardware", "get_gpu_information")()


def get_running_applications():
    return _lazy_import("tools.hardware", "get_running_applications")()


def get_current_datetime():
    return _lazy_import("tools.hardware", "get_current_datetime")()


def get_network_interfaces():
    return _lazy_import("tools.network", "get_network_interfaces")()


def ping_host(host: str = "8.8.8.8"):
    return _lazy_import("tools.network", "ping_host")(host)


def open_display_settings():
    return _lazy_import("tools.display", "open_display_settings")()


def detect_assistant(*args, **kwargs):
    return _lazy_import("assistants.router", "detect_assistant")(*args, **kwargs)


def safe_speak(text: str, assistant: str = "ALFRED"):
    """Block wake-word detection while Alfred speaks (kills echo bleed)."""
    from voice.tts import speak
    from voice.wake_word import set_speaking

    try:
        set_speaking(True)
        speak(text, assistant)
    except Exception as error:
        print(f"[TTS Error] {error}")
    finally:
        time.sleep(0.5)
        set_speaking(False)


# =========================================================
# STARTUP BANNER
# =========================================================

def initialize_runtime():
    from openwakeword.model import Model

    from tools.browser import ensure_brave
    from voice.tts import initialize_tts

    print()
    print("=" * 55)
    print("                    ALFRED")
    print("=" * 55)
    print()

    model_path = resolve_wake_word_model()

    print("Starting ALFRED Brave browser...")
    try:
        ensure_brave()
    except Exception:
        pass

    print("Initializing voice system...")
    try:
        initialize_tts(wait=False)
    except Exception:
        pass

    print("Loading wake-word engine...")
    try:
        wake_model = Model(wakeword_models=[model_path], inference_framework="onnx")
    except Exception:
        try:
            wake_model = Model(wakeword_models=[model_path])
        except Exception as err:
            print(f"Failed loading wake word: {err}")
            raise SystemExit(1)

    print("\nALFRED systems ready and online.")
    print("Say 'shutdown alfred' to exit.\n")
    return wake_model


# =========================================================
# COMMAND PROCESSOR
# =========================================================

def process_command():
    print("Listening for your command...")

    try:
        audio_file = record_audio()
        if not audio_file:
            print("[ALFRED] No command captured; returning to listening mode.")
            return None

        user_input = transcribe_audio(audio_file)
    except Exception as error:
        print(f"[ALFRED] Voice transcription failed: {error}")
        print("[ALFRED] Returning to listening mode.")
        return None

    if not user_input or not user_input.strip():
        print("[ALFRED] Empty transcription; returning to listening mode.")
        return None

    print()
    print(f"You: {user_input}")
    print()

    normalized_input = user_input.lower().strip().rstrip(".?!")

    # Discard mic artifacts
    if normalized_input in {"you", "thank you", "thanks", "subtitles by", "bye", "go", "yeah", "yes"}:
        print("[ALFRED] Discarded brief mic artifact.")
        return None

    # Program shutdown. Require an explicit shutdown phrase so ordinary
    # microphone noise or casual speech does not terminate the assistant.
    shutdown_phrases = {
        "shutdown alfred",
        "exit alfred",
        "close alfred",
        "quit alfred",
        "alfred shutdown",
    }
    if (
        normalized_input in shutdown_phrases
        or normalized_input.endswith(" shutdown alfred")
        or normalized_input.startswith("shutdown alfred ")
    ):
        print("ALFRED: Goodbye, Sir.")
        safe_speak("Goodbye, Sir.", "ALFRED")
        raise SystemExit

    # Standby
    if normalized_input in {"stop listening", "go to sleep", "stand down"}:
        print("ALFRED: Standing down. Call me when you need me, Sir.")
        safe_speak("Standing down. Call me when you need me, Sir.", "ALFRED")
        return None

    # Persona
    try:
        assistant = detect_assistant(user_input)
    except Exception:
        assistant = "ALFRED"

    # Dispatcher
    try:
        tool_result = handle_command(user_input)
        if tool_result is not None:
            if isinstance(tool_result, tuple):
                answer = str(tool_result[1]) if len(tool_result) > 1 and tool_result[1] else str(tool_result[0])
            else:
                answer = str(tool_result)
        else:
            answer = str(ask_brain(user_input))
    except Exception as error:
        answer = f"I encountered an error, Sir: {error}"

    print(f"{assistant}: {answer}")
    print()
    try:
        safe_speak(answer, assistant)
    except Exception as error:
        print(f"[ALFRED] Answer speaking failed: {error}")

    return answer


# =========================================================
# MAIN LOOP
# =========================================================

def main_loop():
    from voice.wake_word import wait_for_wake_word

    wake_model = initialize_runtime()

    while True:
        try:
            wait_for_wake_word(wake_model)

            # confirm wake-word activation
            safe_speak("Yes Sir.", "ALFRED")

            # short pause so the user can speak naturally
            time.sleep(0.25)

            process_command()
            time.sleep(0.2)

        except SystemExit:
            print("\nALFRED: Shutdown complete.")
            break
        except KeyboardInterrupt:
            print("\nALFRED: Goodbye, Sir.")
            break
        except Exception as error:
            print(f"\nSystem error: {error}\n")
            time.sleep(1.0)


if __name__ == "__main__":
    main_loop()
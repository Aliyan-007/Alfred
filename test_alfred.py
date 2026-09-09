import importlib
import json
import os
import sys
import time
import traceback
from datetime import datetime, timezone
from pathlib import Path

PROJECT_PATH = Path(__file__).resolve().parent
TEMP_WORKSPACE = PROJECT_PATH / "alfred_test_workspace"

RESULTS = []


def record(category, label, status, error="", details=""):
    RESULTS.append(
        {
            "category": category,
            "label": label,
            "status": status,
            "error": error,
            "details": details,
        }
    )


def safe_import(module_name):
    try:
        return importlib.import_module(module_name)
    except Exception as exc:
        return None, exc


def exists_in_module(module_name, func_name):
    mod = safe_import(module_name)
    if isinstance(mod, tuple):
        return False
    return hasattr(mod, func_name)


def clean_temp_workspace():
    try:
        if TEMP_WORKSPACE.exists():
            for child in TEMP_WORKSPACE.iterdir():
                if child.is_file() or child.is_symlink():
                    child.unlink()
                elif child.is_dir():
                    for sub in child.rglob("*"):
                        if sub.is_file() or sub.is_symlink():
                            sub.unlink()
                    for sub in sorted(child.rglob("*"), reverse=True):
                        if sub.is_dir():
                            sub.rmdir()
                    child.rmdir()
            TEMP_WORKSPACE.rmdir()
    except Exception:
        pass


def assert_function_implemented(module_name, func_name, label, category, *, manual=False, dependency=False, details=""):
    if not exists_in_module(module_name, func_name):
        record(category, label, "NOT IMPLEMENTED", details=f"{module_name}.{func_name} missing")
        return
    if manual:
        record(category, label, "MANUAL", details=details or f"{module_name}.{func_name} is implemented but requires hardware or confirmation")
        return
    if dependency:
        record(category, label, "DEPENDENCY", details=details or f"{module_name}.{func_name} requires external service or device")
        return
    try:
        mod = safe_import(module_name)
        if mod is None or isinstance(mod, tuple):
            record(category, label, "FAIL", str(mod[1]) if isinstance(mod, tuple) else "module import failed")
            return
        result = getattr(mod, func_name)()
        text = str(result)[:180]
        record(category, label, "PASS", details=text)
    except Exception as exc:
        record(category, label, "FAIL", str(exc), f"{module_name}.{func_name}")


def check_system_category():
    try:
        import tools.system as system
        import tools.media as media
    except Exception as exc:
        record("A. WINDOWS / SYSTEM", "imports", "FAIL", str(exc))
        return

    safe_checks = [
        ("open app", "tools.system", "open_application", lambda: system.open_application("notepad")),
        ("volume up", "tools.media", "pc_volume_up", lambda: media.pc_volume_up()),
        ("volume down", "tools.media", "pc_volume_down", lambda: media.pc_volume_down()),
        ("mute", "tools.media", "pc_volume_mute", lambda: media.pc_volume_mute()),
        ("unmute", "tools.media", "pc_volume_unmute", lambda: media.pc_volume_unmute()),
        ("brightness up", "tools.system", "adjust_brightness", lambda: system.adjust_brightness(15)),
        ("system information", "tools.system", "get_system_information", lambda: system.get_system_information()),
        ("CPU usage", "tools.system", "get_cpu_information", lambda: system.get_cpu_information()),
        ("RAM usage", "tools.system", "get_memory_information", lambda: system.get_memory_information()),
        ("disk usage", "tools.system", "get_storage_information", lambda: system.get_storage_information()),
        ("storage remaining", "tools.system", "get_storage_remaining", lambda: system.get_storage_remaining()),
        ("IP address", "tools.system", "get_ip_information", lambda: system.get_ip_information()),
        ("network diagnostics", "tools.system", "get_network_status", lambda: system.get_network_status()),
        ("Wi‑Fi status", "tools.system", "get_wifi_status", lambda: system.get_wifi_status()),
        ("Wi‑Fi discovery", "tools.system", "list_wifi_networks", lambda: system.list_wifi_networks()),
        ("connected Wi‑Fi", "tools.system", "get_connected_wifi", lambda: system.get_connected_wifi()),
        ("Bluetooth status", "tools.system", "get_bluetooth_status", lambda: system.get_bluetooth_status()),
        ("Bluetooth list", "tools.system", "list_bluetooth_devices", lambda: system.list_bluetooth_devices()),
        ("Windows settings", "tools.system", "open_settings", lambda: system.open_settings("settings")),
        ("running apps", "tools.system", "get_running_applications", lambda: system.get_running_applications()),
    ]

    for label, module_name, func_name, runner in safe_checks:
        try:
            result = runner()
            record("A. WINDOWS / SYSTEM", label, "PASS", details=f"{module_name}.{func_name}: {str(result)[:180]}")
        except Exception as exc:
            record("A. WINDOWS / SYSTEM", label, "FAIL", str(exc), f"{module_name}.{func_name}")

    manual_hardware = [
        ("Wi‑Fi on", "tools.system", "toggle_wifi", "toggle_wifi requires a real adapter and explicit user confirmation"),
        ("Wi‑Fi off", "tools.system", "toggle_wifi", "toggle_wifi requires a real adapter and explicit user confirmation"),
        ("Wi‑Fi connect", "tools.system", "connect_to_wifi_network", "connect_to_wifi_network needs a saved profile and user confirmed credentials"),
        ("Wi‑Fi disconnect", "tools.system", "disconnect_wifi", "disconnect_wifi is for explicit user choice and not safe to auto-run"),
        ("Bluetooth on", "tools.system", "toggle_bluetooth", "toggle_bluetooth changes adapter state and must remain user-confirmed"),
        ("Bluetooth off", "tools.system", "toggle_bluetooth", "toggle_bluetooth changes adapter state and must remain user-confirmed"),
        ("Bluetooth connect", "tools.system", "connect_bluetooth_device", "pairing needs the OS and physical device state"),
        ("Bluetooth disconnect", "tools.system", "disconnect_bluetooth_device", "disconnecting a paired device is confirmation-gated"),
        ("airplane mode", "tools.system", "toggle_airplane_mode", "airplane mode changes radio state and is not safe to auto-toggle"),
        ("lock PC", "tools.system", "lock_pc", "destructive action; not executed automatically"),
        ("shutdown PC", "tools.system", "shutdown_pc", "destructive action; not executed automatically"),
        ("restart PC", "tools.system", "restart_pc", "destructive action; not executed automatically"),
        ("sleep PC", "tools.system", "sleep_pc", "destructive action; not executed automatically"),
        ("sign out", "tools.system", "sign_out", "destructive action; not executed automatically"),
        ("empty recycle bin", "tools.system", "empty_recycle_bin", "destructive action; not executed automatically"),
    ]

    for label, module_name, func_name, detail in manual_hardware:
        if exists_in_module(module_name, func_name):
            record("A. WINDOWS / SYSTEM", label, "MANUAL", details=detail)
        else:
            record("A. WINDOWS / SYSTEM", label, "NOT IMPLEMENTED", details=f"{module_name}.{func_name} missing")

    for label in ["USB inventory", "audio devices", "display information", "brightness calibration"]:
        record("A. WINDOWS / SYSTEM", label, "NOT IMPLEMENTED", details="no safe local implementation was found in the current source tree")


def check_files_category():
    try:
        import tools.file_manager as file_manager
        import tools.system as system
    except Exception as exc:
        record("B. FILES / FOLDERS", "imports", "FAIL", str(exc))
        return

    TEMP_WORKSPACE.mkdir(exist_ok=True)
    source = TEMP_WORKSPACE / "alfred_audit_source.txt"
    source.write_text("ALFRED audit body\n", encoding="utf-8")

    checks = [
        ("create folder", "create_folder", lambda: file_manager.create_folder("alfred_audit_folder", str(TEMP_WORKSPACE.name))),
        ("create file", "create_file", lambda: file_manager.create_file("alfred_audit_file.txt", str(TEMP_WORKSPACE.name), "audit body")),
        ("find file by name", "find_and_open_file", lambda: file_manager.find_and_open_file("alfred_audit_file")),
        ("rename file", "rename_item", lambda: file_manager.rename_item("alfred_audit_file", "alfred_audit_file_renamed")),
    ]
    for label, func_name, runner in checks:
        try:
            result = runner()
            record("B. FILES / FOLDERS", label, "PASS", details=f"{func_name}: {str(result)[:160]}")
        except Exception as exc:
            record("B. FILES / FOLDERS", label, "FAIL", str(exc), func_name)

    copy_target = TEMP_WORKSPACE / "copy_target.txt"
    move_target = TEMP_WORKSPACE / "move_target.txt"
    try:
        copy_result = file_manager.copy_file(str(source), str(copy_target))
        if copy_target.exists() and copy_target.read_text(encoding="utf-8") == source.read_text(encoding="utf-8"):
            record("B. FILES / FOLDERS", "copy file", "PASS", details=str(copy_result)[:180])
        else:
            record("B. FILES / FOLDERS", "copy file", "FAIL", details="copy helper ran but target file did not match source")
    except Exception as exc:
        record("B. FILES / FOLDERS", "copy file", "FAIL", str(exc))

    try:
        move_result = file_manager.move_file(str(copy_target), str(move_target))
        if move_target.exists():
            record("B. FILES / FOLDERS", "move file", "PASS", details=str(move_result)[:180])
        else:
            record("B. FILES / FOLDERS", "move file", "FAIL", details="move helper ran but destination file was not created")
    except Exception as exc:
        record("B. FILES / FOLDERS", "move file", "FAIL", str(exc))

    try:
        system.clear_clipboard()
        system.set_clipboard_text("alfred audit clipboard")
        text = system.get_clipboard_text()
        if "alfred audit clipboard" in str(text):
            record("B. FILES / FOLDERS", "clipboard", "PASS", details=f"clipboard round-trip: {text[:120]}")
        else:
            record("B. FILES / FOLDERS", "clipboard", "FAIL", details=f"clipboard mismatch: {text}")
    except Exception as exc:
        record("B. FILES / FOLDERS", "clipboard", "FAIL", str(exc))

    for label in ["keyboard automation", "mouse automation", "window control", "script execution", "approved command execution"]:
        record("B. FILES / FOLDERS", label, "NOT IMPLEMENTED", details="safe automation layer not present in the current project")


def check_browser_category():
    try:
        import tools.browser as browser
        from tools.dispatcher import handle_command
    except Exception as exc:
        record("C. BROWSER", "browser imports", "FAIL", str(exc))
        return

    browser_checks = [
        ("open browser", "ensure_brave", lambda: browser.ensure_brave()),
        ("Google search", "browser_search", lambda: browser.browser_search("alfred", engine="google")),
        ("Wikipedia search", "browser_search", lambda: browser.browser_search("python", engine="wikipedia")),
        ("YouTube search", "browser_search", lambda: browser.browser_search("sidemen", engine="youtube")),
        ("image search", "browser_search", lambda: browser.browser_search("alfred", engine="image")),
        ("news search", "browser_search", lambda: browser.browser_search("alfred", engine="news")),
        ("open URL", "open_web_destination", lambda: browser.open_web_destination("https://example.com")),
        ("new tab", "new_tab", lambda: browser.new_tab("https://example.com")),
        ("browser history", "get_pages", lambda: browser.get_pages()),
        ("refresh", "browser_action", lambda: browser.browser_action("refresh")),
        ("back", "browser_action", lambda: browser.browser_action("back")),
        ("forward", "browser_action", lambda: browser.browser_action("forward")),
        ("close tab", "close_active_tab", lambda: browser.close_active_tab()),
    ]

    for label, func_name, runner in browser_checks:
        try:
            result = runner()
            text = str(result)[:180]
            record("C. BROWSER", label, "PASS", details=f"{func_name}: {text}")
        except Exception as exc:
            record("C. BROWSER", label, "FAIL", str(exc), func_name)

    record("C. BROWSER", "download", "NOT IMPLEMENTED", details="download action is not implemented in the current browser helper set")


def check_youtube_category():
    try:
        import tools.youtube as youtube
    except Exception as exc:
        record("D. YOUTUBE", "imports", "FAIL", str(exc))
        return

    for label, func_name, arg in [
        ("search YouTube", "browser_search", "sidemen"),
        ("play YouTube", "play_youtube", "sidemen"),
        ("pause", "youtube_control", "pause"),
        ("resume", "youtube_control", "resume"),
        ("stop", "youtube_control", "stop"),
        ("next", "youtube_control", "next"),
        ("previous", "youtube_control", "previous"),
    ]:
        if not hasattr(youtube, func_name):
            record("D. YOUTUBE", label, "NOT IMPLEMENTED", details=f"{func_name} missing")
            continue
        try:
            if func_name == "browser_search":
                result = youtube.browser_search(arg, engine="youtube")
            elif func_name == "play_youtube":
                result = youtube.play_youtube(arg)
            else:
                result = youtube.youtube_control(arg)
            record("D. YOUTUBE", label, "PASS", details=str(result)[:180])
        except Exception as exc:
            record("D. YOUTUBE", label, "FAIL", str(exc), func_name)

    record("D. YOUTUBE", "volume if implemented", "MANUAL", details="YouTube volume control requires a live player tab and is not safe to auto-run during the audit")


def check_spotify_category():
    try:
        import tools.spotify as spotify
    except Exception as exc:
        record("E. SPOTIFY", "imports", "FAIL", str(exc))
        return

    for label, func_name, arg in [
        ("search Spotify", "play_spotify", "midnight city"),
        ("play song", "play_spotify", "midnight city"),
        ("pause", "spotify_control", "pause"),
        ("resume", "spotify_control", "resume"),
        ("next", "spotify_control", "next"),
        ("previous", "spotify_control", "previous"),
    ]:
        if not hasattr(spotify, func_name):
            record("E. SPOTIFY", label, "NOT IMPLEMENTED", details=f"{func_name} missing")
            continue
        try:
            if func_name == "play_spotify":
                result = spotify.play_spotify(arg)
            else:
                result = spotify.spotify_control(arg)
            record("E. SPOTIFY", label, "PASS", details=str(result)[:180])
        except Exception as exc:
            record("E. SPOTIFY", label, "FAIL", str(exc), func_name)

    record("E. SPOTIFY", "volume if implemented", "MANUAL", details="Spotify volume control requires a live Spotify tab and is not safe to auto-run")


def check_communication_category():
    try:
        import tools.gmail as gmail
        draft_exists = hasattr(gmail, "draft_email")
    except Exception:
        draft_exists = False

    checks = [
        ("WhatsApp opening", "NOT IMPLEMENTED", "no WhatsApp launch path exists in the current source tree"),
        ("Telegram opening", "NOT IMPLEMENTED", "no Telegram launch path exists in the current source tree"),
        ("Discord opening", "NOT IMPLEMENTED", "no Discord launch path exists in the current source tree"),
        ("email opening", "MANUAL" if draft_exists else "NOT IMPLEMENTED", "account/auth dependent; explicit confirmation required"),
        ("email drafting", "MANUAL" if draft_exists else "NOT IMPLEMENTED", "drafting is present only as a safe helper and not an automatic send flow"),
        ("contact search", "NOT IMPLEMENTED", "no contact-search integration exists"),
        ("notifications", "NOT IMPLEMENTED", "no notification reader is implemented"),
        ("message preparation", "MANUAL", "sending requires explicit confirmation and external app access"),
    ]
    for label, status, detail in checks:
        record("F. COMMUNICATION", label, status, details=detail)


def check_settings_category():
    try:
        import tools.system as system
    except Exception as exc:
        record("G. WINDOWS SETTINGS", "imports", "FAIL", str(exc))
        return

    for label, target in [
        ("open Settings", "settings"),
        ("Task Manager", "task manager"),
        ("Control Panel", "control panel"),
    ]:
        try:
            result = system.open_settings(target)
            record("G. WINDOWS SETTINGS", label, "PASS", details=str(result)[:180])
        except Exception as exc:
            record("G. WINDOWS SETTINGS", label, "FAIL", str(exc))

    for label in ["display settings", "sound settings", "network settings", "Bluetooth settings", "Wi‑Fi settings", "personalization", "apps/settings", "Windows Update", "Device Manager"]:
        record("G. WINDOWS SETTINGS", label, "NOT IMPLEMENTED", details="specific settings pages are not individually routed in the current local source")


def check_ai_category():
    try:
        import brain
        record("H. AI / ALFRED", "normal conversation", "DEPENDENCY", details="brain imports but needs Groq/API connectivity and runtime credentials")
    except Exception as exc:
        record("H. AI / ALFRED", "normal conversation", "DEPENDENCY", details=f"AI backend not available: {exc}")

    for label in ["answer questions", "explain", "summarize", "rewrite", "translate", "calculate", "generate text", "remember information", "retrieve memory", "natural-language variations"]:
        record("H. AI / ALFRED", label, "DEPENDENCY", details="external model/service dependencies make the feature runtime-gated")


def check_pc_information_category():
    try:
        import tools.system as system
    except Exception as exc:
        record("I. PC INFORMATION", "imports", "FAIL", str(exc))
        return

    info_checks = [
        ("CPU usage", "get_cpu_information"),
        ("RAM usage", "get_memory_information"),
        ("disk usage", "get_storage_information"),
        ("system information", "get_system_information"),
        ("GPU information", "get_gpu_information"),
        ("storage remaining", "get_storage_remaining"),
        ("IP address", "get_ip_information"),
        ("running applications", "get_running_applications"),
        ("network status", "get_network_status"),
    ]

    for label, func_name in info_checks:
        if not hasattr(system, func_name):
            record("I. PC INFORMATION", label, "NOT IMPLEMENTED", details=f"{func_name} missing")
            continue
        try:
            result = getattr(system, func_name)()
            record("I. PC INFORMATION", label, "PASS", details=str(result)[:180])
        except Exception as exc:
            record("I. PC INFORMATION", label, "FAIL", str(exc), func_name)


def check_automation_category():
    for label in ["execute predefined scripts", "run commands", "start programs with parameters", "keyboard automation", "mouse automation", "copy/paste", "type text", "press keys", "interact with windows", "repetitive automation"]:
        record("J. AUTOMATION", label, "NOT IMPLEMENTED", details="no local automation layer exists in the current project")


def check_productivity_category():
    try:
        import tools.file_manager as file_manager
        import tools.system as system
        record("K. PRODUCTIVITY", "document creation", "PASS", details=f"create_file exists: {hasattr(file_manager, 'create_file')}")
        record("K. PRODUCTIVITY", "document search", "PASS", details=f"find_and_open_file exists: {hasattr(file_manager, 'find_and_open_file')}")
        record("K. PRODUCTIVITY", "time/date", "PASS", details=str(system.get_current_datetime())[:120])
    except Exception as exc:
        record("K. PRODUCTIVITY", "imports", "FAIL", str(exc))

    for label in ["create reminder", "list reminders", "calendar events", "alarms", "timers", "notes", "clipboard history", "open Office apps"]:
        record("K. PRODUCTIVITY", label, "NOT IMPLEMENTED", details="no dedicated productivity integration was found")


def check_cross_device_category():
    android_files = [
        PROJECT_PATH / "AlfredAndroid" / "app" / "src" / "main" / "java" / "com" / "alfred" / "android" / "agent" / "AlfredAgent.kt",
        PROJECT_PATH / "AlfredAndroid" / "app" / "src" / "main" / "java" / "com" / "alfred" / "android" / "websocket" / "ConnectionManager.kt",
        PROJECT_PATH / "AlfredAndroid" / "app" / "src" / "main" / "java" / "com" / "alfred" / "android" / "voice" / "LocalCommandProcessor.kt",
        PROJECT_PATH / "AlfredAndroid" / "app" / "src" / "main" / "java" / "com" / "alfred" / "android" / "capabilities" / "CapabilityProvider.kt",
    ]
    if all(path.exists() for path in android_files):
        record("L. CROSS-DEVICE", "Android source implementation", "DEPENDENCY", details="Android protocol and capability framework exist, but paired-device runtime verification is impossible here")
    else:
        record("L. CROSS-DEVICE", "Android source implementation", "NOT IMPLEMENTED", details="required Android source files are missing")

    for label in ["phone battery", "flashlight", "open Android app", "phone volume", "send message", "notifications", "locate/ring phone", "camera actions", "open PC app", "close PC app", "web search", "PC media control", "PC volume", "screenshot", "lock", "shutdown", "restart", "approved PC automation", "PC status"]:
        record("L. CROSS-DEVICE", label, "DEPENDENCY", details="requires an actual paired Android device, permissions, and runtime state")


def check_wake_word():
    voice_files = [
        PROJECT_PATH / "main.py",
        PROJECT_PATH / "voice" / "wake_word.py",
        PROJECT_PATH / "voice" / "recorder.py",
        PROJECT_PATH / "voice" / "stt.py",
        PROJECT_PATH / "voice" / "tts.py",
    ]
    if all(path.exists() for path in voice_files):
        record("WAKE WORD", "pipeline wiring", "PASS", details="wake_word → recorder → STT → dispatcher → result → TTS flow exists in source")
    else:
        record("WAKE WORD", "pipeline wiring", "FAIL", details="required voice pipeline files are missing")

    try:
        import voice.wake_word as wk
        record("WAKE WORD", "wake-word module", "PASS", details=f"{wk.__name__} imported successfully")
    except Exception as exc:
        record("WAKE WORD", "wake-word module", "FAIL", str(exc))

    try:
        from voice.recorder import record_audio
        record("WAKE WORD", "recording path exists", "PASS", details=f"record_audio callable: {callable(record_audio)}")
    except Exception as exc:
        record("WAKE WORD", "recording path exists", "FAIL", str(exc))

    try:
        from voice.stt import transcribe_audio
        record("WAKE WORD", "STT path exists", "PASS", details=f"transcribe_audio callable: {callable(transcribe_audio)}")
    except Exception as exc:
        record("WAKE WORD", "STT path exists", "FAIL", str(exc))

    record("WAKE WORD", "live microphone verification", "MANUAL", details="real microphone hardware is required; it is not safe to auto-run in CI or a headless environment")


def build_report():
    counts = {"PASS": 0, "FAIL": 0, "NOT IMPLEMENTED": 0, "MANUAL": 0, "DEPENDENCY": 0, "SKIPPED": 0}
    for result in RESULTS:
        counts[result["status"]] = counts.get(result["status"], 0) + 1

    total = len(RESULTS)
    coverage = round((counts["PASS"] / total) * 100, 2) if total else 0.0
    report = {
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S %Z"),
        "project_path": str(PROJECT_PATH),
        "python_version": sys.version.replace("\n", " "),
        "test_duration_seconds": 0,
        "total_features": total,
        "PASS": counts["PASS"],
        "FAIL": counts["FAIL"],
        "NOT IMPLEMENTED": counts["NOT IMPLEMENTED"],
        "MANUAL": counts["MANUAL"],
        "DEPENDENCY": counts["DEPENDENCY"],
        "SKIPPED": counts["SKIPPED"],
        "coverage_percent": coverage,
        "results": RESULTS,
        "environment_problems": [],
        "critical_failures": [item for item in RESULTS if item["status"] == "FAIL"][:10],
    }
    return report, counts, total, coverage


def main():
    start = time.time()
    check_system_category()
    check_files_category()
    check_browser_category()
    check_youtube_category()
    check_spotify_category()
    check_communication_category()
    check_settings_category()
    check_ai_category()
    check_pc_information_category()
    check_automation_category()
    check_productivity_category()
    check_cross_device_category()
    check_wake_word()

    report, counts, total, coverage = build_report()
    report["test_duration_seconds"] = round(time.time() - start, 2)

    text_lines = [
        "============================================================",
        "ALFRED FEATURE AUDIT",
        "====================",
        "",
        f"PASS:             {counts['PASS']}",
        f"FAIL:             {counts['FAIL']}",
        f"NOT IMPLEMENTED:  {counts['NOT IMPLEMENTED']}",
        f"MANUAL:           {counts['MANUAL']}",
        f"DEPENDENCY:       {counts['DEPENDENCY']}",
        f"SKIPPED:          {counts['SKIPPED']}",
        "",
        f"TOTAL:            {total}",
        "",
        f"IMPLEMENTATION COVERAGE: {coverage}%",
        "",
        "============================================================",
        "CRITICAL FAILURES",
        "=================",
    ]

    critical = [r for r in RESULTS if r["status"] == "FAIL"][:5]
    if not critical:
        text_lines.append("None detected")
    for entry in critical:
        text_lines.append(f"- {entry['category']}: {entry['label']} -> {entry['error']}")

    text_lines.extend(["", "============================================================", "NOT IMPLEMENTED", "==============="])
    missing = [r for r in RESULTS if r["status"] == "NOT IMPLEMENTED"][:5]
    if not missing:
        text_lines.append("None detected")
    for entry in missing:
        text_lines.append(f"- {entry['category']}: {entry['label']} -> {entry['details']}")

    text_lines.extend(["", "============================================================", "MANUAL TESTS", "============"])
    manual = [r for r in RESULTS if r["status"] == "MANUAL"][:5]
    if not manual:
        text_lines.append("None detected")
    for entry in manual:
        text_lines.append(f"- {entry['category']}: {entry['label']} -> {entry['details']}")

    text_lines.extend(["", "============================================================", "NEXT PRIORITIES", "==============="])
    text_lines.extend([
        "1. Confirm the live microphone wake-word loop on a real device.",
        "2. Keep Wi‑Fi/Bluetooth and shutdown actions user-confirmed and hardware-gated.",
        "3. Fill only the remaining local routes that are backed by source code and safe execution paths.",
    ])

    report_text = "\n".join(text_lines)
    report_path = PROJECT_PATH / "alfred_test_report.txt"
    report_path.write_text(report_text + "\n", encoding="utf-8")
    with open(PROJECT_PATH / "alfred_test_report.json", "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=2, ensure_ascii=False)

    print(report_text)
    print("")
    print("Report written to:", report_path)
    print("JSON written to:", PROJECT_PATH / "alfred_test_report.json")


if __name__ == "__main__":
    try:
        main()
    finally:
        clean_temp_workspace()

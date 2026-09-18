# ALFRED Project Brain

Updated: 2026-09-18
Workspace: `D:\alfred`

## Purpose

ALFRED is a Windows/Python assistant with local tools, a Hub/device layer, a local wake-word model, speech input/output components, and an Android companion app. The intended voice path is:

`Alfred` -> command recognition -> command routing / LocalCommandProcessor -> response -> speech output -> wake listening again.

The current source tree is the source of truth. This document records the repository inventory, current completion state, evidence collected, and the next tests. It does not claim hardware behavior that has not been tested.

## Repository Inventory

A complete recursive filesystem inventory was taken on 2026-09-18.

- Total files: 96,636
- Total directories: 13,950
- The large count includes virtual environments, vendored projects, Android/Gradle outputs, Python bytecode, compiled libraries, model files, datasets, caches, and source code.
- The inventory was taken with hidden files included. No source files were modified during inventory collection.

### Top-level files

- `.env`: local environment configuration; sensitive values must stay private.
- `.gitignore`: excludes environments, generated data, credentials, audio, and other large/private files.
- `al.docx`: document artifact.
- `alfred.onnx`: root PC Alfred wake model; 152,605 bytes.
- `alfred_diagnostic_results.csv`: wake-model diagnostic results.
- `alfred_model.yml`: custom wake-model training configuration.
- `alfred_speech.wav`, `alfred_test.wav`, `test_recording.wav`, `voice_input.wav`, `aegis_test.wav`: recorded audio artifacts; some are test inputs and some may be empty or generated.
- `alfred_test_report.json`, `alfred_test_report.txt`: latest broad feature-audit outputs.
- `AlfredAndroid.zip`, `Alfred_Smart_Command_Phase.zip`: archived project artifacts.
- `aliyan`: device/configuration artifact.
- `brain.py`: main cloud/local AI orchestration and tool-routing implementation.
- `brain_groq_backup.py`: backup AI implementation.
- `checkmodel.py`: model inspection utility.
- `credentials.json`, `gmail_token.json`: private credentials/tokens; do not expose or commit.
- `device_registry.json`: registered device metadata.
- `main.py`: primary PC application entry point.
- `memory.py`: persistent memory database helpers.
- `memory.db`: local memory database.
- `mic_test.py`: microphone stream and volume test.
- `readme.md`: short project description.
- `Record (online-voice-recorder.com).mp3`: recorded wake-word test input.
- `requirements.txt`: Python dependency list.
- `start_alfred.bat`: Windows launcher.
- `test.py`: small project test/utility script.
- `test_aegis.py`: Aegis test.
- `test_alfred.py`: broad ALFRED feature tests.
- `test_alfred_onnx.py`: finite ONNX model isolation test.
- `test_command.py`: command behavior test.
- `test_device_registry.py`: device registry test.
- `test_main_lifecycle.py`: PC application lifecycle test.
- `test_master_pc_core.py`: PC core test.
- `test_microphones.py`: microphone enumeration/test helper.
- `test_realtime_alfred.py`: live microphone wake-word test; currently uses device index 1, 16 kHz, 1280-frame chunks, threshold 0.40, and a two-second cooldown.
- `test_windows_feature_modules.py`: Windows feature tests.
- `testmic.py`: live microphone level test using device index 1.
- `teststt.py`: recorded-audio speech-to-text test.
- `test_wake_model.py`: recorded-audio wake-model test.
- `test_wake_model_v2.py`: expanded recorded-audio wake diagnostic.
- `wake_word.py`: older live wake listener; currently configured for `alexa_v0.1`, so it is not the preferred Alfred test path.
- `wakeword.yaml`: newer custom Alfred wake-word training configuration.

### Top-level directories

- `AlfredAndroid/` (3,361 files): Kotlin/Compose Android companion app. Contains the foreground service, local OpenWakeWord adapter, TTS/SpeechRecognizer flow, dashboard, deterministic tests, Gradle project, and Android assets. Required models are in `app/src/main/assets/` and have been verified in the debug APK.
- `AlfredWakeWord/` (41 files): wake-word dataset preparation/training project.
- `assistants/` (3 files): assistant profiles and routing helpers.
- `hub/` (40 files): PC/device hub protocol, client, server, routing, executors, mocks, and tests.
- `livekit-wakeword/` (155 files): separate LiveKit/Swift wake-word project and examples; not the primary Android or PC Alfred path.
- `models/` (4 files): local model assets/configuration area.
- `openWakeWord/` (100 files): vendored openWakeWord Python package and examples; the PC model tests use the installed package from `.venv`.
- `oww_extract/` (29 files): extracted OpenWakeWord/AAR inspection artifacts.
- `piper/` (360 files): Piper speech/TTS data and runtime assets.
- `research/` (14 files): research notes and YouTube/PC-agent test logs.
- `tools/` (50 files): local PC automation, media, system, browser, email, and utility tools.
- `voice/` (12 files): PC speech input/output and STT helpers.
- `wakeword_data/` (2,100 files): wake-word recordings, backgrounds, RIRs, and training data.
- `wakeword_output/` (101 files): generated wake-word training/output data.
- `.venv/` (59,393 files): active Python virtual environment; use `D:\alfred\.venv\Scripts\python.exe` for PC tests.
- `training_venv/` (30,039 files): training environment.
- `.venv-1/` (498 files): additional environment.
- `.git/` (280 files): Git metadata; not application source.
- `__pycache__/` (5 files): generated Python bytecode.
- `tmp_oww_aar/`, `tmp_oww_classes/`, `tmp_oww_decompile/`: temporary OpenWakeWord Android inspection artifacts; the latter two are currently empty.

### File-type scale

The recursive tree contains approximately:

- 24,827 Python source files and 24,234 compiled Python files, mostly from environments/vendor trees.
- 1,950 ONNX files, mostly model/vendor/environment content.
- 1,262 WAV files, mostly datasets and test recordings.
- 1,030 Java class files and 482 DEX files from Android/build outputs.
- 85 Kotlin files, 17 Swift files, 78 JSON files outside the larger generated/environment inventory, and 117 Markdown files.

The generated/vendor/environment files are included in the inventory but are not treated as individual ALFRED implementation units. The meaningful application units are the root PC files, `assistants/`, `hub/`, `tools/`, `voice/`, `AlfredAndroid/`, and the wake-word projects.

## Current Completion Status

### Verified

- PC ONNX model loads successfully in the project `.venv`.
- `test_alfred_onnx.py` completes successfully for silence, low noise, medium noise, loud noise, and synthetic impulses.
- The finite ONNX sanity test produced no scores at or above 0.50, 0.75, or 0.90 for those synthetic inputs.
- Silence did not produce a strong activation; maximum silence score was approximately 0.124952.
- Windows microphone enumeration works in `.venv`.
- Available inputs include the TWS headset, Realtek microphone array, stereo mix, and other Bluetooth/WDM inputs.
- Current default input is device 1: `Headset (TWS Hands-Free AG Audio)`.
- Android unit tests previously passed.
- Android debug APK previously built successfully.
- Android APK previously contained `alfred.onnx`, `melspectrogram.onnx`, and `embedding_model.onnx`.
- Android voice lifecycle and TTS initialization diagnostics were added without creating a second voice architecture.

### Not yet proven

- Live spoken `Alfred` detection on the PC microphone.
- PC end-to-end wake -> STT -> command -> response loop.
- PC false-positive rate in a quiet room.
- Android physical-device wake detection.
- Android physical-device microphone behavior.
- Android SpeechRecognizer behavior on the handset.
- Actual British voice playback on a handset.
- Complete Android voice loop.

### Broad feature audit snapshot

From `alfred_test_report.txt` and `alfred_test_report.json` dated 2026-09-09:

- PASS: 71
- FAIL: 0
- NOT IMPLEMENTED: 43
- MANUAL: 21
- DEPENDENCY: 31
- SKIPPED: 0
- Total features: 166
- Reported implementation coverage: 42.77%

That audit is broader than wake-word functionality and should not be interpreted as voice-loop completion.

## Wake-Word Test Plan

### Test A: model-only sanity

Command:

```powershell
& D:\alfred\.venv\Scripts\python.exe D:\alfred\test_alfred_onnx.py
```

Purpose: verify the ONNX model loads and does not activate on synthetic silence/noise. Status: PASS for the 2026-09-18 run.

### Test B: microphone level

Command:

```powershell
& D:\alfred\.venv\Scripts\python.exe D:\alfred\testmic.py
```

Purpose: confirm the selected input receives real audio and identify a usable device. Speak normally and stop with Ctrl+C. This is a live/manual test.

### Test C: live PC Alfred wake word

Preferred command:

```powershell
& D:\alfred\.venv\Scripts\python.exe D:\alfred\test_realtime_alfred.py
```

Current configuration: device index 1, 16,000 Hz, 1,280-frame chunks, threshold 0.40, two-second cooldown. Say `Alfred`, record whether `ALFRED DETECTED!` appears, note the score, then stop with Ctrl+C.

If device 1 is not the microphone being used, change only the test configuration to a confirmed input such as:

- device 2: `Microphone Array (Realtek Audio)`
- device 19: `Microphone Array (Realtek Audio)`, WASAPI
- device 21: TWS hands-free, WASAPI

Do not claim detection until the spoken test produces an observed detection event.

### Test D: recorded wake-word scoring

Commands:

```powershell
& D:\alfred\.venv\Scripts\python.exe D:\alfred\test_wake_model.py
& D:\alfred\.venv\Scripts\python.exe D:\alfred\test_wake_model_v2.py
```

Purpose: score the existing recording, inspect peak/RMS/timing, and investigate false positives. These are not substitutes for a live microphone test.

### Test E: speech recognition

1. Run `testmic.py` to create/confirm `test_recording.wav`.
2. Run `teststt.py`.
3. Compare transcription with the spoken command.

This requires the configured STT/Groq environment and is separate from wake detection.

## What Remains To Do

1. Run `testmic.py` and confirm the microphone has non-zero levels.
2. Run `test_realtime_alfred.py` with the correct physical microphone.
3. Say `Alfred` several times at normal distance and record scores/detections.
4. Run quiet-room observation for at least 10 minutes and record false activations.
5. Tune the PC threshold only after collecting real scores; do not lower it based on synthetic tests.
6. Verify the PC command path after a real wake event: STT -> parser/router -> tool or LocalCommandProcessor -> response.
7. Check PC TTS separately if the response is silent.
8. Install the Android debug APK on a physical handset and execute the Android manual checklist.
9. Record actual Android TTS engine, selected voice name, locale, and whether `en-GB` exists.
10. Keep real hardware results marked `MANUAL` until observed and logged.

## Known Limitations / Risks

- `wake_word.py` is an older Alexa-configured listener and should not be used as the canonical Alfred test.
- `test_realtime_alfred.py` hardcodes device index 1; Windows device numbering can change.
- The current finite model test does not include a verified spoken `Alfred` recording in this run.
- The root `alfred.onnx` is validated for loading and basic synthetic behavior, not for live detection quality.
- Credentials and tokens exist in the workspace and must remain private.
- The recursive tree includes large generated and virtual-environment content; do not mass-edit or commit it.
- No physical Android device was connected during the previous APK install attempt.

## Evidence Log

- 2026-09-18: Full recursive inventory: 96,636 files and 13,950 directories.
- 2026-09-18: Active `.venv` confirmed `openwakeword` and `sounddevice` imports.
- 2026-09-18: `test_alfred_onnx.py` completed successfully with no synthetic threshold crossings at 0.50, 0.75, or 0.90.
- 2026-09-18: `sounddevice.query_devices()` found multiple Windows microphone inputs; default input reported `[1, 5]`.
- 2026-09-18: Live spoken wake-word test remains pending; no live detection result is claimed.

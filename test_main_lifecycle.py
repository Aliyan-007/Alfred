import os
import subprocess
import sys
import unittest
from unittest.mock import patch


ROOT = os.path.dirname(__file__)


class MainLifecycleTest(unittest.TestCase):
    def test_main_module_import_is_safe(self):
        code = (
            "import os, sys; "
            "sys.path.insert(0, os.getcwd()); "
            "import main; "
            "print('IMPORTED')"
        )
        result = subprocess.run(
            [sys.executable, "-c", code],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=10,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("IMPORTED", result.stdout)

    def test_voice_cycle_runs_twice_and_returns_to_listening(self):
        import main as alfred_main

        with patch.object(alfred_main, "record_audio", side_effect=["voice_1.wav", "voice_2.wav"]), \
             patch.object(alfred_main, "transcribe_audio", side_effect=["what time is it", "what time is it"]), \
             patch.object(alfred_main, "safe_speak", return_value=None), \
             patch.object(alfred_main, "handle_command", side_effect=["The time is 4:20 PM.", "The time is 4:21 PM."]):

            first_result = alfred_main.process_command()
            second_result = alfred_main.process_command()

        self.assertIsInstance(first_result, str)
        self.assertIsInstance(second_result, str)
        self.assertIn("time", first_result.lower())
        self.assertIn("time", second_result.lower())

    def test_failed_transcription_returns_to_listening(self):
        import main as alfred_main

        with patch.object(alfred_main, "record_audio", return_value="voice_input.wav"), \
             patch.object(alfred_main, "transcribe_audio", side_effect=RuntimeError("transcription failed")):
            result = alfred_main.process_command()

        self.assertIsNone(result)

    def test_empty_transcription_returns_to_listening(self):
        import main as alfred_main

        with patch.object(alfred_main, "record_audio", return_value="voice_input.wav"), \
             patch.object(alfred_main, "transcribe_audio", return_value="   "):
            result = alfred_main.process_command()

        self.assertIsNone(result)

    def test_command_exception_returns_to_listening(self):
        import main as alfred_main

        with patch.object(alfred_main, "record_audio", return_value="voice_input.wav"), \
             patch.object(alfred_main, "transcribe_audio", return_value="what time is it"), \
             patch.object(alfred_main, "handle_command", side_effect=RuntimeError("dispatcher failed")), \
             patch.object(alfred_main, "safe_speak", return_value=None):
            result = alfred_main.process_command()

        self.assertIsInstance(result, str)
        self.assertIn("error", result.lower())

    def test_tts_exception_returns_to_listening(self):
        import main as alfred_main

        with patch.object(alfred_main, "record_audio", return_value="voice_input.wav"), \
             patch.object(alfred_main, "transcribe_audio", return_value="what time is it"), \
             patch.object(alfred_main, "handle_command", return_value="The time is 4:20 PM."), \
             patch.object(alfred_main, "safe_speak", side_effect=RuntimeError("tts failed")):
            result = alfred_main.process_command()

        self.assertIsInstance(result, str)
        self.assertIn("time", result.lower())


if __name__ == "__main__":
    unittest.main()

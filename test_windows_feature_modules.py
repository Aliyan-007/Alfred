import importlib
import unittest


class WindowsFeatureModulesTest(unittest.TestCase):
    def test_windows_feature_modules_exist(self):
        modules = [
            "tools.network",
            "tools.bluetooth",
            "tools.display",
            "tools.hardware",
        ]

        for module_name in modules:
            with self.subTest(module=module_name):
                module = importlib.import_module(module_name)
                self.assertIsNotNone(module)

    def test_windows_feature_modules_expose_expected_functions(self):
        network = importlib.import_module("tools.network")
        bluetooth = importlib.import_module("tools.bluetooth")
        display = importlib.import_module("tools.display")
        hardware = importlib.import_module("tools.hardware")
        system = importlib.import_module("tools.system")

        self.assertTrue(hasattr(network, "get_network_status"))
        self.assertTrue(hasattr(network, "toggle_wifi"))
        self.assertTrue(hasattr(network, "connect_to_wifi_network"))
        self.assertTrue(hasattr(bluetooth, "get_bluetooth_status"))
        self.assertTrue(hasattr(bluetooth, "toggle_bluetooth"))
        self.assertTrue(hasattr(bluetooth, "list_bluetooth_devices"))
        self.assertTrue(hasattr(display, "set_brightness"))
        self.assertTrue(hasattr(display, "adjust_brightness"))
        self.assertTrue(hasattr(display, "get_brightness"))
        self.assertTrue(hasattr(system, "get_usb_inventory"))
        self.assertTrue(hasattr(system, "get_audio_device_inventory"))
        self.assertTrue(hasattr(system, "get_display_information"))
        self.assertTrue(hasattr(hardware, "get_system_information"))
        self.assertTrue(hasattr(hardware, "get_cpu_information"))
        self.assertTrue(hasattr(hardware, "get_memory_information"))

    def test_usb_audio_display_brightness_helpers_are_safe_and_structured(self):
        import tools.system as system
        from tools.dispatcher import handle_command

        usb = system.get_usb_inventory()
        self.assertIsInstance(usb, list)

        audio = system.get_audio_device_inventory()
        self.assertIsInstance(audio, dict)
        self.assertIn("playback", audio)
        self.assertIn("recording", audio)

        display_info = system.get_display_information()
        self.assertIsInstance(display_info, dict)
        self.assertIn("monitors", display_info)
        self.assertIn("count", display_info)

        brightness = system.get_brightness()
        self.assertIsInstance(brightness, dict)
        self.assertIn("supported", brightness)
        self.assertIn("limitation", brightness)

        self.assertIsNotNone(handle_command("show my USB devices"))
        self.assertIsNotNone(handle_command("show my audio devices"))
        self.assertIsNotNone(handle_command("show my display information"))
        self.assertIsNotNone(handle_command("show brightness"))


if __name__ == "__main__":
    unittest.main()

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

        self.assertTrue(hasattr(network, "get_network_status"))
        self.assertTrue(hasattr(network, "toggle_wifi"))
        self.assertTrue(hasattr(network, "connect_to_wifi_network"))
        self.assertTrue(hasattr(bluetooth, "get_bluetooth_status"))
        self.assertTrue(hasattr(bluetooth, "toggle_bluetooth"))
        self.assertTrue(hasattr(bluetooth, "list_bluetooth_devices"))
        self.assertTrue(hasattr(display, "set_brightness"))
        self.assertTrue(hasattr(display, "adjust_brightness"))
        self.assertTrue(hasattr(hardware, "get_system_information"))
        self.assertTrue(hasattr(hardware, "get_cpu_information"))
        self.assertTrue(hasattr(hardware, "get_memory_information"))


if __name__ == "__main__":
    unittest.main()

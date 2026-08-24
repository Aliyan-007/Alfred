from tools.device_registry import (
    register_device,
    list_devices,
)


# Register the current PC
register_device(
    device_id="pc_01",
    name="My PC",
    device_type="pc",
    capabilities=[
        "browser",
        "spotify",
        "youtube",
        "web_search",
        "filesystem",
        "applications",
    ],
)


# Display registered devices
devices = list_devices()

print()
print("REGISTERED DEVICES")
print("=" * 50)

for device in devices:
    print(device)

print()
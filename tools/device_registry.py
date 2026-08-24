import json
import os
from datetime import datetime, timezone


# =========================================================
# STORAGE
# =========================================================

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

REGISTRY_FILE = os.path.join(
    BASE_DIR,
    "device_registry.json",
)


# =========================================================
# INTERNAL HELPERS
# =========================================================

def _load_registry():
    if not os.path.exists(
        REGISTRY_FILE
    ):
        return {}

    try:
        with open(
            REGISTRY_FILE,
            "r",
            encoding="utf-8",
        ) as file:
            data = json.load(file)

        if isinstance(data, dict):
            return data

    except Exception:
        pass

    return {}


def _save_registry(
    devices,
):
    with open(
        REGISTRY_FILE,
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            devices,
            file,
            ensure_ascii=False,
            indent=2,
        )


def _utc_now():
    return datetime.now(
        timezone.utc
    ).isoformat()


# =========================================================
# REGISTER DEVICE
# =========================================================

def register_device(
    device_id: str,
    name: str,
    device_type: str,
    capabilities=None,
    permissions=None,
):
    """
    Add a device to the ALFRED device registry.

    If the device already exists, its information is updated.
    """

    if not device_id.strip():
        raise ValueError(
            "device_id cannot be empty"
        )

    if capabilities is None:
        capabilities = []

    if permissions is None:
        permissions = []

    devices = _load_registry()

    existing = devices.get(
        device_id,
        {},
    )

    devices[device_id] = {
        "id": device_id,
        "name": name,
        "type": device_type,
        "online": True,
        "last_seen": _utc_now(),
        "capabilities": list(
            capabilities
        ),
        "permissions": list(
            permissions
        ),
        "metadata": existing.get(
            "metadata",
            {},
        ),
    }

    _save_registry(
        devices
    )

    return devices[
        device_id
    ]


# =========================================================
# GET DEVICE
# =========================================================

def get_device(
    device_id: str,
):
    devices = _load_registry()

    return devices.get(
        device_id
    )


# =========================================================
# LIST DEVICES
# =========================================================

def list_devices():
    devices = _load_registry()

    return list(
        devices.values()
    )


# =========================================================
# MARK ONLINE
# =========================================================

def mark_online(
    device_id: str,
):
    devices = _load_registry()

    if device_id not in devices:
        return False

    devices[
        device_id
    ][
        "online"
    ] = True

    devices[
        device_id
    ][
        "last_seen"
    ] = _utc_now()

    _save_registry(
        devices
    )

    return True


# =========================================================
# MARK OFFLINE
# =========================================================

def mark_offline(
    device_id: str,
):
    devices = _load_registry()

    if device_id not in devices:
        return False

    devices[
        device_id
    ][
        "online"
    ] = False

    _save_registry(
        devices
    )

    return True


# =========================================================
# UPDATE LAST SEEN
# =========================================================

def update_last_seen(
    device_id: str,
):
    devices = _load_registry()

    if device_id not in devices:
        return False

    devices[
        device_id
    ][
        "online"
    ] = True

    devices[
        device_id
    ][
        "last_seen"
    ] = _utc_now()

    _save_registry(
        devices
    )

    return True


# =========================================================
# UPDATE CAPABILITIES
# =========================================================

def update_capabilities(
    device_id: str,
    capabilities,
):
    devices = _load_registry()

    if device_id not in devices:
        return False

    devices[
        device_id
    ][
        "capabilities"
    ] = list(
        capabilities
    )

    devices[
        device_id
    ][
        "last_seen"
    ] = _utc_now()

    _save_registry(
        devices
    )

    return True


# =========================================================
# UPDATE PERMISSIONS
# =========================================================

def update_permissions(
    device_id: str,
    permissions,
):
    devices = _load_registry()

    if device_id not in devices:
        return False

    devices[
        device_id
    ][
        "permissions"
    ] = list(
        permissions
    )

    _save_registry(
        devices
    )

    return True
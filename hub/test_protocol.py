from .protocol import (
    create_command,
    validate_command,
)


# =========================================================
# CREATE A COMMAND
# =========================================================

command = create_command(
    device_id="pc_01",
    action="open_application",
    parameters={
        "name": "spotify",
    },
)

print()
print("CREATED COMMAND")
print("=" * 50)
print(command)
print()


# =========================================================
# VALIDATE THE COMMAND
# =========================================================

valid, message = validate_command(
    command
)

print(
    "VALID:",
    valid,
)

print(
    "MESSAGE:",
    message,
)

print()


# =========================================================
# TEST INVALID COMMAND
# =========================================================

bad_command = {
    "id": "cmd_test",
    "device": "pc_01",
    "action": "something_dangerous",
    "parameters": {},
}

valid, message = validate_command(
    bad_command
)

print(
    "INVALID COMMAND TEST:"
)

print(
    "VALID:",
    valid,
)

print(
    "MESSAGE:",
    message,
)

print()

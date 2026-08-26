from hub.hub_client import (
    send_command,
)


print()
print(
    "=" * 60
)
print(
    "              HUB CLIENT TEST"
)
print(
    "=" * 60
)
print()


result = send_command(
    device="pc_01",
    action="ping",
)

print(
    "PING RESULT:"
)

print(
    result
)

print()


result = send_command(
    device="pc_01",
    action="open_application",
    parameters={
        "name": "notepad",
    },
)

print(
    "OPEN APPLICATION RESULT:"
)

print(
    result
)

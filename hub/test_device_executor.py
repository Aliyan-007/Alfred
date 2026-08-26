
from hub.device_executor import (
    execute_device_command,
)


# =========================================================
# TEST
# =========================================================

def main():

    print()

    print(
        "=" * 60
    )

    print(
        "       ALFRED DEVICE EXECUTOR TEST"
    )

    print(
        "=" * 60
    )

    print()

    print(
        "[TEST] Sending ping..."
    )

    result = execute_device_command(
        "open_application",
        {
            "application": "notepad",
        },  
    )

    print()

    print(
        "[TEST] RESULT:"
    )

    print(
        result
    )

    print()

    print(
        "=" * 60
    )


# =========================================================
# ENTRY POINT
# =========================================================

if __name__ == "__main__":

    main()

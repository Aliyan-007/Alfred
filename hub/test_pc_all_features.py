from hub.device_executor import (
    execute_device_command,
)


def run_test(
    name,
    action,
    parameters=None,
):

    print()
    print("-" * 60)
    print(f"[TEST] {name}")
    print(f"Action: {action}")
    print(f"Parameters: {parameters or {}}")
    print("-" * 60)

    result = execute_device_command(
        action,
        parameters or {},
    )

    print()
    print("[RESULT]")
    print(result)

    success = result.get(
        "success",
        False,
    )

    if success:

        print("[PASS]")
        return True

    print("[FAIL]")
    return False


def main():

    print()
    print("=" * 70)
    print("          ALFRED COMPLETE PC CAPABILITY TEST")
    print("=" * 70)

    tests = [

        # --------------------------------------------------
        # BASIC
        # --------------------------------------------------

        (
            "Ping",
            "ping",
            {},
        ),

        # --------------------------------------------------
        # APPLICATION / WEB
        # --------------------------------------------------

        (
            "Open Notepad",
            "open_application",
            {
                "application": "notepad",
            },
        ),

        (
            "Open Google",
            "open_url",
            {
                "url": "https://www.google.com",
            },
        ),

        (
            "Web Search",
            "web_search",
            {
                "query": "Python programming",
            },
        ),

        # --------------------------------------------------
        # SPOTIFY
        # --------------------------------------------------

        (
            "Play Spotify",
            "play_spotify",
            {
                "query": "Imagine Dragons Believer",
            },
        ),

        (
            "Spotify Control",
            "spotify_control",
            {
                "command": "pause",
            },
        ),

        # --------------------------------------------------
        # YOUTUBE
        # --------------------------------------------------

        (
            "Play YouTube",
            "play_youtube",
            {
                "query": "lofi hip hop",
            },
        ),

        (
            "YouTube Control",
            "youtube_control",
            {
                "command": "pause",
            },
        ),

        (
            "Research YouTube",
            "research_youtube",
            {
                "query": "Python tutorials",
            },
        ),

        # --------------------------------------------------
        # VOLUME
        # --------------------------------------------------

        (
            "Volume Up",
            "pc_volume_up",
            {},
        ),

        (
            "Volume Down",
            "pc_volume_down",
            {},
        ),

        (
            "Mute Volume",
            "pc_volume_mute",
            {},
        ),

        (
            "Unmute Volume",
            "pc_volume_unmute",
            {},
        ),

        # --------------------------------------------------
        # FILES
        # --------------------------------------------------

        (
            "Save To Notepad",
            "save_to_notepad",
            {
                "content": (
                    "ALFRED PC capability test."
                ),
            },
        ),

        (
            "Save To Word",
            "save_to_word",
            {
                "content": (
                    "ALFRED PC capability test."
                ),
                "filename": (
                    "alfred_test_document.docx"
                ),
            },
        ),

        # --------------------------------------------------
        # EMAIL
        # --------------------------------------------------

        (
            "Draft Email",
            "draft_email",
            {
                "recipient": "test@example.com",
                "subject": "ALFRED Test",
                "body": (
                    "This is a PC capability test."
                ),
            },
        ),

        (
            "Send Pending Email",
            "send_pending_email",
            {},
        ),

    ]

    passed = 0
    failed = 0

    results = []

    for (
        name,
        action,
        parameters,
    ) in tests:

        success = run_test(
            name,
            action,
            parameters,
        )

        results.append(
            (
                name,
                success,
            )
        )

        if success:

            passed += 1

        else:

            failed += 1

    print()
    print()
    print("=" * 70)
    print("               PC CAPABILITY TEST SUMMARY")
    print("=" * 70)
    print()

    for (
        name,
        success,
    ) in results:

        status = (
            "[PASS]"
            if success
            else "[FAIL]"
        )

        print(
            f"{status} {name}"
        )

    print()
    print("-" * 70)

    print(
        f"TOTAL:  {len(tests)}"
    )

    print(
        f"PASSED: {passed}"
    )

    print(
        f"FAILED: {failed}"
    )

    print("-" * 70)

    if failed == 0:

        print()
        print(
            "ALL PC FEATURES PASSED."
        )

    else:

        print()
        print(
            "SOME PC FEATURES FAILED."
        )


if __name__ == "__main__":

    main()

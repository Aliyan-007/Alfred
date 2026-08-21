import subprocess


# =========================================================
# APPLICATIONS ALFRED IS ALLOWED TO OPEN
# =========================================================

APPLICATIONS = {
    "notepad": [
        "notepad.exe"
    ],

    "calculator": [
        "calc.exe"
    ],

    "file explorer": [
        "explorer.exe"
    ],

    "explorer": [
        "explorer.exe"
    ],

    "chrome": [
        "cmd",
        "/c",
        "start",
        "",
        "chrome"
    ],

    "brave": [
        r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe"
    ],

    "vscode": [
        "code"
    ],

    "vs code": [
        "code"
    ],
}

# =========================================================
# OPEN APPLICATION
# =========================================================

def open_application(
    application: str,
) -> str:

    application = (
        application
        .lower()
        .strip()
    )

    command = APPLICATIONS.get(
        application
    )

    if command is None:

        return (
            f"I don't have permission to open "
            f"'{application}'."
        )

    try:

        subprocess.Popen(
            command,
            shell=False,
        )

        return (
            f"Opened {application}."
        )

    except Exception as error:

        return (
            f"I couldn't open {application}: "
            f"{error}"
        )


# =========================================================
# TEST
# =========================================================

if __name__ == "__main__":

    print(
        open_application("notepad")
    )
from pathlib import Path
import os


# =========================================================
# SAFE BASE DIRECTORIES
# =========================================================

HOME = Path.home()

ALFRED_DIR = HOME / "Desktop" / "alfred"

ALLOWED_ROOTS = [
    HOME / "Desktop",
    HOME / "Documents",
    HOME / "Downloads",
    ALFRED_DIR,
]


# =========================================================
# PATH SAFETY
# =========================================================

def safe_path(path: str) -> Path:
    """
    Resolve a path and make sure it is inside one of the
    approved user directories.
    """

    candidate = Path(path).expanduser()

    if not candidate.is_absolute():
        candidate = HOME / candidate

    candidate = candidate.resolve()

    for root in ALLOWED_ROOTS:

        try:
            candidate.relative_to(
                root.resolve()
            )
            return candidate
        except ValueError:
            continue

    raise PermissionError(
        "That path is outside ALFRED's approved directories."
    )


# =========================================================
# FIND FILES
# =========================================================

def find_files(
    name: str,
    location: str = "Desktop",
    max_results: int = 20,
):
    """
    Find files or folders by name.
    """

    name = name.strip()

    if not name:
        return "Please tell me what file or folder to find, Sir."

    roots = {
        "desktop": HOME / "Desktop",
        "documents": HOME / "Documents",
        "downloads": HOME / "Downloads",
        "alfred": ALFRED_DIR,
    }

    root = roots.get(
        location.lower().strip(),
        HOME / "Desktop",
    )

    if not root.exists():
        return f"{root} does not exist, Sir."

    matches = []

    lowered = name.lower()

    try:

        for item in root.rglob("*"):

            if lowered in item.name.lower():

                matches.append(
                    str(item)
                )

                if len(matches) >= max_results:
                    break

    except PermissionError:
        pass

    if not matches:
        return (
            f"I couldn't find '{name}' in "
            f"{location}, Sir."
        )

    return (
        f"Found {len(matches)} result(s):\n"
        + "\n".join(
            f"- {path}"
            for path in matches
        )
    )


# =========================================================
# LIST DIRECTORY
# =========================================================

def list_directory(
    path: str = "Desktop",
):
    """
    List files and folders in an approved directory.
    """

    try:

        directory = safe_path(
            path
        )

    except Exception as error:

        return str(error)

    if not directory.exists():

        return (
            f"The directory '{directory}' "
            "does not exist, Sir."
        )

    if not directory.is_dir():

        return (
            f"'{directory}' is not a directory, Sir."
        )

    try:

        items = sorted(
            directory.iterdir(),
            key=lambda item: (
                not item.is_dir(),
                item.name.lower(),
            ),
        )

    except PermissionError:

        return (
            f"I don't have permission to read "
            f"'{directory}', Sir."
        )

    if not items:

        return (
            f"'{directory}' is empty, Sir."
        )

    lines = []

    for item in items[:100]:

        kind = (
            "[DIR]"
            if item.is_dir()
            else "[FILE]"
        )

        lines.append(
            f"{kind} {item.name}"
        )

    return (
        f"Contents of {directory}:\n"
        + "\n".join(lines)
    )


# =========================================================
# CREATE FOLDER
# =========================================================

def create_folder(
    name: str,
    parent: str = "Desktop",
):
    """
    Create a new folder inside an approved directory.
    """

    name = name.strip()

    if not name:
        return "Please provide a folder name, Sir."

    try:

        parent_path = safe_path(
            parent
        )

        if not parent_path.exists():
            return (
                f"The parent directory "
                f"'{parent_path}' does not exist, Sir."
            )

        folder = (
            parent_path / name
        ).resolve()

        # Make sure the resulting folder remains safe.
        safe_path(
            str(folder)
        )

        folder.mkdir(
            parents=False,
            exist_ok=False,
        )

        return (
            f"Created folder '{folder}', Sir."
        )

    except FileExistsError:

        return (
            f"The folder '{name}' already exists, Sir."
        )

    except Exception as error:

        return (
            f"I couldn't create that folder, Sir. "
            f"{error}"
        )


# =========================================================
# OPEN FILE OR FOLDER
# =========================================================

def open_path(
    path: str,
):
    """
    Open an approved file or folder using Windows.
    """

    try:

        target = safe_path(
            path
        )

    except Exception as error:

        return str(error)

    if not target.exists():

        return (
            f"I couldn't find '{target}', Sir."
        )

    try:

        os.startfile(
            target
        )

        return (
            f"Opened '{target}', Sir."
        )

    except Exception as error:

        return (
            f"I couldn't open '{target}', Sir. "
            f"{error}"
        )

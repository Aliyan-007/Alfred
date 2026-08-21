import ctypes
import os
import re
import subprocess
from pathlib import Path


# =========================================================
# CONFIGURATION
# =========================================================

# Directories we do NOT want to scan.
EXCLUDED_DIR_NAMES = {
    "$recycle.bin",
    "system volume information",
    "windows",
    "program files",
    "program files (x86)",
    "programdata",
    "appdata",
    "node_modules",
    ".git",
    ".venv",
    "__pycache__",
}

# Maximum number of results to return internally.
MAX_RESULTS = 15

# Avoid scanning endlessly large directory trees.
MAX_FILES_SCANNED = 500_000


# =========================================================
# WINDOWS DRIVE DISCOVERY
# =========================================================

def get_fixed_drives():
    """
    Return available fixed drives such as:
        C:\\
        D:\\
    """

    drives = []

    bitmask = ctypes.windll.kernel32.GetLogicalDrives()

    for i in range(26):

        if not (bitmask & (1 << i)):
            continue

        drive = f"{chr(65 + i)}:\\"

        drive_type = ctypes.windll.kernel32.GetDriveTypeW(
            drive
        )

        # DRIVE_FIXED = 3
        if drive_type == 3:
            drives.append(
                drive
            )

    return drives


# =========================================================
# NORMALIZATION
# =========================================================

def normalize(
    text: str,
) -> str:
    return re.sub(
        r"\s+",
        " ",
        text.lower().strip(),
    )


# =========================================================
# NAME MATCHING
# =========================================================

def score_file(
    path: Path,
    query: str,
):
    """
    Score a file against the user's query.

    Higher = better match.
    """

    query = normalize(
        query
    )

    name = normalize(
        path.name
    )

    stem = normalize(
        path.stem
    )

    score = 0

    if name == query:
        score += 100

    if stem == query:
        score += 95

    if query in name:
        score += 80

    if query in stem:
        score += 75

    query_words = [
        word
        for word in query.split()
        if len(word) >= 2
    ]

    for word in query_words:

        if word in name:
            score += 15

        if word in stem:
            score += 12

    # Prefer exact extension matches when supplied.
    if "." in query:

        if name == query:
            score += 50

    return score


# =========================================================
# DIRECTORY FILTER
# =========================================================

def should_skip_directory(
    name: str,
):
    return (
        name.lower()
        in EXCLUDED_DIR_NAMES
    )


# =========================================================
# SEARCH
# =========================================================

def find_files(
    query: str,
    max_results: int = MAX_RESULTS,
):
    """
    Search fixed Windows drives for files matching query.
    """

    query = query.strip()

    if not query:
        return []

    candidates = []

    scanned = 0

    drives = get_fixed_drives()

    print(
        f"[FILES] Searching drives: {drives}"
    )

    for drive in drives:

        for root, dirs, files in os.walk(
            drive,
            topdown=True,
            onerror=lambda error: None,
        ):

            # Filter directories in-place.
            dirs[:] = [
                directory
                for directory in dirs
                if not should_skip_directory(
                    directory
                )
            ]

            for filename in files:

                scanned += 1

                if (
                    scanned
                    > MAX_FILES_SCANNED
                ):
                    break

                try:

                    path = Path(
                        root
                    ) / filename

                    score = score_file(
                        path,
                        query,
                    )

                    if score > 0:

                        try:
                            modified = path.stat().st_mtime
                        except Exception:
                            modified = 0

                        candidates.append(
                            (
                                score,
                                modified,
                                path,
                            )
                        )

                except Exception:
                    continue

            if (
                scanned
                > MAX_FILES_SCANNED
            ):
                break

        if (
            scanned
            > MAX_FILES_SCANNED
        ):
            break

    # Highest score first, then newest.
    candidates.sort(
        key=lambda item: (
            item[0],
            item[1],
        ),
        reverse=True,
    )

    return [
        item[2]
        for item in candidates[
            :max_results
        ]
    ]


# =========================================================
# OPEN FILE
# =========================================================

def open_file(
    path: Path,
):
    """
    Open the file with its Windows default application.
    """

    if not path.exists():
        return (
            f"The file no longer exists: {path}"
        )

    if not path.is_file():
        return (
            f"That path is not a file: {path}"
        )

    try:

        os.startfile(
            str(path)
        )

        return (
            f"Opened '{path.name}'."
        )

    except Exception as error:

        return (
            f"I found '{path.name}', but Windows "
            f"couldn't open it: {error}"
        )


# =========================================================
# FIND + OPEN
# =========================================================

def find_and_open_file(
    query: str,
):
    """
    Find the best matching file and open it.

    Examples:
        resume
        invoice.pdf
        project.py
        report
    """

    query = query.strip()

    if not query:

        return (
            "What file should I find, Sir?"
        )

    print(
        f"[FILES] Looking for: {query}"
    )

    results = find_files(
        query
    )

    if not results:

        return (
            f"I couldn't find a file matching "
            f"'{query}', Sir."
        )

    # Best match.
    best = results[0]

    print(
        "[FILES] Best match:"
    )

    print(
        best
    )

    result = open_file(
        best
    )

    # Show a few alternatives if useful.
    if len(results) > 1:

        alternatives = "\n".join(
            str(path)
            for path in results[1:5]
        )

        return (
            f"{result}\n"
            f"Other matches:\n"
            f"{alternatives}"
        )

    return result

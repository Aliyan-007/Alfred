import ctypes
import os
import re
import shutil
import subprocess
from pathlib import Path

# =========================================================
# CONFIGURATION & EXCLUSIONS
# =========================================================

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

USER_HOME = Path.home()

STANDARD_DIRS = {
    "desktop": USER_HOME / "Desktop",
    "downloads": USER_HOME / "Downloads",
    "documents": USER_HOME / "Documents",
    "pictures": USER_HOME / "Pictures",
    "videos": USER_HOME / "Videos",
    "music": USER_HOME / "Music",
}

MAX_RESULTS = 10
MAX_FILES_SCANNED = 300_000


# =========================================================
# DRIVE DISCOVERY
# =========================================================

def get_fixed_drives():
    drives = []
    bitmask = ctypes.windll.kernel32.GetLogicalDrives()
    for i in range(26):
        if bitmask & (1 << i):
            drive = f"{chr(65 + i)}:\\"
            if ctypes.windll.kernel32.GetDriveTypeW(drive) == 3:  # DRIVE_FIXED
                drives.append(drive)
    return drives


# =========================================================
# UTILITIES & SCORING
# =========================================================

def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower().strip())


def score_file(path: Path, query: str) -> int:
    query = normalize(query)
    name = normalize(path.name)
    stem = normalize(path.stem)
    score = 0

    if name == query:
        score += 100
    elif stem == query:
        score += 95
    elif query in name:
        score += 80
    elif query in stem:
        score += 75

    query_words = [w for w in query.split() if len(w) >= 2]
    for word in query_words:
        if word in name:
            score += 15
        if word in stem:
            score += 12

    if "." in query and name.endswith(query.split(".")[-1]):
        score += 20

    return score


def should_skip_directory(name: str) -> bool:
    return name.lower() in EXCLUDED_DIR_NAMES


# =========================================================
# SEARCH & OPEN
# =========================================================

def find_files(query: str, max_results: int = MAX_RESULTS):
    query = query.strip()
    if not query:
        return []

    candidates = []
    scanned = 0
    drives = get_fixed_drives()

    for drive in drives:
        for root, dirs, files in os.walk(drive, topdown=True, onerror=lambda e: None):
            dirs[:] = [d for d in dirs if not should_skip_directory(d)]

            for filename in files:
                scanned += 1
                if scanned > MAX_FILES_SCANNED:
                    break

                try:
                    path = Path(root) / filename
                    score = score_file(path, query)
                    if score > 0:
                        try:
                            mtime = path.stat().st_mtime
                        except Exception:
                            mtime = 0
                        candidates.append((score, mtime, path))
                except Exception:
                    continue

            if scanned > MAX_FILES_SCANNED:
                break
        if scanned > MAX_FILES_SCANNED:
            break

    candidates.sort(key=lambda item: (item[0], item[1]), reverse=True)
    return [item[2] for item in candidates[:max_results]]


def open_file(path: Path) -> str:
    if not path.exists():
        return f"The file no longer exists: {path}"
    try:
        os.startfile(str(path))
        return f"Opened '{path.name}', Sir."
    except Exception as error:
        return f"I found '{path.name}', but Windows couldn't open it: {error}"


def find_and_open_file(query: str) -> str:
    query = query.strip()
    if not query:
        return "What file should I find, Sir?"

    results = find_files(query)
    if not results:
        return f"I couldn't find any file matching '{query}', Sir."

    best = results[0]
    result = open_file(best)

    if len(results) > 1:
        alts = "\n".join(f"- {p.name} ({p.parent})" for p in results[1:4])
        return f"{result}\nOther matches:\n{alts}"
    return result


# =========================================================
# FILE & DIRECTORY OPERATIONS
# =========================================================

def resolve_target_dir(location: str = "desktop") -> Path:
    loc = location.lower().strip()
    return STANDARD_DIRS.get(loc, STANDARD_DIRS["desktop"])


def create_folder(folder_name: str, location: str = "desktop") -> str:
    base_dir = resolve_target_dir(location)
    target = base_dir / folder_name.strip()
    try:
        target.mkdir(parents=True, exist_ok=True)
        return f"Created folder '{folder_name}' on your {location.capitalize()}, Sir."
    except Exception as error:
        return f"Failed to create folder '{folder_name}': {error}"


def create_file(file_name: str, location: str = "desktop", content: str = "") -> str:
    base_dir = resolve_target_dir(location)
    target = base_dir / file_name.strip()
    try:
        target.write_text(content, encoding="utf-8")
        return f"Created file '{file_name}' on your {location.capitalize()}, Sir."
    except Exception as error:
        return f"Failed to create file '{file_name}': {error}"


def delete_item(name_or_path: str) -> str:
    target = Path(name_or_path.strip())
    if not target.is_absolute():
        matches = find_files(name_or_path, max_results=1)
        if not matches:
            return f"I couldn't locate '{name_or_path}' to delete, Sir."
        target = matches[0]

    try:
        if target.is_file():
            target.unlink()
            return f"Deleted file '{target.name}', Sir."
        elif target.is_dir():
            shutil.rmtree(target)
            return f"Deleted directory '{target.name}', Sir."
        return f"Target not found: {target}"
    except Exception as error:
        return f"Failed to delete '{target.name}': {error}"


def rename_item(current_name: str, new_name: str) -> str:
    matches = find_files(current_name, max_results=1)
    if not matches:
        return f"I couldn't locate '{current_name}' to rename, Sir."

    target = matches[0]
    destination = target.parent / new_name.strip()
    try:
        target.rename(destination)
        return f"Renamed '{target.name}' to '{new_name}', Sir."
    except Exception as error:
        return f"Failed to rename '{target.name}': {error}"


# =========================================================
# SAFE FILE/FOLDER ACCESSOR HELPERS
# =========================================================

def _safe_user_path(raw_path: str) -> Path | None:
    if not raw_path or not raw_path.strip():
        return None

    candidate = Path(raw_path.strip()).expanduser()
    if not candidate.is_absolute():
        candidate = (Path.cwd() / candidate).resolve()
    else:
        candidate = candidate.resolve()

    user_home = Path.home().resolve()
    project_root = Path(__file__).resolve().parent.parent.resolve()

    if candidate == user_home or user_home in candidate.parents or candidate.is_relative_to(project_root):
        return candidate

    return None


def open_folder(folder_name: str) -> str:
    lookup = (folder_name or "").strip()
    if not lookup:
        return "Which folder should I open, Sir?"

    if lookup.lower() in STANDARD_DIRS:
        folder = STANDARD_DIRS[lookup.lower()]
    else:
        folder = _safe_user_path(lookup)

    if folder is None:
        return "I can only open folders inside your home folder or this project, Sir."

    try:
        if not folder.exists():
            return f"The folder '{folder}' does not exist, Sir."
        os.startfile(str(folder))
        return f"Opened '{folder}', Sir."
    except Exception as error:
        return f"I couldn't open '{folder}', Sir. {error}"


def search_files(query: str, max_results: int = MAX_RESULTS):
    return find_files(query, max_results=max_results)


def find_file_by_name(query: str, max_results: int = MAX_RESULTS):
    return search_files(query, max_results=max_results)


def copy_file(source: str, destination: str) -> str:
    src = _safe_user_path(source)
    dst = _safe_user_path(destination)

    if src is None or not src.exists() or src.is_dir():
        return f"I couldn't locate the source file '{source}', Sir."
    if dst is None:
        return "I can only copy files within your safe folders, Sir."

    try:
        target = dst / src.name if dst.is_dir() else dst
        shutil.copy2(src, target)
        return f"Copied '{src.name}' to '{target}', Sir."
    except Exception as error:
        return f"I couldn't copy the file, Sir. {error}"


def move_file(source: str, destination: str) -> str:
    src = _safe_user_path(source)
    dst = _safe_user_path(destination)

    if src is None or not src.exists() or src.is_dir():
        return f"I couldn't locate the source file '{source}', Sir."
    if dst is None:
        return "I can only move files within your safe folders, Sir."

    try:
        target = dst / src.name if dst.is_dir() else dst
        shutil.move(str(src), str(target))
        return f"Moved '{src.name}' to '{target}', Sir."
    except Exception as error:
        return f"I couldn't move the file, Sir. {error}"
import os
import re
import subprocess
from pathlib import Path

# =========================================================
# SHORTCUT SEARCH DIRECTORIES
# =========================================================

START_MENU_PATHS = [
    Path(os.environ.get("APPDATA", "")) / r"Microsoft\Windows\Start Menu\Programs",
    Path(os.environ.get("PROGRAMDATA", "")) / r"Microsoft\Windows\Start Menu\Programs",
    Path.home() / "Desktop",
    Path(os.environ.get("PUBLIC", "")) / "Desktop",
]

SYSTEM_APPS = {
    "notepad": "notepad.exe",
    "calculator": "calc.exe",
    "calc": "calc.exe",
    "file explorer": "explorer.exe",
    "explorer": "explorer.exe",
    "task manager": "taskmgr.exe",
    "taskmgr": "taskmgr.exe",
    "control panel": "control.exe",
    "settings": "ms-settings:",
    "command prompt": "cmd.exe",
    "cmd": "cmd.exe",
    "powershell": "powershell.exe",
    "terminal": "wt.exe",
    "paint": "mspaint.exe",
    "device manager": "devmgmt.msc",
}

STOP_WORDS = {"on", "in", "at", "to", "for", "the", "a", "an", "app", "browser", "pc", "windows", "my"}


# =========================================================
# APPLICATION INDEXER CLASS
# =========================================================

class AppIndexer:
    def __init__(self):
        self.app_index = {}
        self.build_index()

    def _clean_name(self, name: str) -> str:
        name = name.lower()
        name = re.sub(r"\.(lnk|exe|url)$", "", name)
        name = re.sub(r"[-_]", " ", name)
        name = re.sub(r"\s+", " ", name)
        return name.strip()

    def build_index(self):
        self.app_index.clear()

        # 1. Add Windows system utilities
        for name, cmd in SYSTEM_APPS.items():
            self.app_index[name] = cmd

        # 2. Add Start Menu and Desktop shortcuts
        for base_path in START_MENU_PATHS:
            if not base_path.exists():
                continue

            for root, _, files in os.walk(base_path):
                for file in files:
                    if file.lower().endswith((".lnk", ".url")):
                        clean = self._clean_name(file)
                        full_path = Path(root) / file
                        if any(w in clean for w in ["uninstall", "help", "documentation", "readme"]):
                            continue
                        self.app_index[clean] = str(full_path)

        print(f"[INDEXER] Indexed {len(self.app_index)} applications and tools.")

    def find_app(self, query: str):
        query = re.sub(r"[^\w\s]", "", query.lower()).strip()
        if not query:
            return None, None

        q_tokens = [w for w in query.split() if w not in STOP_WORDS]
        if not q_tokens:
            q_tokens = query.split()
        cleaned_query = " ".join(q_tokens)

        # 1. Exact match
        if cleaned_query in self.app_index:
            return self.app_index[cleaned_query], cleaned_query

        # 2. Word boundary match
        for name, target in self.app_index.items():
            if re.search(r"\b" + re.escape(cleaned_query) + r"\b", name):
                return target, name

        # 3. Meaningful token match
        best_match = None
        best_score = 0
        q_set = set(q_tokens)

        for name, target in self.app_index.items():
            n_tokens = [w for w in name.split() if w not in STOP_WORDS]
            n_set = set(n_tokens)
            overlap = q_set.intersection(n_set)

            if len(overlap) > best_score and len(overlap) >= len(q_set):
                best_score = len(overlap)
                best_match = (target, name)

        if best_match:
            return best_match

        return None, None

    def launch(self, query: str):
        target, matched_name = self.find_app(query)
        if not target:
            return False, None

        try:
            if target.startswith("ms-settings:"):
                subprocess.Popen(["cmd", "/c", "start", "", target], shell=False)
            else:
                os.startfile(target)
            return True, f"Opened {matched_name.capitalize()}, Sir."
        except Exception as error:
            return False, f"I found {matched_name}, but couldn't open it: {error}"


# Singleton instance
indexer = AppIndexer() 
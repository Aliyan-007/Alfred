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

# Standard Windows Built-ins
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


# =========================================================
# APPLICATION INDEXER
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
        """Scan Start Menu and Desktop shortcuts."""
        self.app_index.clear()

        # 1. Add System apps first
        for name, cmd in SYSTEM_APPS.items():
            self.app_index[name] = cmd

        # 2. Scan shortcut directories
        for base_path in START_MENU_PATHS:
            if not base_path.exists():
                continue

            for root, _, files in os.walk(base_path):
                for file in files:
                    if file.lower().endswith((".lnk", ".url")):
                        clean = self._clean_name(file)
                        full_path = Path(root) / file
                        # Ignore uninstallers or help links
                        if any(w in clean for w in ["uninstall", "help", "documentation", "readme"]):
                            continue
                        self.app_index[clean] = str(full_path)

        print(f"[INDEXER] Indexed {len(self.app_index)} applications and tools.")

    def find_app(self, query: str):
        query = query.lower().strip()

        # 1. Exact match
        if query in self.app_index:
            return self.app_index[query], query

        # 2. Substring match
        for name, target in self.app_index.items():
            if query == name or query in name:
                return target, name

        # 3. Token match
        q_words = set(query.split())
        best_match = None
        best_score = 0
        for name, target in self.app_index.items():
            n_words = set(name.split())
            overlap = len(q_words.intersection(n_words))
            if overlap > best_score:
                best_score = overlap
                best_match = (target, name)

        if best_match and best_score >= 1:
            return best_match

        return None, None

    def launch(self, query: str) -> str:
        target, matched_name = self.find_app(query)
        if not target:
            return f"I couldn't find an installed application matching '{query}', Sir."

        try:
            if target.startswith("ms-settings:"):
                subprocess.Popen(["cmd", "/c", "start", "", target], shell=False)
            else:
                os.startfile(target)
            return f"Opened {matched_name.capitalize()}, Sir."
        except Exception as error:
            return f"I found {matched_name}, but couldn't open it: {error}"


# Singleton instance
indexer = AppIndexer()
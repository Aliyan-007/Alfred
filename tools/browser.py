import json
import subprocess
import time
from pathlib import Path
from urllib.parse import quote_plus

import requests
import websocket

# =========================================================
# CONFIGURATION
# =========================================================

BRAVE_PATH = r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe"
PROFILE_PATH = Path("D:/ALFRED_SLM/browser")
CDP_BASE = "http://127.0.0.1:9222"
CDP_TIMEOUT = 10

_brave_process = None


# =========================================================
# PROCESS & CDP STATUS
# =========================================================

def cdp_ready() -> bool:
    try:
        res = requests.get(f"{CDP_BASE}/json/version", timeout=2)
        return res.status_code == 200
    except Exception:
        return False


def start_brave() -> bool:
    global _brave_process
    if cdp_ready():
        return True

    PROFILE_PATH.mkdir(parents=True, exist_ok=True)
    try:
        _brave_process = subprocess.Popen(
            [
                BRAVE_PATH,
                f"--user-data-dir={PROFILE_PATH}",
                "--remote-debugging-port=9222",
                f"--remote-allow-origins={CDP_BASE}",
                "--no-first-run",
                "--no-default-browser-check",
                "--new-window",
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except Exception as error:
        print(f"[BRAVE] Failed to start Brave: {error}")
        return False

    for _ in range(30):
        time.sleep(0.5)
        if cdp_ready():
            return True
        if _brave_process and _brave_process.poll() is not None:
            break
    return False


def ensure_brave() -> bool:
    return cdp_ready() or start_brave()


# =========================================================
# TAB MANAGEMENT
# =========================================================

def get_pages():
    if not ensure_brave():
        raise RuntimeError("Brave browser is not accessible.")
    res = requests.get(f"{CDP_BASE}/json/list", timeout=5)
    res.raise_for_status()
    return res.json()


def find_page(url_contains: str):
    pages = get_pages()
    target = url_contains.lower()
    for page in pages:
        if page.get("type") == "page" and target in page.get("url", "").lower():
            return page
    return None


def get_active_page():
    pages = [p for p in get_pages() if p.get("type") == "page"]
    return pages[0] if pages else None


def connect_page(page):
    ws_url = page.get("webSocketDebuggerUrl")
    if not ws_url:
        raise RuntimeError("No WebSocket debugger URL available for this page.")
    return websocket.create_connection(ws_url, timeout=CDP_TIMEOUT, origin=CDP_BASE)


def cdp_command(ws, command_id: int, method: str, params: dict = None):
    payload = {"id": command_id, "method": method}
    if params:
        payload["params"] = params
    ws.send(json.dumps(payload))
    while True:
        response = json.loads(ws.recv())
        if response.get("id") == command_id:
            if "error" in response:
                raise RuntimeError(response["error"])
            return response


# =========================================================
# NAVIGATION & CONTROL
# =========================================================

def navigate(page, url: str):
    ws = None
    try:
        ws = connect_page(page)
        cdp_command(ws, 1, "Page.enable")
        return cdp_command(ws, 2, "Page.navigate", {"url": url})
    finally:
        if ws:
            ws.close()


def bring_to_front(page):
    ws = None
    try:
        ws = connect_page(page)
        return cdp_command(ws, 1, "Page.bringToFront")
    finally:
        if ws:
            ws.close()


def evaluate(page, expression: str, args=None):
    ws = None
    try:
        ws = connect_page(page)
        cdp_command(ws, 1, "Runtime.enable")

        expr = expression.strip()
        is_fn = any(expr.startswith(prefix) for prefix in ["function", "async function", "(", "async ("])

        if is_fn:
            args_json = json.dumps(args if args is not None else [])
            wrapped = f"(() => {{ const fn = ({expr}); const args = {args_json}; return fn(...args); }})()"
        else:
            wrapped = expr

        result = cdp_command(ws, 2, "Runtime.evaluate", {
            "expression": wrapped,
            "returnByValue": True,
            "awaitPromise": True,
        })

        root = result.get("result", {})
        if "exceptionDetails" in root:
            desc = root["exceptionDetails"].get("exception", {}).get("description", "Evaluation failed.")
            raise RuntimeError(desc)
        return root.get("result", {}).get("value")
    finally:
        if ws:
            ws.close()


def new_tab(url: str = "https://www.google.com") -> str:
    if not ensure_brave():
        return "I couldn't launch Brave, Sir."
    try:
        res = requests.put(f"{CDP_BASE}/json/new?{quote_plus(url, safe=':/?=')}", timeout=5)
        res.raise_for_status()
        return "Opened a new tab, Sir."
    except Exception as error:
        return f"Couldn't open a new tab: {error}"


def close_active_tab() -> str:
    page = get_active_page()
    if not page:
        return "There are no browser tabs to close, Sir."
    try:
        res = requests.get(f"{CDP_BASE}/json/close/{page['id']}", timeout=5)
        res.raise_for_status()
        return "Closed the current tab, Sir."
    except Exception as error:
        return f"Failed to close tab: {error}"


def browser_search(query: str, engine: str = "google") -> str:
    if not ensure_brave():
        return "Browser is unavailable, Sir."

    if engine.lower() == "youtube":
        url = f"https://www.youtube.com/results?search_query={quote_plus(query)}"
        svc = "YouTube"
    else:
        url = f"https://www.google.com/search?q={quote_plus(query)}"
        svc = "Google"

    page = get_active_page()
    if page:
        navigate(page, url)
        bring_to_front(page)
    else:
        new_tab(url)

    return f"Searching {svc} for '{query}', Sir."


def open_url(url: str) -> str:
    if not url.startswith("http://") and not url.startswith("https://"):
        url = "https://" + url

    if not ensure_brave():
        return "Browser is unavailable, Sir."

    page = get_active_page()
    if page:
        navigate(page, url)
        bring_to_front(page)
    else:
        new_tab(url)

    return f"Navigating to {url}, Sir."


def browser_action(action: str) -> str:
    page = get_active_page()
    if not page:
        return "No active browser tab found, Sir."

    actions = {
        "refresh": "window.location.reload()",
        "back": "window.history.back()",
        "forward": "window.history.forward()",
    }
    script = actions.get(action.lower().strip())
    if not script:
        return f"Unsupported browser action: {action}"

    try:
        evaluate(page, script)
        return f"Browser {action} executed, Sir."
    except Exception as error:
        return f"Couldn't perform {action}: {error}"
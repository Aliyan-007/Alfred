import json
import os
import re
import subprocess
import time
import webbrowser
from pathlib import Path
from urllib.parse import quote_plus

import requests
import websocket


# =========================================================
# BRAVE PATH AUTO-DETECTION
# =========================================================

POSSIBLE_BRAVE_PATHS = [
    Path(r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe"),
    Path(r"C:\Program Files (x86)\BraveSoftware\Brave-Browser\Application\brave.exe"),
    Path(os.environ.get("LOCALAPPDATA", ""))
    / r"BraveSoftware\Brave-Browser\Application\brave.exe",
]

BRAVE_PATH = next(
    (str(path) for path in POSSIBLE_BRAVE_PATHS if path.exists()),
    None,
)

PROFILE_PATH = Path(r"D:\ALFRED_SLM\browser")
CDP_BASE = "http://127.0.0.1:9222"
CDP_TIMEOUT = 5

_brave_process = None


# =========================================================
# WEB SERVICE DIRECTORY
# =========================================================

KNOWN_WEB_SERVICES = {
    "youtube": "https://www.youtube.com",
    "spotify": "https://open.spotify.com",
    "gmail": "https://mail.google.com",
    "google": "https://www.google.com",
    "chatgpt": "https://chatgpt.com",
    "github": "https://github.com",
    "whatsapp": "https://web.whatsapp.com",
    "reddit": "https://www.reddit.com",
    "twitter": "https://x.com",
    "x": "https://x.com",
    "netflix": "https://www.netflix.com",
    "instagram": "https://www.instagram.com",
    "facebook": "https://www.facebook.com",
    "linkedin": "https://www.linkedin.com",
    "maps": "https://maps.google.com",
    "google drive": "https://drive.google.com",
    "drive": "https://drive.google.com",
}


# =========================================================
# CDP STATUS & LAUNCH
# =========================================================

def _clear_cdp_port_conflicts(port: int = 9222) -> None:
    """Release stale listeners that are holding the CDP port without serving DevTools."""
    try:
        result = subprocess.run(
            [
                "powershell",
                "-NoProfile",
                "-Command",
                "Get-NetTCPConnection -LocalPort "
                f"{port} -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess",
            ],
            capture_output=True,
            text=True,
            check=False,
        )

        pids = []
        for value in (result.stdout or "").splitlines():
            cleaned = str(value).strip()
            if cleaned and cleaned.isdigit():
                pids.append(cleaned)

        for pid in sorted(set(pids), key=int):
            try:
                proc = subprocess.run(
                    ["powershell", "-NoProfile", "-Command",
                     f"(Get-Process -Id {pid} -ErrorAction SilentlyContinue | Select-Object -ExpandProperty ProcessName)"],
                    capture_output=True,
                    text=True,
                    check=False,
                )
                name = (proc.stdout or "").strip().lower()
                if not name or name not in {"brave", "chrome", "msedge", "chromium"}:
                    continue
                subprocess.run(["taskkill", "/PID", str(pid), "/F"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
                print(f"[BRAVE] Cleared stale CDP listener on port {port} (PID {pid}).")
            except Exception:
                continue

    except Exception:
        pass


def cdp_ready() -> bool:
    """Return True when Brave's Chrome DevTools Protocol is available."""
    try:
        response = requests.get(
            f"{CDP_BASE}/json/version",
            timeout=1.5,
        )
        return response.status_code == 200 and "Browser" in response.text
    except Exception:
        return False


def start_brave() -> bool:
    """Start Brave with a dedicated ALFRED browser profile using a clean CDP port."""
    global _brave_process

    if cdp_ready():
        return True

    if not BRAVE_PATH:
        print("[BRAVE] Brave executable not found in standard paths.")
        return False

    _clear_cdp_port_conflicts()

    PROFILE_PATH.mkdir(parents=True, exist_ok=True)

    try:
        _brave_process = subprocess.Popen(
            [
                BRAVE_PATH,
                f"--user-data-dir={PROFILE_PATH}",
                "--remote-debugging-address=127.0.0.1",
                "--remote-debugging-port=9222",
                "--remote-allow-origins=http://127.0.0.1:9222",
                "--new-window",
                "about:blank",
                "--no-first-run",
                "--no-default-browser-check",
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0),
        )
    except Exception as error:
        print(f"[BRAVE] Failed to start Brave: {error}")
        return False

    for _ in range(40):
        time.sleep(0.5)

        if cdp_ready():
            return True

        if _brave_process and _brave_process.poll() is not None:
            break

    print("[BRAVE] CDP did not become available on http://127.0.0.1:9222.")
    return False


def ensure_brave() -> bool:
    """Ensure Brave is running with CDP enabled, or confirm a browser fallback is available."""
    if cdp_ready():
        return True
    if start_brave():
        return True
    try:
        import webbrowser
        return webbrowser.get() is not None
    except Exception:
        return False


# =========================================================
# CDP HELPERS
# =========================================================

def get_pages():
    """Return all currently open CDP pages."""
    if not ensure_brave():
        return []

    try:
        response = requests.get(
            f"{CDP_BASE}/json/list",
            timeout=3,
        )
        response.raise_for_status()
        return response.json()
    except Exception:
        return []


def find_page(url_contains: str):
    """Find the first browser page whose URL contains the supplied text."""
    pages = get_pages()
    target = url_contains.lower().strip()

    for page in pages:
        if page.get("type") != "page":
            continue

        page_url = page.get("url", "").lower()

        if target and target in page_url:
            return page

    return None


def get_active_page():
    """
    Return a usable browser page.

    CDP's /json/list endpoint does not expose a guaranteed 'active tab'
    property, so we prefer the most recently listed normal page.
    """
    pages = [
        page
        for page in get_pages()
        if page.get("type") == "page"
    ]

    if not pages:
        return None

    return pages[0]


def connect_page(page):
    """Open a WebSocket connection to a CDP page."""
    websocket_url = page.get("webSocketDebuggerUrl")

    if not websocket_url:
        raise RuntimeError("No WebSocket debugger URL available.")

    return websocket.create_connection(
        websocket_url,
        timeout=CDP_TIMEOUT,
        origin=CDP_BASE,
    )


def cdp_command(
    ws,
    command_id: int,
    method: str,
    params: dict | None = None,
):
    """Send a CDP command and wait for its matching response."""
    payload = {
        "id": command_id,
        "method": method,
    }

    if params:
        payload["params"] = params

    ws.send(json.dumps(payload))

    while True:
        response = json.loads(ws.recv())

        if response.get("id") != command_id:
            continue

        if "error" in response:
            raise RuntimeError(response["error"])

        return response


def navigate(page, url: str):
    """Navigate an existing browser page to a URL."""
    ws = None

    try:
        ws = connect_page(page)

        cdp_command(
            ws,
            1,
            "Page.enable",
        )

        return cdp_command(
            ws,
            2,
            "Page.navigate",
            {"url": url},
        )

    finally:
        if ws:
            ws.close()


def bring_to_front(page):
    """Bring a browser page to the foreground."""
    ws = None

    try:
        ws = connect_page(page)

        return cdp_command(
            ws,
            1,
            "Page.bringToFront",
        )

    finally:
        if ws:
            ws.close()


def evaluate(
    page,
    expression: str,
    args=None,
):
    """
    Evaluate JavaScript in a browser page.

    If expression is a function, args are passed to that function.
    Otherwise expression is executed directly.
    """
    ws = None

    try:
        ws = connect_page(page)

        cdp_command(
            ws,
            1,
            "Runtime.enable",
        )

        expr = expression.strip()

        is_function = (
            expr.startswith("function")
            or expr.startswith("async function")
            or expr.startswith("(")
            or expr.startswith("async (")
        )

        if is_function:
            args_json = json.dumps(
                args if args is not None else []
            )

            wrapped = (
                "(() => { "
                f"const fn = ({expr}); "
                f"const args = {args_json}; "
                "return fn(...args); "
                "})()"
            )
        else:
            wrapped = expr

        result = cdp_command(
            ws,
            2,
            "Runtime.evaluate",
            {
                "expression": wrapped,
                "returnByValue": True,
                "awaitPromise": True,
            },
        )

        root = result.get("result", {})

        if "exceptionDetails" in root:
            exception = root["exceptionDetails"].get(
                "exception",
                {},
            )

            description = exception.get(
                "description",
                "Evaluation failed.",
            )

            raise RuntimeError(description)

        return root.get("result", {}).get("value")

    finally:
        if ws:
            ws.close()


def press_key(page, key: str):
    """Send a keyboard key through CDP."""
    ws = None

    try:
        ws = connect_page(page)

        key_map = {
            "f": {
                "key": "f",
                "code": "KeyF",
                "text": "f",
                "windowsVirtualKeyCode": 70,
            },
            "k": {
                "key": "k",
                "code": "KeyK",
                "text": "k",
                "windowsVirtualKeyCode": 75,
            },
            "Escape": {
                "key": "Escape",
                "code": "Escape",
                "windowsVirtualKeyCode": 27,
            },
            "Space": {
                "key": " ",
                "code": "Space",
                "text": " ",
                "windowsVirtualKeyCode": 32,
            },
        }

        info = key_map.get(
            key,
            {
                "key": key,
                "code": key,
            },
        )

        cdp_command(
            ws,
            1,
            "Input.dispatchKeyEvent",
            {
                "type": "keyDown",
                **info,
            },
        )

        cdp_command(
            ws,
            2,
            "Input.dispatchKeyEvent",
            {
                "type": "keyUp",
                **info,
            },
        )

        return True

    finally:
        if ws:
            ws.close()


def get_page_text(page):
    """Extract visible text from a page."""
    return evaluate(
        page,
        """
        (() => {
            if (!document.body) {
                return "";
            }

            const clone = document.body.cloneNode(true);

            clone
                .querySelectorAll("script, style, noscript, svg")
                .forEach(el => el.remove());

            return (clone.innerText || "").trim();
        })()
        """,
    )


# =========================================================
# WEB DESTINATION HANDLER
# =========================================================

def _clean_destination(value: str) -> str:
    """Clean a voice-derived browser destination without damaging URLs."""
    value = str(value or "").strip()

    # Remove common Markdown URL formatting accidentally introduced
    # by copied assistant output.
    value = value.replace("[", "").replace("]", "")

    # Remove surrounding parentheses only when they wrap the whole value.
    if value.startswith("(") and value.endswith(")"):
        value = value[1:-1].strip()

    return value


def open_web_destination(destination_or_url: str) -> str:
    """
    Open a known web service, URL, domain, or Google search.

    Brave/CDP is preferred. The system browser is used as fallback.
    """
    raw_destination = _clean_destination(destination_or_url)

    if not raw_destination:
        return "No web destination was provided, Sir."

    dest = raw_destination.lower().strip()

    # -----------------------------------------------------
    # 1. Known service
    # -----------------------------------------------------

    if dest in KNOWN_WEB_SERVICES:
        url = KNOWN_WEB_SERVICES[dest]
        service_name = dest.title()

    # -----------------------------------------------------
    # 2. Direct URL
    # -----------------------------------------------------

    elif re.match(
        r"^https?://",
        raw_destination,
        re.IGNORECASE,
    ):
        url = raw_destination
        service_name = raw_destination

    # -----------------------------------------------------
    # 3. Plain domain
    # -----------------------------------------------------

    elif (
        "." in raw_destination
        and " " not in raw_destination
        and not raw_destination.startswith(".")
    ):
        url = f"https://{raw_destination}"
        service_name = raw_destination

    # -----------------------------------------------------
    # 4. Search
    # -----------------------------------------------------

    else:
        url = (
            "https://www.google.com/search?q="
            + quote_plus(raw_destination)
        )
        service_name = f"Google Search for '{raw_destination}'"

    # -----------------------------------------------------
    # Attempt Brave/CDP first
    # -----------------------------------------------------

    if ensure_brave():
        try:
            page = find_page(dest) or get_active_page()

            if page:
                navigate(page, url)
                bring_to_front(page)
            else:
                response = requests.put(
                    f"{CDP_BASE}/json/new",
                    params={"url": url},
                    timeout=5,
                )

                response.raise_for_status()

            return f"Opened {service_name}, Sir."

        except Exception as error:
            print(f"[BRAVE] CDP navigation failed: {error}")

    # -----------------------------------------------------
    # Fallback to system browser
    # -----------------------------------------------------

    try:
        opened = webbrowser.open(url)

        if opened:
            return f"Opened {service_name}, Sir."

        return f"Could not open {service_name}, Sir."

    except Exception as error:
        return f"Failed to open {service_name}: {error}"


def new_tab(
    url: str = "https://www.google.com",
) -> str:
    """Open a destination in the browser."""
    return open_web_destination(url)


def close_active_tab() -> str:
    """Close the currently selected CDP page."""
    page = get_active_page()

    if not page:
        return "There are no active browser tabs to close, Sir."

    page_id = page.get("id")

    if not page_id:
        return "The active browser tab has no valid ID, Sir."

    try:
        response = requests.get(
            f"{CDP_BASE}/json/close/{page_id}",
            timeout=3,
        )
        response.raise_for_status()

        return "Closed the current tab, Sir."

    except Exception as error:
        return f"Failed to close tab: {error}"


def browser_search(
    query: str,
    engine: str = "google",
) -> str:
    """Search Google, YouTube, Wikipedia, images, or news from ALFRED."""
    query = str(query or "").strip()

    if not query:
        return "No search query was provided, Sir."

    engine = engine.lower().strip()

    if engine in {"youtube", "yt"}:
        url = "https://www.youtube.com/results?search_query=" + quote_plus(query)
        service = "YouTube"
    elif engine in {"wikipedia", "wiki"}:
        url = "https://en.wikipedia.org/wiki/Special:Search?search=" + quote_plus(query)
        service = "Wikipedia"
    elif engine in {"images", "image", "img"}:
        url = "https://www.google.com/search?q=" + quote_plus(query) + "&tbm=isch"
        service = "Google Images"
    elif engine in {"news", "newspaper"}:
        url = "https://news.google.com/search?q=" + quote_plus(query)
        service = "Google News"
    else:
        url = "https://www.google.com/search?q=" + quote_plus(query)
        service = "Google"

    result = open_web_destination(url)

    if result.startswith("Opened"):
        return f"Opened {service} search, Sir."

    return result


def browser_history() -> str:
    """Return a concise list of open browser pages and their URLs."""
    pages = get_pages()
    if not pages:
        return "There are no open browser pages, Sir."

    lines = []
    for index, page in enumerate(pages[:8], start=1):
        url = page.get("url", "about:blank")
        lines.append(f"{index}. {url}")
    return "\n".join(lines)


def next_tab() -> str:
    """Switch to the next Chrome/Brave tab using the CDP page list."""
    pages = [page for page in get_pages() if page.get("type") == "page"]
    if len(pages) < 2:
        return "There are no other tabs to switch to, Sir."
    active = get_active_page()
    active_id = active.get("id") if active else None
    current_index = 0
    for idx, page in enumerate(pages):
        if page.get("id") == active_id:
            current_index = idx
            break
    target = pages[(current_index + 1) % len(pages)]
    try:
        bring_to_front(target)
        return "Switched to the next tab, Sir."
    except Exception as error:
        return f"I couldn't switch to the next tab, Sir. {error}"


def previous_tab() -> str:
    """Switch to the previous Chrome/Brave tab using the CDP page list."""
    pages = [page for page in get_pages() if page.get("type") == "page"]
    if len(pages) < 2:
        return "There are no previous tabs to switch to, Sir."
    active = get_active_page()
    active_id = active.get("id") if active else None
    current_index = 0
    for idx, page in enumerate(pages):
        if page.get("id") == active_id:
            current_index = idx
            break
    target = pages[(current_index - 1) % len(pages)]
    try:
        bring_to_front(target)
        return "Switched to the previous tab, Sir."
    except Exception as error:
        return f"I couldn't switch to the previous tab, Sir. {error}"


def browser_action(action: str) -> str:
    """Perform a basic action on the active browser page."""
    page = get_active_page()

    if not page:
        return "No active browser tab found, Sir."

    action = str(action or "").strip().lower()

    actions = {
        "refresh": "window.location.reload()",
        "back": "window.history.back()",
        "forward": "window.history.forward()",
    }

    script = actions.get(action)

    if not script:
        return f"Unsupported browser action: {action}"

    try:
        evaluate(page, script)
        return f"Browser {action} executed, Sir."

    except Exception as error:
        return f"Couldn't perform {action}: {error}"

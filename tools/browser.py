import json
import subprocess
import time
from pathlib import Path

import requests
import websocket


# =========================================================
# CONFIGURATION
# =========================================================

BRAVE_PATH = (
    r"C:\Program Files\BraveSoftware\Brave-Browser"
    r"\Application\brave.exe"
)

PROFILE_PATH = (
    Path("D:/ALFRED_SLM/browser")
)

CDP_BASE = (
    "http://127.0.0.1:9222"
)

CDP_TIMEOUT = 15


# =========================================================
# BRAVE PROCESS
# =========================================================

_brave_process = None


# =========================================================
# CDP STATUS
# =========================================================

def cdp_ready():
    """
    Check whether the dedicated ALFRED Brave instance
    is exposing the classic CDP endpoint.
    """

    try:

        response = requests.get(
            f"{CDP_BASE}/json/version",
            timeout=2,
        )

        return response.status_code == 200

    except Exception:

        return False


# =========================================================
# START BRAVE
# =========================================================

def start_brave():
    """
    Start the dedicated ALFRED Brave profile.
    """

    global _brave_process

    if cdp_ready():
        return True

    PROFILE_PATH.mkdir(
        parents=True,
        exist_ok=True,
    )

    try:

        _brave_process = subprocess.Popen(
            [
                BRAVE_PATH,

                f"--user-data-dir={PROFILE_PATH}",

                "--remote-debugging-port=9222",

                "--remote-allow-origins=http://127.0.0.1:9222",

                "--no-first-run",

                "--no-default-browser-check",

                "--new-window",
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

    except Exception as error:

        print(
            f"[BRAVE] Failed to start Brave: {error}"
        )

        return False

    # -----------------------------------------------------
    # Wait for CDP
    # -----------------------------------------------------

    for _ in range(30):

        time.sleep(0.5)

        if cdp_ready():
            return True

        if (
            _brave_process is not None
            and _brave_process.poll() is not None
        ):
            break

    return False


# =========================================================
# ENSURE BRAVE
# =========================================================

def ensure_brave():
    """
    Ensure the dedicated ALFRED Brave instance is available.
    """

    if cdp_ready():
        return True

    return start_brave()


# =========================================================
# LIST PAGES
# =========================================================

def get_pages():
    """
    Get all tabs/pages from Brave.
    """

    if not ensure_brave():

        raise RuntimeError(
            "ALFRED Brave is not available."
        )

    response = requests.get(
        f"{CDP_BASE}/json/list",
        timeout=5,
    )

    response.raise_for_status()

    return response.json()


# =========================================================
# FIND PAGE
# =========================================================

def find_page(
    url_contains: str,
):
    """
    Find an open browser tab whose URL contains
    the supplied string.
    """

    pages = get_pages()

    target = url_contains.lower()

    for page in pages:

        if page.get("type") != "page":
            continue

        url = page.get(
            "url",
            "",
        )

        if target in url.lower():

            return page

    return None


# =========================================================
# CONNECT PAGE
# =========================================================

def connect_page(
    page,
):
    websocket_url = page.get(
        "webSocketDebuggerUrl"
    )

    if not websocket_url:

        raise RuntimeError(
            "Brave did not provide a WebSocket debugger URL."
        )

    return websocket.create_connection(
        websocket_url,
        timeout=CDP_TIMEOUT,
        origin=CDP_BASE,
    )


# =========================================================
# CDP COMMAND
# =========================================================

def cdp_command(
    ws,
    command_id,
    method,
    params=None,
):
    payload = {
        "id": command_id,
        "method": method,
    }

    if params is not None:
        payload["params"] = params

    ws.send(
        json.dumps(
            payload
        )
    )

    while True:

        response = json.loads(
            ws.recv()
        )

        if response.get("id") == command_id:

            if "error" in response:

                raise RuntimeError(
                    response["error"]
                )

            return response


# =========================================================
# PAGE NAVIGATION
# =========================================================

def navigate(
    page,
    url: str,
):
    ws = None

    try:

        ws = connect_page(
            page
        )

        cdp_command(
            ws,
            1,
            "Page.enable",
        )

        result = cdp_command(
            ws,
            2,
            "Page.navigate",
            {
                "url": url,
            },
        )

        return result

    finally:

        if ws is not None:

            try:
                ws.close()
            except Exception:
                pass


# =========================================================
# BRING PAGE TO FRONT
# =========================================================

def bring_to_front(
    page,
):
    ws = None

    try:

        ws = connect_page(
            page
        )

        return cdp_command(
            ws,
            1,
            "Page.bringToFront",
        )

    finally:

        if ws is not None:

            try:
                ws.close()
            except Exception:
                pass


# =========================================================
# EVALUATE JAVASCRIPT
# =========================================================
def evaluate(
    page,
    expression: str,
    args=None,
):
    """
    Execute JavaScript in a page using CDP.

    Supports:
      function() { ... }
      function(query) { ... }
      (query) => { ... }
      () => { ... }

    Optional Python arguments are passed to the function.
    """

    import json

    ws = None

    try:

        ws = connect_page(
            page
        )

        cdp_command(
            ws,
            1,
            "Runtime.enable",
        )

        expression = expression.strip()

        # -------------------------------------------------
        # Decide whether the supplied expression is a
        # function expression.
        # -------------------------------------------------

        is_function_expression = (
            expression.startswith(
                "function"
            )
            or expression.startswith(
                "async function"
            )
            or expression.startswith(
                "("
            )
            or expression.startswith(
                "async ("
            )
        )

        # -------------------------------------------------
        # Function expression
        # -------------------------------------------------

        if is_function_expression:

            function_source = (
                f"({expression})"
            )

            serialized_args = json.dumps(
                args if args is not None else []
            )

            wrapped_expression = f"""
            (() => {{
                const fn = {function_source};
                const args = {serialized_args};
                return fn(...args);
            }})()
            """

        # -------------------------------------------------
        # Plain JavaScript expression
        # -------------------------------------------------

        else:

            wrapped_expression = expression

        result = cdp_command(
            ws,
            2,
            "Runtime.evaluate",
            {
                "expression": wrapped_expression,
                "returnByValue": True,
                "awaitPromise": True,
            },
        )

        # -------------------------------------------------
        # CDP exception
        # -------------------------------------------------

        result_root = result.get(
            "result",
            {},
        )

        if (
            "exceptionDetails"
            in result_root
        ):

            exception = result_root[
                "exceptionDetails"
            ]

            description = (
                exception.get(
                    "exception",
                    {},
                )
                .get(
                    "description"
                )
            )

            if not description:

                description = str(
                    exception
                )

            raise RuntimeError(
                description
            )

        # -------------------------------------------------
        # Extract returned value
        # -------------------------------------------------

        inner = result_root.get(
            "result",
            {},
        )

        return inner.get(
            "value"
        )

    finally:

        if ws is not None:

            try:
                ws.close()
            except Exception:
                pass

# =========================================================
# TAKE SNAPSHOT
# =========================================================

def get_page_text(
    page,
):
    """
    Extract visible page text.
    """

    return evaluate(
        page,
        """
        (() => {
            const clone =
                document.body.cloneNode(true);

            clone.querySelectorAll(
                "script, style, noscript, svg"
            ).forEach(
                element => element.remove()
            );

            return (
                clone.innerText || ""
            ).trim();
        })()
        """,
    )

def press_key(
    page,
    key: str,
):
    """
    Send a keyboard key through the Chrome DevTools Protocol.
    """

    ws = None

    try:

        ws = connect_page(
            page
        )

        key_map = {
            "f": {
                "key": "f",
                "code": "KeyF",
                "text": "f",
                "windowsVirtualKeyCode": 70,
            },
            "Escape": {
                "key": "Escape",
                "code": "Escape",
                "windowsVirtualKeyCode": 27,
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

        if ws is not None:

            try:
                ws.close()
            except Exception:
                pass
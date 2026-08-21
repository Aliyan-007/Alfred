import json
import time

import requests
import websocket


CDP_BASE = "http://127.0.0.1:9222"
CDP_TIMEOUT = 10


# =========================================================
# CDP COMMAND
# =========================================================

def cdp_command(
    ws,
    command_id,
    method,
    params=None,
):
    message = {
        "id": command_id,
        "method": method,
    }

    if params is not None:
        message["params"] = params

    ws.send(
        json.dumps(message)
    )

    while True:

        response = json.loads(
            ws.recv()
        )

        if response.get("id") == command_id:
            return response


# =========================================================
# CREATE TAB
# =========================================================

def create_tab():

    response = requests.put(
        f"{CDP_BASE}/json/new",
        timeout=5,
    )

    response.raise_for_status()

    return response.json()


# =========================================================
# OPEN WEBPAGE
# =========================================================

def open_webpage(
    url: str,
    max_chars: int = 12000,
):
    """
    Open a webpage in the existing Brave browser,
    extract readable text, and return it to ALFRED.
    """

    url = url.strip()

    if not url:
        return "No webpage URL was provided, Sir."

    if not (
        url.startswith("http://")
        or url.startswith("https://")
    ):
        url = "https://" + url

    ws = None

    try:

        print(
            f"[WEBPAGE] Opening {url}"
        )

        # -------------------------------------------------
        # Create a new tab in the existing Brave instance.
        # -------------------------------------------------

        page = create_tab()

        websocket_url = page.get(
            "webSocketDebuggerUrl"
        )

        if not websocket_url:

            return (
                "Brave did not provide a webpage "
                "connection, Sir."
            )

        # -------------------------------------------------
        # Connect to tab.
        # -------------------------------------------------

        ws = websocket.create_connection(
            websocket_url,
            timeout=CDP_TIMEOUT,
            origin=CDP_BASE,
        )

        cdp_command(
            ws,
            1,
            "Runtime.enable",
        )

        cdp_command(
            ws,
            2,
            "Page.enable",
        )

        # -------------------------------------------------
        # Navigate.
        # -------------------------------------------------

        cdp_command(
            ws,
            3,
            "Page.navigate",
            {
                "url": url,
            },
        )

        # -------------------------------------------------
        # Wait for page load.
        # -------------------------------------------------

        deadline = time.time() + 15

        while time.time() < deadline:

            try:

                state = cdp_command(
                    ws,
                    10,
                    "Runtime.evaluate",
                    {
                        "expression": (
                            "document.readyState"
                        ),
                        "returnByValue": True,
                    },
                )

                ready_state = (
                    state
                    .get("result", {})
                    .get("result", {})
                    .get("value")
                )

                if ready_state in {
                    "interactive",
                    "complete",
                }:
                    break

            except Exception:
                pass

            time.sleep(1)

        # Give JavaScript pages a little extra time.
        time.sleep(2)

        # -------------------------------------------------
        # Extract visible page text.
        # -------------------------------------------------

        result = cdp_command(
            ws,
            20,
            "Runtime.evaluate",
            {
                "expression": """
                (() => {

                    const clone =
                        document.body.cloneNode(true);

                    clone.querySelectorAll(
                        "script, style, noscript, svg"
                    ).forEach(
                        element => element.remove()
                    );

                    return {
                        title:
                            document.title || "",

                        url:
                            location.href || "",

                        text:
                            (
                                clone.innerText || ""
                            )
                            .replace(
                                /\\n{3,}/g,
                                "\\n\\n"
                            )
                            .trim()
                    };

                })()
                """,
                "returnByValue": True,
            },
        )

        page_data = (
            result
            .get("result", {})
            .get("result", {})
            .get("value")
        )

        if not page_data:

            return (
                "I opened the webpage, but I "
                "couldn't extract readable text, Sir."
            )

        title = page_data.get(
            "title",
            "",
        )

        final_url = page_data.get(
            "url",
            url,
        )

        text = page_data.get(
            "text",
            "",
        )

        text = text[:max_chars]

        return (
            "WEBPAGE CONTENT\n\n"
            f"Title: {title}\n"
            f"URL: {final_url}\n\n"
            f"{text}"
        )

    except Exception as error:

        return (
            "I couldn't read that webpage, Sir. "
            f"{error}"
        )

    finally:

        if ws is not None:

            try:
                ws.close()
            except Exception:
                pass
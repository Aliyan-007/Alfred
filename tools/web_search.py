import json
import time
from tools.browser import ensure_brave
from urllib.parse import quote_plus

import requests
import websocket


CDP_BASE = "http://127.0.0.1:9222"
CDP_TIMEOUT = 10


# =========================================================
# CDP
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
# FIND EXISTING SEARCH TAB
# =========================================================

def find_search_tab():

    response = requests.get(
        f"{CDP_BASE}/json/list",
        timeout=5,
    )

    response.raise_for_status()

    pages = response.json()

    for page in pages:

        if page.get("type") != "page":
            continue

        url = page.get(
            "url",
            "",
        ).lower()

        if (
            "google.com/search" in url
            or "bing.com/search" in url
            or "duckduckgo.com" in url
        ):
            return page

    return None


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
# SEARCH WEB
# =========================================================

def web_search(
    query: str,
    num_results: int = 5,
):
    """
    Search the web using the existing Brave browser.

    Returns a compact set of search results for the AI.
    """

    query = query.strip()

    if not query:
        return "Please provide something to search for, Sir."

    num_results = max(
        1,
        min(
            int(num_results),
            10,
        ),
    )

    search_url = (
        "https://www.google.com/search?q="
        + quote_plus(query)
    )

    ws = None

    try:

        # -------------------------------------------------
        # Reuse an existing search tab when possible.
        # -------------------------------------------------

        search_tab = find_search_tab()

        if search_tab:

            print(
                "Existing search tab found. "
                "Using it."
            )

        else:

            print(
                "No search tab found. "
                "Creating one."
            )

            search_tab = create_tab()

        websocket_url = search_tab.get(
            "webSocketDebuggerUrl"
        )

        if not websocket_url:

            return (
                "Brave did not provide a search-tab "
                "connection, Sir."
            )

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
        # Navigate to Google.
        # -------------------------------------------------

        cdp_command(
            ws,
            3,
            "Page.navigate",
            {
                "url": search_url
            },
        )

        print(
            f"Searching web for: {query}"
        )

        # Give Google time to render.
        time.sleep(3)

        # -------------------------------------------------
        # Extract search results.
        # -------------------------------------------------

        result = cdp_command(
            ws,
            4,
            "Runtime.evaluate",
            {
                "expression": """
                (() => {

                    const results = [];

                    const blocks = [
                        ...document.querySelectorAll(
                            "div.MjjYud"
                        )
                    ];

                    for (
                        const block of blocks
                    ) {

                        const link =
                            block.querySelector(
                                "a"
                            );

                        const heading =
                            block.querySelector(
                                "h3"
                            );

                        if (!link || !heading) {
                            continue;
                        }

                        const href =
                            link.href || "";

                        const title =
                            (
                                heading.innerText
                                || ""
                            ).trim();

                        const text =
                            (
                                block.innerText
                                || ""
                            )
                            .replace(
                                /\\s+/g,
                                " "
                            )
                            .trim();

                        if (
                            !href ||
                            !title
                        ) {
                            continue;
                        }

                        results.push({
                            title,
                            url: href,
                            snippet: text.slice(
                                0,
                                500
                            )
                        });

                        if (
                            results.length >=
                            %d
                        ) {
                            break;
                        }
                    }

                    return results;

                })()
                """ % num_results,
                "returnByValue": True,
            },
        )

        results = (
            result
            .get("result", {})
            .get("result", {})
            .get("value", [])
        )

        ws.close()
        ws = None

        if not results:
            return (
                f"I couldn't find useful web results "
                f"for '{query}', Sir."
            )

        # -------------------------------------------------
        # Format compact results for Qwen.
        # -------------------------------------------------

        lines = [
            f"WEB SEARCH RESULTS FOR: {query}",
            "",
        ]

        for index, item in enumerate(
            results,
            start=1,
        ):

            lines.append(
                f"{index}. {item['title']}"
            )

            lines.append(
                f"URL: {item['url']}"
            )

            lines.append(
                f"Snippet: {item['snippet']}"
            )

            lines.append("")

        return "\n".join(
            lines
        )

    except Exception as error:

        return (
            "Web search failed, Sir. "
            f"{error}"
        )

    finally:

        if ws is not None:

            try:
                ws.close()

            except Exception:
                pass
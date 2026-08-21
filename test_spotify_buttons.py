import json
import requests
import websocket


pages = requests.get(
    "http://127.0.0.1:9222/json/list",
    timeout=5,
).json()

spotify_pages = [
    page
    for page in pages
    if (
        page.get("type") == "page"
        and "open.spotify.com" in page.get("url", "")
    )
]

if not spotify_pages:
    print("No Spotify tab found.")
    raise SystemExit

page = spotify_pages[0]

print("Spotify tab:")
print(page["url"])
print()

ws = websocket.create_connection(
    page["webSocketDebuggerUrl"],
    origin="http://127.0.0.1:9222",
    timeout=8,
)

message = {
    "id": 1,
    "method": "Runtime.evaluate",
    "params": {
        "expression": """
            JSON.stringify(
                [...document.querySelectorAll("button")]
                    .filter(
                        b => b.offsetParent !== null
                    )
                    .map(
                        b => ({
                            aria: b.getAttribute("aria-label"),
                            title: b.getAttribute("title"),
                            testid: b.getAttribute("data-testid"),
                            text: (b.innerText || "").trim()
                        })
                    )
            )
        """,
        "returnByValue": True,
    },
}

ws.send(
    json.dumps(message)
)

while True:

    result = json.loads(
        ws.recv()
    )

    if result.get("id") == 1:

        print("VISIBLE SPOTIFY BUTTONS:")
        print()

        value = (
            result
            .get("result", {})
            .get("result", {})
            .get("value", "[]")
        )

        buttons = json.loads(value)

        for button in buttons:
            print(button)

        break

ws.close()
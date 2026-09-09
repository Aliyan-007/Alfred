import time
from urllib.parse import quote_plus

from tools.browser import (
    ensure_brave,
    find_page,
    navigate,
    bring_to_front,
    evaluate,
    open_web_destination
)


# =========================================================
# FIND SPOTIFY PAGE
# =========================================================

def find_spotify_page():
    return find_page("open.spotify.com")


# =========================================================
# SELECT SPOTIFY PAGE
# =========================================================

def select_spotify_page():
    page = find_spotify_page()
    if page is None:
        return None
    try:
        bring_to_front(page)
    except Exception:
        pass
    return page


# =========================================================
# CREATE SPOTIFY PAGE
# =========================================================

def create_spotify_page():
    import requests
    response = requests.put(
        "http://127.0.0.1:9222/json/new?https://open.spotify.com/",
        timeout=5,
    )
    response.raise_for_status()
    return response.json()


# =========================================================
# WAIT FOR SEARCH RESULTS
# =========================================================

def wait_for_spotify_results(page, query: str, timeout: int = 15):
    print(f"[SPOTIFY] Waiting for results for '{query}'...")
    start = time.time()
    while (time.time() - start) < timeout:
        try:
            result = evaluate(
                page,
                """
                function(query) {
                    var wanted = String(query).trim().toLowerCase();
                    var body = document.body;
                    var bodyText = "";
                    if (body) {
                        bodyText = String(body.innerText || "").toLowerCase();
                    }
                    var links = document.querySelectorAll('a[href*="/track/"]');
                    var visibleLinks = 0;
                    var matchingLinks = 0;

                    for (var i = 0; i < links.length; i++) {
                        var element = links[i];
                        if (element.offsetParent === null) continue;
                        visibleLinks++;
                        var text = String(element.innerText || element.textContent || "").trim().toLowerCase();
                        if (wanted.length > 0 && text.indexOf(wanted) !== -1) {
                            matchingLinks++;
                        }
                    }

                    return {
                        ready: document.readyState,
                        bodyContainsQuery: wanted.length > 0 && bodyText.indexOf(wanted) !== -1,
                        trackLinks: visibleLinks,
                        matchingTracks: matchingLinks
                    };
                }
                """,
                args=[query],
            )
            if result:
                if result.get("matchingTracks", 0) > 0 or (result.get("trackLinks", 0) > 0 and result.get("bodyContainsQuery", False)):
                    return True
        except Exception:
            pass
        time.sleep(0.5)
    return False


# =========================================================
# FIND MATCHING TRACK
# =========================================================

def find_spotify_track(page, query: str):
    return evaluate(
        page,
        """
        function(query) {
            var wanted = String(query).trim().toLowerCase();
            var links = document.querySelectorAll('a[href*="/track/"]');
            var exact = null;
            var partial = null;
            var words = wanted.split(/\\s+/);
            var best = null;
            var bestScore = 0;

            for (var i = 0; i < links.length; i++) {
                var element = links[i];
                if (element.offsetParent === null) continue;
                var title = String(element.innerText || element.textContent || "").trim();
                if (!title) continue;
                var lower = title.toLowerCase();

                if (lower === wanted) {
                    exact = element;
                    break;
                }
                if (partial === null && wanted.length > 0 && lower.indexOf(wanted) !== -1) {
                    partial = element;
                }

                var score = 0;
                for (var w = 0; w < words.length; w++) {
                    var word = words[w];
                    if (word.length >= 2 && lower.indexOf(word) !== -1) {
                        score++;
                    }
                }
                if (score > bestScore) {
                    bestScore = score;
                    best = element;
                }
            }

            if (exact !== null) {
                return { found: true, type: "exact", href: exact.href || "", text: String(exact.innerText || exact.textContent || "").trim() };
            }
            if (partial !== null) {
                return { found: true, type: "partial", href: partial.href || "", text: String(partial.innerText || partial.textContent || "").trim() };
            }
            if (best !== null && bestScore > 0) {
                return { found: true, type: "word_match", score: bestScore, href: best.href || "", text: String(best.innerText || best.textContent || "").trim() };
            }
            return { found: false };
        }
        """,
        args=[query],
    )


# =========================================================
# PLAY SPOTIFY
# =========================================================

def play_spotify(query: str) -> str:
    query = query.strip()
    if not query:
        return "What would you like me to play on Spotify, Sir?"

    # Check if Brave is running. If not, open directly in system browser cleanly.
    if not ensure_brave():
        return open_web_destination(f"https://open.spotify.com/search/{quote_plus(query)}")

    try:
        page = select_spotify_page()
        if page is None:
            page = create_spotify_page()
            time.sleep(2)

        try:
            bring_to_front(page)
        except Exception:
            pass

        search_url = "https://open.spotify.com/search/" + quote_plus(query)
        navigate(page, search_url)

        if not wait_for_spotify_results(page, query, timeout=12):
            return f"Opened search for '{query}' on Spotify, Sir."

        result = find_spotify_track(page, query)
        if not result or not result.get("found", False):
            return f"Searching Spotify for '{query}', Sir."

        track_title = result.get("text", query).strip()
        track_url = result.get("href", "")

        if not track_url:
            return f"Playing '{track_title}' on Spotify, Sir."

        track_url = track_url.split("?")[0]
        if track_url.startswith("/"):
            track_url = "https://open.spotify.com" + track_url

        navigate(page, track_url)
        return f"Playing '{track_title}' on Spotify, Sir."

    except Exception:
        # Failsafe fallback
        return open_web_destination(f"https://open.spotify.com/search/{quote_plus(query)}")


# =========================================================
# SPOTIFY PLAYBACK CONTROLS
# =========================================================

def spotify_control(action: str) -> str:
    if not ensure_brave():
        return "I couldn't control Spotify, Sir."

    try:
        page = select_spotify_page()
        if page is None:
            return "No active Spotify session was found, Sir."

        if action in {"pause", "resume", "play"}:
            state = evaluate(
                page,
                """
                function() {
                    var button = document.querySelector('[data-testid="control-button-playpause"]');
                    if (!button) return { found: false };
                    var label = String(button.getAttribute("aria-label") || "").trim().toLowerCase();
                    return { found: true, playing: label.indexOf("pause") !== -1 };
                }
                """
            )
            if not state or not state.get("found", False):
                return "I couldn't find Spotify's playback control, Sir."

            playing = state.get("playing", False)
            if action == "pause" and not playing:
                return "Spotify is already paused, Sir."
            if action in {"resume", "play"} and playing:
                return "Spotify is already playing, Sir."

            evaluate(page, "document.querySelector('[data-testid=\"control-button-playpause\"]').click()")
            return f"Spotify {action}d, Sir."

        if action == "next":
            evaluate(page, "document.querySelector('[data-testid=\"control-button-skip-forward\"]').click()")
            return "Skipped to the next track, Sir."

        if action == "previous":
            evaluate(page, "document.querySelector('[data-testid=\"control-button-skip-back\"]').click()")
            return "Playing the previous track, Sir."

    except Exception as error:
        return f"I couldn't control Spotify, Sir: {error}"

import time
from urllib.parse import quote_plus

from tools.browser import (
    ensure_brave,
    find_page,
    navigate,
    bring_to_front,
    evaluate,
)


# =========================================================
# FIND SPOTIFY PAGE
# =========================================================

def find_spotify_page():
    """
    Find the Spotify tab in the ALFRED Brave browser.
    """

    return find_page(
        "open.spotify.com"
    )


# =========================================================
# SELECT SPOTIFY PAGE
# =========================================================

def select_spotify_page():
    """
    Find and bring the Spotify tab to the front.
    """

    page = find_spotify_page()

    if page is None:
        return None

    try:
        bring_to_front(
            page
        )
    except Exception:
        pass

    return page


# =========================================================
# CREATE SPOTIFY PAGE
# =========================================================

def create_spotify_page():
    """
    Create a Spotify tab in the ALFRED Brave browser.
    """

    import requests

    response = requests.put(
        "http://127.0.0.1:9222/json/new"
        "?https://open.spotify.com/",
        timeout=5,
    )

    response.raise_for_status()

    return response.json()


# =========================================================
# WAIT FOR SEARCH RESULTS
# =========================================================

def wait_for_spotify_results(
    page,
    query: str,
    timeout: int = 20,
):
    """
    Wait until Spotify has actually rendered search results.
    """

    print(
        f"[SPOTIFY] Waiting for results for '{query}'..."
    )

    start = time.time()

    while (
        time.time() - start
    ) < timeout:

        try:

            result = evaluate(
                page,
                """
                function(query) {

                    var wanted =
                        String(query)
                            .trim()
                            .toLowerCase();

                    var body =
                        document.body;

                    var bodyText = "";

                    if (body) {
                        bodyText =
                            String(
                                body.innerText || ""
                            ).toLowerCase();
                    }

                    var links =
                        document.querySelectorAll(
                            'a[href*="/track/"]'
                        );

                    var visibleLinks = 0;
                    var matchingLinks = 0;

                    for (
                        var i = 0;
                        i < links.length;
                        i++
                    ) {

                        var element =
                            links[i];

                        if (
                            element.offsetParent === null
                        ) {
                            continue;
                        }

                        visibleLinks++;

                        var text =
                            String(
                                element.innerText
                                || element.textContent
                                || ""
                            )
                            .trim()
                            .toLowerCase();

                        if (
                            wanted.length > 0
                            && text.indexOf(
                                wanted
                            ) !== -1
                        ) {
                            matchingLinks++;
                        }
                    }

                    return {
                        ready:
                            document.readyState,

                        bodyContainsQuery:
                            wanted.length > 0
                            && bodyText.indexOf(
                                wanted
                            ) !== -1,

                        trackLinks:
                            visibleLinks,

                        matchingTracks:
                            matchingLinks
                    };
                }
                """,
                args=[
                    query
                ],
            )

            print(
                f"[SPOTIFY] DOM status: {result}"
            )

            if result:

                if (
                    result.get(
                        "matchingTracks",
                        0,
                    ) > 0
                ):

                    print(
                        "[SPOTIFY] Search content is ready."
                    )

                    return True

                if (
                    result.get(
                        "trackLinks",
                        0,
                    ) > 0
                    and result.get(
                        "bodyContainsQuery",
                        False,
                    )
                ):

                    print(
                        "[SPOTIFY] Search content is ready."
                    )

                    return True

        except Exception as error:

            print(
                f"[SPOTIFY] Waiting for results: {error}"
            )

        time.sleep(
            0.5
        )

    print(
        "[SPOTIFY] Search results timed out."
    )

    return False


# =========================================================
# FIND MATCHING TRACK
# =========================================================

def find_spotify_track(
    page,
    query: str,
):
    """
    Find a matching Spotify track.

    We prefer a title containing the full query.
    We do not blindly select the first result.
    """

    return evaluate(
        page,
        """
        function(query) {

            var wanted =
                String(query)
                    .trim()
                    .toLowerCase();

            var links =
                document.querySelectorAll(
                    'a[href*="/track/"]'
                );

            var exact = null;
            var partial = null;

            var words =
                wanted.split(
                    /\\s+/
                );

            var best = null;
            var bestScore = 0;

            for (
                var i = 0;
                i < links.length;
                i++
            ) {

                var element =
                    links[i];

                if (
                    element.offsetParent === null
                ) {
                    continue;
                }

                var title =
                    String(
                        element.innerText
                        || element.textContent
                        || ""
                    ).trim();

                if (!title) {
                    continue;
                }

                var lower =
                    title.toLowerCase();

                // -----------------------------------------
                // Exact title match
                // -----------------------------------------

                if (
                    lower === wanted
                ) {

                    exact = element;
                    break;
                }

                // -----------------------------------------
                // Full query inside title
                // -----------------------------------------

                if (
                    partial === null
                    && wanted.length > 0
                    && lower.indexOf(
                        wanted
                    ) !== -1
                ) {

                    partial = element;
                }

                // -----------------------------------------
                // Word scoring
                // -----------------------------------------

                var score = 0;

                for (
                    var w = 0;
                    w < words.length;
                    w++
                ) {

                    var word =
                        words[w];

                    if (
                        word.length >= 2
                        && lower.indexOf(
                            word
                        ) !== -1
                    ) {

                        score++;
                    }
                }

                if (
                    score > bestScore
                ) {

                    bestScore = score;
                    best = element;
                }
            }

            // Exact match wins.
            if (exact !== null) {

                return {
                    found: true,
                    type: "exact",
                    href:
                        exact.href || "",
                    text:
                        String(
                            exact.innerText
                            || exact.textContent
                            || ""
                        ).trim()
                };
            }

            // Full query match next.
            if (partial !== null) {

                return {
                    found: true,
                    type: "partial",
                    href:
                        partial.href || "",
                    text:
                        String(
                            partial.innerText
                            || partial.textContent
                            || ""
                        ).trim()
                };
            }

            // Word match only if at least one useful
            // search word matched.
            if (
                best !== null
                && bestScore > 0
            ) {

                return {
                    found: true,
                    type: "word_match",
                    score: bestScore,
                    href:
                        best.href || "",
                    text:
                        String(
                            best.innerText
                            || best.textContent
                            || ""
                        ).trim()
                };
            }

            return {
                found: false
            };
        }
        """,
        args=[
            query
        ],
    )


# =========================================================
# PLAY SPOTIFY
# =========================================================

def play_spotify(
    query: str,
):
    """
    Search Spotify and open the best matching track.

    Spotify's normal track page can autoplay depending on
    the current browser/player state, so this function does
    not depend on a fragile Play button selector.
    """

    query = query.strip()

    # Always initialize this so exception paths never fail
    # with "track_title referenced before assignment".
    track_title = query

    if not query:

        return (
            "What would you like me to play "
            "on Spotify, Sir?"
        )

    if not ensure_brave():

        return (
            "I couldn't start ALFRED's Spotify browser, Sir."
        )

    try:

        # -------------------------------------------------
        # Find existing Spotify page
        # -------------------------------------------------

        page = select_spotify_page()

        # -------------------------------------------------
        # Open Spotify if necessary
        # -------------------------------------------------

        if page is None:

            print(
                "[SPOTIFY] No Spotify tab found."
            )

            print(
                "[SPOTIFY] Opening Spotify..."
            )

            page = create_spotify_page()

            time.sleep(
                2
            )

        # -------------------------------------------------
        # Bring to front
        # -------------------------------------------------

        try:

            bring_to_front(
                page
            )

        except Exception:
            pass

        # -------------------------------------------------
        # Navigate to search
        # -------------------------------------------------

        search_url = (
            "https://open.spotify.com/search/"
            + quote_plus(query)
        )

        print(
            f"[SPOTIFY] Searching for: {query}"
        )

        navigate(
            page,
            search_url,
        )

        # -------------------------------------------------
        # Wait for search results
        # -------------------------------------------------

        if not wait_for_spotify_results(
            page,
            query,
            timeout=20,
        ):

            try:

                fallback_text = evaluate(
                    page,
                    """
                    function() {

                        if (!document.body) {
                            return "";
                        }

                        return String(
                            document.body.innerText
                            || ""
                        ).slice(
                            0,
                            2000
                        );
                    }
                    """,
                )

                print(
                    "[SPOTIFY] Final page text:"
                )

                print(
                    fallback_text
                )

            except Exception:
                pass

            return (
                f"Spotify search results for "
                f"'{query}' did not become detectable, Sir."
            )

        # -------------------------------------------------
        # Find matching track
        # -------------------------------------------------

        result = find_spotify_track(
            page,
            query,
        )

        print(
            "[SPOTIFY] Search match:"
        )

        print(
            result
        )

        if not result or not result.get(
            "found",
            False,
        ):

            return (
                f"I couldn't find '{query}' on Spotify, Sir."
            )

        # -------------------------------------------------
        # Save track title safely
        # -------------------------------------------------

        track_title = (
            result.get(
                "text",
                query,
            )
            or query
        ).strip()

        if not track_title:
            track_title = query

        print(
            f"[SPOTIFY] Found: {track_title}"
        )

        # -------------------------------------------------
        # Get exact track URL
        # -------------------------------------------------

        track_url = (
            result.get(
                "href",
                "",
            )
            or ""
        )

        if not track_url:

            return (
                f"I found '{track_title}', but couldn't "
                "determine its Spotify URL, Sir."
            )

        # Remove tracking/query parameters.
        track_url = track_url.split(
            "?"
        )[0]

        # Relative URL fallback.
        if track_url.startswith("/"):
            track_url = (
                "https://open.spotify.com"
                + track_url
            )

        if "/track/" not in track_url:

            return (
                f"I found '{track_title}', but the "
                "Spotify result did not provide a valid track URL, Sir."
            )

        # -------------------------------------------------
        # Open exact track
        # -------------------------------------------------

        print(
            f"[SPOTIFY] Opening track: {track_url}"
        )

        navigate(
            page,
            track_url,
        )

        # Short transition delay. We do not use a long
        # arbitrary player wait anymore.
        time.sleep(
            2
        )

        print(
            f"[SPOTIFY] Track opened: {track_title}"
        )

        # -------------------------------------------------
        # Verify that navigation reached a track page.
        # -------------------------------------------------

        try:

            page_state = evaluate(
                page,
                """
                function() {

                    return {
                        url:
                            window.location.href,

                        title:
                            document.title
                    };
                }
                """,
            )

            print(
                "[SPOTIFY] Track page state:"
            )

            print(
                page_state
            )

            if page_state:

                current_url = (
                    page_state.get(
                        "url",
                        "",
                    )
                    or ""
                )

                if "/track/" not in current_url:

                    return (
                        f"Spotify opened '{track_title}', "
                        "but the track page did not finish navigating, Sir."
                    )

        except Exception:

            # The page has already been navigated to the
            # exact track URL, so don't fail solely because
            # verification isn't available.
            pass

        return (
            f"Playing '{track_title}' on Spotify, Sir."
        )

    except Exception as error:

        return (
            "I couldn't control Spotify, Sir. "
            f"{error}"
        )


# =========================================================
# SPOTIFY PLAYBACK CONTROLS
# =========================================================

def spotify_control(
    action: str,
):
    """
    Control Spotify playback on the current Spotify page.
    """

    if not ensure_brave():

        return (
            "I couldn't connect to Spotify, Sir."
        )

    try:

        page = select_spotify_page()

        if page is None:

            return (
                "I couldn't find an open Spotify tab, Sir."
            )

        # =================================================
        # PLAY / PAUSE / RESUME
        # =================================================

        if action in {
            "pause",
            "resume",
            "play",
        }:

            state = evaluate(
                page,
                """
                function() {

                    var button =
                        document.querySelector(
                            '[data-testid="control-button-playpause"]'
                        );

                    if (!button) {

                        return {
                            found: false
                        };
                    }

                    var label =
                        String(
                            button.getAttribute(
                                "aria-label"
                            )
                            || ""
                        )
                        .trim()
                        .toLowerCase();

                    return {
                        found: true,

                        playing:
                            label.indexOf(
                                "pause"
                            ) !== -1,

                        paused:
                            label.indexOf(
                                "play"
                            ) !== -1,

                        label:
                            label
                    };
                }
                """,
            )

            if not state or not state.get(
                "found",
                False,
            ):

                return (
                    "I couldn't find Spotify's "
                    "playback control, Sir."
                )

            playing = state.get(
                "playing",
                False,
            )

            paused = state.get(
                "paused",
                False,
            )

            # -------------------------------------------------
            # PAUSE
            # -------------------------------------------------

            if action == "pause":

                if not playing:

                    return (
                        "Spotify is already paused, Sir."
                    )

                result = evaluate(
                    page,
                    """
                    function() {

                        var button =
                            document.querySelector(
                                '[data-testid="control-button-playpause"]'
                            );

                        if (!button) {
                            return false;
                        }

                        button.click();

                        return true;
                    }
                    """,
                )

                if result:

                    return (
                        "Spotify paused, Sir."
                    )

                return (
                    "I couldn't pause Spotify, Sir."
                )

            # -------------------------------------------------
            # RESUME / PLAY
            # -------------------------------------------------

            if action in {
                "resume",
                "play",
            }:

                if playing:

                    return (
                        "Spotify is already playing, Sir."
                    )

                if paused:

                    result = evaluate(
                        page,
                        """
                        function() {

                            var button =
                                document.querySelector(
                                    '[data-testid="control-button-playpause"]'
                                );

                            if (!button) {
                                return false;
                            }

                            button.click();

                            return true;
                        }
                        """,
                    )

                    if result:

                        return (
                            "Spotify resumed, Sir."
                        )

                    return (
                        "I couldn't resume Spotify, Sir."
                    )

                return (
                    "Spotify's playback state is unclear, Sir."
                )

        # =================================================
        # NEXT
        # =================================================

        if action == "next":

            result = evaluate(
                page,
                """
                function() {

                    var button =
                        document.querySelector(
                            '[data-testid="control-button-skip-forward"]'
                        );

                    if (!button) {
                        return false;
                    }

                    button.click();

                    return true;
                }
                """,
            )

            if result:

                return (
                    "Playing the next Spotify track, Sir."
                )

            return (
                "I couldn't skip to the next Spotify track, Sir."
            )

        # =================================================
        # PREVIOUS
        # =================================================

        if action == "previous":

            result = evaluate(
                page,
                """
                function() {

                    var button =
                        document.querySelector(
                            '[data-testid="control-button-skip-back"]'
                        );

                    if (!button) {
                        return false;
                    }

                    button.click();

                    return true;
                }
                """,
            )

            if result:

                return (
                    "Going back to the previous "
                    "Spotify track, Sir."
                )

            return (
                "I couldn't go to the previous "
                "Spotify track, Sir."
            )

        # =================================================
        # UNKNOWN ACTION
        # =================================================

        return (
            "That Spotify control isn't available yet, Sir."
        )

    except Exception as error:

        return (
            "I couldn't control Spotify, Sir. "
            f"{error}"
        )

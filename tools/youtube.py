import time
from urllib.parse import quote_plus

from tools.browser import (
    ensure_brave,
    find_page,
    navigate,
    bring_to_front,
    evaluate,
    press_key,
)


# =========================================================
# PAGE HELPERS
# =========================================================

def find_youtube_page():
    return find_page(
        "youtube.com"
    )


def select_youtube_page():
    page = find_youtube_page()

    if page is None:
        return None

    try:
        bring_to_front(page)
    except Exception:
        pass

    return page


def create_youtube_page():
    import requests

    response = requests.put(
        "http://127.0.0.1:9222/json/new"
        "?https://www.youtube.com/",
        timeout=5,
    )

    response.raise_for_status()

    return response.json()


# =========================================================
# WAIT FOR SEARCH RESULTS
# =========================================================

def wait_for_youtube_results(
    page,
    query,
    timeout=20,
):
    print(
        "[YOUTUBE] Waiting for results for '{}'..."
        .format(query)
    )

    start = time.time()

    while time.time() - start < timeout:

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
                            "a#video-title"
                        );

                    var visibleCount = 0;
                    var matchingCount = 0;

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

                        visibleCount++;

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
                            matchingCount++;
                        }
                    }

                    return {
                        ready:
                            document.readyState,

                        bodyContainsQuery:
                            bodyText.indexOf(
                                wanted
                            ) !== -1,

                        videoLinks:
                            visibleCount,

                        matchingVideos:
                            matchingCount
                    };
                }
                """,
                args=[query],
            )

            print(
                "[YOUTUBE] DOM status: {}"
                .format(result)
            )

            if result:

                if (
                    result.get(
                        "matchingVideos",
                        0,
                    ) > 0
                ):
                    print(
                        "[YOUTUBE] Matching video detected."
                    )
                    return True
               
                if (
                    result.get(
                        "videoLinks",
                    0,
                    ) >= 3
                ):
                    print(
                    "[YOUTUBE] Video results are available."
                    )
                    return True 

        except Exception as error:

            print(
                "[YOUTUBE] Waiting for results: {}"
                .format(error)
            )

        time.sleep(
            0.5
        )

    print(
        "[YOUTUBE] Search results timed out."
    )

    return False


# =========================================================
# FIND VIDEO
# =========================================================

def find_youtube_video(
    page,
    query,
):
    """
    Find an exact, partial, or word-matching video.
    No modern JavaScript syntax is used here.
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
                    "a#video-title"
                );

            var exact = null;
            var partial = null;
            var best = null;
            var bestScore = 0;

            var words =
                wanted.split(
                    /\\s+/
                );

            var i;

            for (
                i = 0;
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

                var lower =
                    title.toLowerCase();

                if (
                    lower === wanted
                ) {

                    exact = element;
                    break;
                }

                if (
                    partial === null
                    && wanted.length > 0
                    && lower.indexOf(
                        wanted
                    ) !== -1
                ) {

                    partial = element;
                }

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

            var chosen =
                exact
                || partial
                || (
                    bestScore > 0
                    ? best
                    : null
                );

            if (chosen === null) {

                return {
                    found: false
                };
            }

            var href =
                chosen.getAttribute(
                    "href"
                );

            return {
                found: true,
                href:
                    href || "",
                title:
                    String(
                        chosen.innerText
                        || chosen.textContent
                        || ""
                    ).trim(),
                score:
                    exact
                    ? 100
                    : (
                        partial
                        ? 50
                        : bestScore
                    )
            };
        }
        """,
        args=[query],
    )


# =========================================================
# OPEN VIDEO
# =========================================================

def open_youtube_video(
    page,
    query,
):
    """
    Open the video matching the query.
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
                    "a#video-title"
                );

            var exact = null;
            var partial = null;
            var best = null;
            var bestScore = 0;

            var words =
                wanted.split(
                    /\\s+/
                );

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

                var lower =
                    title.toLowerCase();

                if (
                    lower === wanted
                ) {

                    exact = element;
                    break;
                }

                if (
                    partial === null
                    && wanted.length > 0
                    && lower.indexOf(
                        wanted
                    ) !== -1
                ) {

                    partial = element;
                }

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

            var chosen =
                exact
                || partial
                || (
                    bestScore > 0
                    ? best
                    : null
                );

            if (chosen === null) {

                return {
                    opened: false
                };
            }

            chosen.click();

            return {
                opened: true,
                title:
                    String(
                        chosen.innerText
                        || chosen.textContent
                        || ""
                    ).trim(),
                score:
                    exact
                    ? 100
                    : (
                        partial
                        ? 50
                        : bestScore
                    )
            };
        }
        """,
        args=[query],
    )


# =========================================================
# WAIT FOR VIDEO
# =========================================================

def wait_for_youtube_video(
    page,
    timeout=15,
):
    print(
        "[YOUTUBE] Waiting for video page..."
    )

    start = time.time()

    while time.time() - start < timeout:

        try:

            result = evaluate(
                page,
                """
                function() {

                    var video =
                        document.querySelector(
                            "video"
                        );

                    if (!video) {

                        return {
                            found: false
                        };
                    }

                    return {
                        found: true,
                        readyState:
                            video.readyState,
                        paused:
                            video.paused,
                        currentTime:
                            video.currentTime
                    };
                }
                """,
            )

            print(
                "[YOUTUBE] Video status: {}"
                .format(result)
            )

            if (
                result
                and result.get(
                    "found",
                    False,
                )
            ):

                return True

        except Exception as error:

            print(
                "[YOUTUBE] Video check: {}"
                .format(error)
            )

        time.sleep(
            0.5
        )

    return False


# =========================================================
# GET VIDEO STATE
# =========================================================

def get_youtube_state(
    page,
):
    return evaluate(
        page,
        """
        function() {

            var video =
                document.querySelector(
                    "video"
                );

            if (!video) {

                return {
                    found: false
                };
            }

            return {
                found: true,

                paused:
                    video.paused,

                muted:
                    video.muted,

                volume:
                    video.volume,

                currentTime:
                    video.currentTime,

                duration:
                    video.duration,

                fullscreen:
                    !!document.fullscreenElement
            };
        }
        """,
    )


# =========================================================
# PLAY VIDEO
# =========================================================

def play_youtube(
    query,
):
    """
    Search YouTube and play a suitable matching video.
    """

    query = query.strip()

    if not query:

        return (
            "What would you like me to play "
            "on YouTube, Sir?"
        )

    if not ensure_brave():

        return (
            "I couldn't start ALFRED's YouTube browser, Sir."
        )

    try:

        page = select_youtube_page()

        if page is None:

            print(
                "[YOUTUBE] No YouTube tab found."
            )

            print(
                "[YOUTUBE] Opening YouTube..."
            )

            page = create_youtube_page()

            time.sleep(
                2
            )

        try:
            bring_to_front(
                page
            )
        except Exception:
            pass

        search_url = (
            "https://www.youtube.com/results?search_query="
            + quote_plus(query)
        )

        print(
            "[YOUTUBE] Searching for: {}"
            .format(query)
        )

        navigate(
            page,
            search_url,
        )

        if not wait_for_youtube_results(
            page,
            query,
            timeout=20,
        ):

            return (
                "YouTube search results for "
                "'{}' did not become ready, Sir."
                .format(query)
            )

        result = find_youtube_video(
            page,
            query,
        )

        print(
            "[YOUTUBE] Search match: {}"
            .format(result)
        )

        if not result or not result.get(
            "found",
            False,
        ):

            return (
                "I couldn't find a suitable YouTube "
                "video for '{}', Sir."
                .format(query)
            )

        video_title = (
            result.get(
                "title",
                query,
            )
            .strip()
        )

        print(
            "[YOUTUBE] Found: {}"
            .format(video_title)
        )

        opened = open_youtube_video(
            page,
            query,
        )

        print(
            "[YOUTUBE] Open result: {}"
            .format(opened)
        )

        if not opened or not opened.get(
            "opened",
            False,
        ):

            return (
                "I found '{}', but couldn't open it, Sir."
                .format(video_title)
            )

        if not wait_for_youtube_video(
            page,
            timeout=15,
        ):

            return (
                "I opened '{}', but the video player "
                "did not become ready, Sir."
                .format(video_title)
            )

        state = get_youtube_state(
            page
        )

        print(
            "[YOUTUBE] Playback state: {}"
            .format(state)
        )

        if not state or not state.get(
            "found",
            False,
        ):

            return (
                "I opened '{}', but couldn't read "
                "the player state, Sir."
                .format(video_title)
            )

        if state.get(
            "paused",
            True,
        ):

            result = evaluate(
                page,
                """
                function() {

                    var video =
                        document.querySelector(
                            "video"
                        );

                    if (!video) {
                        return false;
                    }

                    try {

                        var promise =
                            video.play();

                        if (
                            promise
                            && promise.catch
                        ) {

                            promise.catch(
                                function() {}
                            );
                        }

                        return true;

                    } catch (
                        error
                    ) {

                        return false;
                    }
                }
                """,
            )

            print(
                "[YOUTUBE] Play result: {}"
                .format(result)
            )

            time.sleep(
                0.8
            )

        return (
            "Playing '{}' on YouTube, Sir."
            .format(video_title)
        )

    except Exception as error:

        return (
            "I couldn't control YouTube, Sir. "
            "{}"
            .format(error)
        )


# =========================================================
# FULLSCREEN
# =========================================================

def youtube_fullscreen(
    page,
):
    """
    Enter YouTube fullscreen using the native F shortcut,
    then verify the browser actually entered fullscreen.
    """

    try:

        # YouTube's native fullscreen shortcut.
        pressed = press_key(
            page,
            "f",
        )

        print(
            "[YOUTUBE] Fullscreen key result:",
            pressed,
        )

        if not pressed:
            return (
                "I couldn't activate YouTube fullscreen, Sir."
            )

        # Give the browser a moment to process the shortcut.
        time.sleep(0.8)

        # Verify actual browser fullscreen state.
        state = evaluate(
            page,
            """
            function() {

                return {
                    fullscreen:
                        !!document.fullscreenElement,

                    videoFullscreen:
                        !!(
                            document.querySelector("video")
                            && document.fullscreenElement
                            === document.querySelector("video")
                        )
                };
            }
            """,
        )

        print(
            "[YOUTUBE] Fullscreen state:",
            state,
        )

        if (
            state
            and state.get(
                "fullscreen",
                False,
            )
        ):
            return (
                "YouTube is now in fullscreen, Sir."
            )

        return (
            "YouTube did not enter fullscreen, Sir."
        )

    except Exception as error:

        return (
            "I couldn't put YouTube into fullscreen, Sir. "
            f"{error}"
        )
# =========================================================
# YOUTUBE CONTROLS
# =========================================================

def youtube_control(
    action,
):
    """
    Control the current YouTube video.
    """

    if not ensure_brave():

        return (
            "I couldn't connect to YouTube, Sir."
        )

    try:

        page = select_youtube_page()

        if page is None:

            return (
                "I couldn't find an open YouTube tab, Sir."
            )

        # -------------------------------------------------
        # PLAY / PAUSE / RESUME
        # -------------------------------------------------

        if action in {
            "pause",
            "resume",
            "play",
        }:

            state = get_youtube_state(
                page
            )

            if not state or not state.get(
                "found",
                False,
            ):

                return (
                    "I couldn't find the YouTube video player, Sir."
                )

            paused = state.get(
                "paused",
                True,
            )

            if action == "pause":

                if paused:

                    return (
                        "YouTube is already paused, Sir."
                    )

                result = evaluate(
                    page,
                    """
                    function() {

                        var video =
                            document.querySelector(
                                "video"
                            );

                        if (!video) {
                            return false;
                        }

                        video.pause();

                        return true;
                    }
                    """,
                )

                if result:

                    return (
                        "YouTube paused, Sir."
                    )

                return (
                    "I couldn't pause YouTube, Sir."
                )

            if action in {
                "resume",
                "play",
            }:

                if not paused:

                    return (
                        "YouTube is already playing, Sir."
                    )

                result = evaluate(
                    page,
                    """
                    function() {

                        var video =
                            document.querySelector(
                                "video"
                            );

                        if (!video) {
                            return false;
                        }

                        try {

                            video.play();

                            return true;

                        } catch (
                            error
                        ) {

                            return false;
                        }
                    }
                    """,
                )

                if result:

                    return (
                        "YouTube resumed, Sir."
                    )

                return (
                    "YouTube didn't allow playback to start, Sir."
                )

        # -------------------------------------------------
        # FULLSCREEN
        # -------------------------------------------------

        if action == "fullscreen":

            return youtube_fullscreen(
                page
            )

        # -------------------------------------------------
        # EXIT FULLSCREEN
        # -------------------------------------------------

        if action in {
            "exit_fullscreen",
            "windowed",
        }:

            result = evaluate(
                page,
                """
                function() {

                    if (
                        document.fullscreenElement
                    ) {

                        try {

                            document.exitFullscreen();

                            return true;

                        } catch (
                            error
                        ) {

                            return false;
                        }
                    }

                    return true;
                }
                """,
            )

            if result:

                return (
                    "YouTube exited fullscreen, Sir."
                )

            return (
                "I couldn't exit YouTube fullscreen, Sir."
            )

        # -------------------------------------------------
        # NEXT
        # -------------------------------------------------

        if action == "next":

            result = evaluate(
                page,
                """
                function() {

                    var button =
                        document.querySelector(
                            ".ytp-next-button"
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
                    "Playing the next YouTube video, Sir."
                )

            return (
                "I couldn't move to the next YouTube video, Sir."
            )

        # -------------------------------------------------
        # PREVIOUS
        # -------------------------------------------------

        if action == "previous":

            result = evaluate(
                page,
                """
                function() {

                    var button =
                        document.querySelector(
                            ".ytp-prev-button"
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
                    "Going back to the previous YouTube video, Sir."
                )

            return (
                "I couldn't go to the previous YouTube video, Sir."
            )

        # -------------------------------------------------
        # VOLUME UP
        # -------------------------------------------------

        if action == "volume_up":

            result = evaluate(
                page,
                """
                function() {

                    var video =
                        document.querySelector(
                            "video"
                        );

                    if (!video) {
                        return false;
                    }

                    video.volume =
                        Math.min(
                            1,
                            video.volume + 0.10
                        );

                    return true;
                }
                """,
            )

            if result:

                return (
                    "YouTube volume increased, Sir."
                )

            return (
                "I couldn't increase YouTube volume, Sir."
            )

        # -------------------------------------------------
        # VOLUME DOWN
        # -------------------------------------------------

        if action == "volume_down":

            result = evaluate(
                page,
                """
                function() {

                    var video =
                        document.querySelector(
                            "video"
                        );

                    if (!video) {
                        return false;
                    }

                    video.volume =
                        Math.max(
                            0,
                            video.volume - 0.10
                        );

                    return true;
                }
                """,
            )

            if result:

                return (
                    "YouTube volume decreased, Sir."
                )

            return (
                "I couldn't decrease YouTube volume, Sir."
            )

        # -------------------------------------------------
        # STOP
        # -------------------------------------------------

        if action == "stop":

            result = evaluate(
                page,
                """
                function() {

                    var video =
                        document.querySelector(
                            "video"
                        );

                    if (!video) {
                        return false;
                    }

                    video.pause();
                    video.currentTime = 0;

                    return true;
                }
                """,
            )

            if result:

                return (
                    "YouTube stopped, Sir."
                )

            return (
                "I couldn't stop YouTube, Sir."
            )

        return (
            "That YouTube control isn't available yet, Sir."
        )

    except Exception as error:

        return (
            "I couldn't control YouTube, Sir. "
            "{}"
            .format(error)
        )

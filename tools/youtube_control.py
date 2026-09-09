from urllib.parse import quote_plus
import webbrowser

from tools.browser import ensure_brave, find_page, navigate, bring_to_front, open_web_destination


def play_youtube(query: str) -> str:
    """
    Search YouTube for a query. Uses CDP if Brave is CDP-enabled,
    otherwise reliably opens in the default system browser.
    """
    query = str(query or "").strip()
    if not query:
        return "What would you like me to search on YouTube, Sir?"

    # YouTube auto-play URL trick
    search_url = f"https://www.youtube.com/results?search_query={quote_plus(query)}"

    # 1. Attempt CDP through Brave (if enabled)
    try:
        if ensure_brave():
            page = find_page("youtube.com")
            if page:
                navigate(page, search_url)
                bring_to_front(page)
                return f"Searching YouTube for '{query}', Sir."
    except Exception:
        pass

    # 2. Reliable Web Fallback
    try:
        webbrowser.open(search_url)
        return f"Searching YouTube for '{query}', Sir."
    except Exception as error:
        return f"I couldn't open YouTube: {error}"


def youtube_control(action: str) -> str:
    """
    Control playing YouTube tab via CDP.
    Requires Brave with --remote-debugging-port=9222 enabled.
    """
    if not ensure_brave():
        return "YouTube control requires Brave running with CDP enabled, Sir."

    try:
        page = find_page("youtube.com")
        if not page:
            return "No active YouTube tab was found, Sir."

        from tools.browser import evaluate

        scripts = {
            "pause": "const v = document.querySelector('video'); if (v && !v.paused) v.pause();",
            "resume": "const v = document.querySelector('video'); if (v && v.paused) v.play();",
            "play": "const v = document.querySelector('video'); if (v) v.play();",
            "stop": "const v = document.querySelector('video'); if (v) { v.pause(); v.currentTime = 0; }",
            "next": "document.querySelector('.ytp-next-button')?.click();",
            "previous": "document.querySelector('.ytp-prev-button')?.click();",
            "mute": "const v = document.querySelector('video'); if (v) v.muted = true;",
            "unmute": "const v = document.querySelector('video'); if (v) v.muted = false;",
            "fullscreen": "document.querySelector('.ytp-fullscreen-button')?.click();",
        }

        script = scripts.get(action.lower())
        if not script:
            return f"YouTube action '{action}' is not supported, Sir."

        evaluate(page, script)
        return f"YouTube: {action} executed, Sir."

    except Exception as error:
        return f"Couldn't control YouTube, Sir: {error}"
import os
import requests

from dotenv import load_dotenv


# =========================================================
# CONFIGURATION
# =========================================================

load_dotenv()

YOUTUBE_API_KEY = os.getenv(
    "YOUTUBE_API_KEY"
)

SEARCH_URL = (
    "https://www.googleapis.com/youtube/v3/search"
)

VIDEOS_URL = (
    "https://www.googleapis.com/youtube/v3/videos"
)

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

RESEARCH_DIR = os.path.join(
    BASE_DIR,
    "research",
)

CURRENT_RESEARCH_FILE = os.path.join(
    RESEARCH_DIR,
    "current_youtube_research.txt",
)

os.makedirs(
    RESEARCH_DIR,
    exist_ok=True,
)


# =========================================================
# SEARCH
# =========================================================

def search_youtube_research(
    query: str,
    max_results: int = 5,
):
    query = query.strip()

    if not query:
        return []

    if not YOUTUBE_API_KEY:
        raise RuntimeError(
            "YOUTUBE_API_KEY is missing from .env"
        )

    params = {
        "part": "snippet",
        "q": query,
        "type": "video",
        "maxResults": max_results,
        "order": "relevance",
        "key": YOUTUBE_API_KEY,
    }

    response = requests.get(
        SEARCH_URL,
        params=params,
        timeout=20,
    )

    response.raise_for_status()

    data = response.json()

    results = []

    for item in data.get(
        "items",
        [],
    ):

        video_id = (
            item.get(
                "id",
                {},
            ).get(
                "videoId"
            )
        )

        snippet = item.get(
            "snippet",
            {}
        )

        if not video_id:
            continue

        results.append(
            {
                "video_id": video_id,
                "title": snippet.get(
                    "title",
                    "",
                ),
                "channel": snippet.get(
                    "channelTitle",
                    "",
                ),
                "published_at": snippet.get(
                    "publishedAt",
                    "",
                ),
                "description": snippet.get(
                    "description",
                    "",
                ),
                "url": (
                    "https://www.youtube.com/watch?v="
                    + video_id
                ),
            }
        )

    return results


# =========================================================
# DETAILS
# =========================================================

def get_youtube_video_details(
    video_ids,
):

    if not video_ids:
        return []

    if not YOUTUBE_API_KEY:
        raise RuntimeError(
            "YOUTUBE_API_KEY is missing from .env"
        )

    params = {
        "part": (
            "snippet,"
            "contentDetails,"
            "statistics"
        ),
        "id": ",".join(
            video_ids
        ),
        "key": YOUTUBE_API_KEY,
    }

    response = requests.get(
        VIDEOS_URL,
        params=params,
        timeout=20,
    )

    response.raise_for_status()

    data = response.json()

    return data.get(
        "items",
        [],
    )


# =========================================================
# SAVE CURRENT RESEARCH
# =========================================================

def save_current_research(
    query: str,
    results,
):

    lines = [
        f"YouTube Research",
        f"Topic: {query}",
        "=" * 70,
        "",
    ]

    for index, result in enumerate(
        results,
        start=1,
    ):

        description = (
            result.get(
                "description",
                "",
            )
            .strip()
        )

        # Keep the document useful without making it huge.
        if len(description) > 1200:
            description = (
                description[:1200]
                + "..."
            )

        lines.extend(
            [
                f"VIDEO {index}",
                f"Title: {result.get('title', '')}",
                f"Channel: {result.get('channel', '')}",
                f"Published: {result.get('published_at', '')}",
                f"URL: {result.get('url', '')}",
                "",
                "Description:",
                description,
                "",
                "-" * 70,
                "",
            ]
        )

    content = "\n".join(
        lines
    )

    with open(
        CURRENT_RESEARCH_FILE,
        "w",
        encoding="utf-8",
    ) as file:

        file.write(
            content
        )

    return (
        content
    )


# =========================================================
# RESEARCH YOUTUBE
# =========================================================

def research_youtube(
    query: str,
    max_results: int = 5,
):
    """
    Search YouTube for research and store the resulting
    research packet locally.

    The full research is written to:
        research/current_youtube_research.txt

    Returning only a short confirmation keeps LLM tool
    arguments and follow-up tool calls small.
    """

    query = query.strip()

    if not query:

        return (
            "I need a YouTube research topic, Sir."
        )

    results = search_youtube_research(
        query,
        max_results=max_results,
    )

    if not results:

        return (
            f"No YouTube results were found for "
            f"'{query}', Sir."
        )

    video_ids = [
        item["video_id"]
        for item in results
    ]

    details = get_youtube_video_details(
        video_ids
    )

    details_by_id = {
        item.get("id"): item
        for item in details
    }

    enriched = []

    for result in results:

        video = details_by_id.get(
            result["video_id"],
            {},
        )

        snippet = video.get(
            "snippet",
            {},
        )

        statistics = video.get(
            "statistics",
            {},
        )

        enriched.append(
            {
                "video_id": result["video_id"],
                "title": (
                    snippet.get(
                        "title"
                    )
                    or result["title"]
                ),
                "channel": (
                    snippet.get(
                        "channelTitle"
                    )
                    or result["channel"]
                ),
                "published_at": (
                    snippet.get(
                        "publishedAt"
                    )
                    or result["published_at"]
                ),
                "description": (
                    snippet.get(
                        "description"
                    )
                    or result["description"]
                ),
                "views": statistics.get(
                    "viewCount",
                    "N/A",
                ),
                "likes": statistics.get(
                    "likeCount",
                    "N/A",
                ),
                "url": result["url"],
            }
        )

    content = save_current_research(
        query,
        enriched,
    )

    return (
        f"YouTube research completed for '{query}', Sir. "
        f"{len(enriched)} videos were collected and saved "
        f"to the current research packet.\n\n"
        f"Research file: {CURRENT_RESEARCH_FILE}"
    )

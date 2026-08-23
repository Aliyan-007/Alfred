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


# =========================================================
# SEARCH YOUTUBE
# =========================================================

def search_youtube_research(
    query: str,
    max_results: int = 5,
):
    """
    Search YouTube for research purposes.

    Returns video metadata rather than controlling playback.
    """

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
            )
            .get(
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
# GET VIDEO DETAILS
# =========================================================

def get_youtube_video_details(
    video_ids,
):
    """
    Retrieve additional metadata for selected videos.
    """

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
# RESEARCH TEXT
# =========================================================

def research_youtube(
    query: str,
    max_results: int = 5,
):
    """
    Search YouTube and turn the returned metadata into a
    clean text research packet for ALFRED.
    """

    results = search_youtube_research(
        query,
        max_results=max_results,
    )

    if not results:

        return (
            f"No YouTube results were found for '{query}'."
        )

    video_ids = [
        item["video_id"]
        for item in results
    ]

    detailed_items = get_youtube_video_details(
        video_ids
    )

    details_by_id = {
        item.get("id"): item
        for item in detailed_items
    }

    sections = []

    for index, result in enumerate(
        results,
        start=1,
    ):

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

        title = (
            snippet.get(
                "title"
            )
            or result["title"]
        )

        channel = (
            snippet.get(
                "channelTitle"
            )
            or result["channel"]
        )

        description = (
            snippet.get(
                "description"
            )
            or result["description"]
        )

        published = (
            snippet.get(
                "publishedAt"
            )
            or result["published_at"]
        )

        views = statistics.get(
            "viewCount",
            "N/A",
        )

        likes = statistics.get(
            "likeCount",
            "N/A",
        )

        sections.append(
            "\n".join(
                [
                    f"VIDEO {index}",
                    f"Title: {title}",
                    f"Channel: {channel}",
                    f"Published: {published}",
                    f"Views: {views}",
                    f"Likes: {likes}",
                    f"URL: {result['url']}",
                    "",
                    "Description:",
                    description,
                ]
            )
        )

    return (
        f"YouTube research for: {query}\n"
        f"{'=' * 60}\n\n"
        + "\n\n".join(
            sections
        )
    )

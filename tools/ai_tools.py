import json


from tools.system import open_application
from tools.web_search import web_search
from tools.file_finder import find_and_open_file
from tools.webpage import open_webpage
from tools.youtube_research import research_youtube

from tools.spotify import (
    play_spotify,
    spotify_control,
)

from tools.youtube import (
    play_youtube,
    youtube_control,
)

from tools.media import (
    pc_volume_up,
    pc_volume_down,
    pc_volume_mute,
    pc_volume_unmute,
)

from tools.gmail import(
    draft_email,
    send_pending_email,
)

from tools.document_writer import (
    save_to_notepad,
    save_to_word,
)
# =========================================================
# TOOL DEFINITIONS
# =========================================================

TOOL_DEFINITIONS = [

    # =====================================================
    # OPEN APPLICATION
    # =====================================================

    {
        "type": "function",
        "function": {
            "name": "open_application",
            "description": (
                "Open an approved Windows application. "
                "Use this when the user explicitly asks "
                "to open, launch, or start an application."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "application": {
                        "type": "string",
                        "description": (
                            "Application name, such as "
                            "brave, chrome, calculator, "
                            "notepad, or vscode."
                        ),
                    },
                },
                "required": [
                    "application",
                ],
            },
        },
    },

    # =====================================================
    # OPEN WEBPAGE
    # =====================================================

    {
        "type": "function",
        "function": {
            "name": "open_webpage",
            "description": (
                "Open a specific webpage URL in Brave and "
                "extract its readable text so the AI can "
                "analyze or summarize the page."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": (
                            "The full webpage URL to open."
                        ),
                    },
                    "max_chars": {
                        "type": "integer",
                        "description": (
                            "Maximum amount of webpage text "
                            "to return. Normally use 12000."
                        ),
                    },
                },
                "required": [
                    "url",
                ],
            },
        },
    },

    # =====================================================
    # WEB SEARCH
    # =====================================================

    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": (
                "Search the live web for current information, "
                "news, websites, documentation, prices, events, "
                "or anything that may require up-to-date information."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": (
                            "The exact topic or question "
                            "to search for."
                        ),
                    },
                    "num_results": {
                        "type": "integer",
                        "description": (
                            "Number of search results to retrieve. "
                            "Use 5 normally."
                        ),
                    },
                },
                "required": [
                    "query",
                ],
            },
        },
    },

    # =====================================================
    # SPOTIFY PLAY
    # =====================================================

    {
        "type": "function",
        "function": {
            "name": "play_spotify",
            "description": (
                "Search Spotify for a song, artist, album, "
                "or other media and start playback. "
                "Use the user's wording as the search query. "
                "When the user gives both a song and artist, "
                "include both in the query."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": (
                            "The song, artist, album, or media "
                            "the user wants to play."
                        ),
                    },
                },
                "required": [
                    "query",
                ],
            },
        },
    },

    # =====================================================
    # YOUTUBE PLAY
    # =====================================================

    {
        "type": "function",
        "function": {
            "name": "play_youtube",
            "description": (
                "Search YouTube for a video, song, topic, "
                "creator, or other content and play it."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": (
                            "The video, song, topic, creator, "
                            "or other content to search for."
                        ),
                    },
                },
                "required": [
                    "query",
                ],
            },
        },
    },

    # =====================================================
    # SPOTIFY CONTROL
    # =====================================================

    {
        "type": "function",
        "function": {
            "name": "spotify_control",
            "description": (
                "Control playback in the existing Spotify tab. "
                "Use only for direct Spotify playback commands."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": [
                            "play",
                            "pause",
                            "resume",
                            "next",
                            "previous",
                        ],
                        "description": (
                            "The Spotify playback action."
                        ),
                    },
                },
                "required": [
                    "action",
                ],
            },
        },
    },

    # =====================================================
    # YOUTUBE CONTROL
    # =====================================================

    {
        "type": "function",
        "function": {
            "name": "youtube_control",
            "description": (
                "Control the currently open YouTube video "
                "in the existing YouTube tab. "
                "Supports playback, volume, fullscreen, "
                "and exiting fullscreen."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": [
                            "play",
                            "pause",
                            "resume",
                            "stop",
                            "next",
                            "previous",
                            "volume_up",
                            "volume_down",
                            "fullscreen",
                            "exit_fullscreen",
                        ],
                        "description": (
                            "The YouTube control action."
                        ),
                    },
                },
                "required": [
                    "action",
                ],
            },
        },
    },

    # =====================================================
    # PC VOLUME UP
    # =====================================================

    {
        "type": "function",
        "function": {
            "name": "pc_volume_up",
            "description": (
                "Increase the Windows master volume."
            ),
            "parameters": {
                "type": "object",
                "properties": {},
            },
        },
    },

    # =====================================================
    # PC VOLUME DOWN
    # =====================================================

    {
        "type": "function",
        "function": {
            "name": "pc_volume_down",
            "description": (
                "Decrease the Windows master volume."
            ),
            "parameters": {
                "type": "object",
                "properties": {},
            },
        },
    },

    # =====================================================
    # PC MUTE
    # =====================================================

    {
        "type": "function",
        "function": {
            "name": "pc_volume_mute",
            "description": (
                "Mute the Windows master volume."
            ),
            "parameters": {
                "type": "object",
                "properties": {},
            },
        },
    },

    # =====================================================
    # PC UNMUTE
    # =====================================================

    {
        "type": "function",
        "function": {
            "name": "pc_volume_unmute",
            "description": (
                "Unmute the Windows master volume."
            ),
            "parameters": {
                "type": "object",
                "properties": {},
            },
        },
    },


{
    "type": "function",
    "function": {
        "name": "draft_email",
        "description": (
            "Create a Gmail draft without sending it. "
            "Use when the user asks to write, compose, "
            "or draft an email."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "recipient": {
                    "type": "string",
                    "description": "Recipient email address.",
                },
                "subject": {
                    "type": "string",
                    "description": "Email subject.",
                },
                "body": {
                    "type": "string",
                    "description": "Complete plain-text email body.",
                },
            },
            "required": [
                "recipient",
                "subject",
                "body",
            ],
        },
    },
},

{
    "type": "function",
    "function": {
        "name": "send_pending_email",
        "description": (
            "Send an email using Gmail. "
            "If a pending ALFRED draft exists, send that draft. "
            "If the user is asking to send a new email and there "
            "is no pending draft, provide the recipient, subject, "
            "and complete body and this tool will create and send "
            "the email. "
            "If the user asks to modify an existing pending email "
            "and send it, provide the complete updated recipient, "
            "subject, and body."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "recipient": {
                    "type": "string",
                    "description": (
                        "Recipient email address. Required when "
                        "sending a new email."
                    ),
                },
                "subject": {
                    "type": "string",
                    "description": (
                        "Complete email subject."
                    ),
                },
                "body": {
                    "type": "string",
                    "description": (
                        "Complete email body."
                    ),
                },
            },
            "required": [],
        },
    },
},

{
    "type": "function",
    "function": {
        "name": "save_to_notepad",
        "description": (
            "Save research or generated text to a plain-text "
            "file and open it in Windows Notepad."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "title": {
                    "type": "string",
                    "description": "Short title for the file.",
                },
                "content": {
                    "type": "string",
                    "description": "Complete text to save.",
                },
            },
            "required": [
                "title",
                "content",
            ],
        },
    },
},
{
    "type": "function",
    "function": {
        "name": "save_to_word",
        "description": (
            "Create a Microsoft Word .docx document from "
            "research or generated text and open it."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "title": {
                    "type": "string",
                    "description": "Document title.",
                },
                "content": {
                    "type": "string",
                    "description": "Complete text to put in the document.",
                },
            },
            "required": [
                "title",
                "content",
            ],
        },
    },
},

{
    "type": "function",
    "function": {
        "name": "research_youtube",
        "description": (
            "Search YouTube for a topic and return research "
            "text containing relevant video titles, channels, "
            "dates, descriptions, statistics, and URLs. "
            "Use this for research, not ordinary video playback."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": (
                        "The topic to research on YouTube."
                    ),
                },
                "max_results": {
                    "type": "integer",
                    "description": (
                        "Number of relevant videos to research. "
                        "Use 5 normally."
                    ),
                },
            },
            "required": [
                "query",
            ],
        },
    },
},


]
# =========================================================
# TOOL REGISTRY
# =========================================================

TOOL_FUNCTIONS = {

    "web_search":
        web_search,

    "find_and_open_file":
        find_and_open_file,

    "open_webpage":
        open_webpage,

    "open_application":
        open_application,

    "play_spotify":
        play_spotify,

    "play_youtube":
        play_youtube,

    "spotify_control":
        spotify_control,

    "youtube_control":
        youtube_control,

    "pc_volume_up":
        pc_volume_up,

    "pc_volume_down":
        pc_volume_down,

    "pc_volume_mute":
        pc_volume_mute,

    "pc_volume_unmute":
        pc_volume_unmute,

    "send_pending_email": 
        send_pending_email,
        
    "draft_email":
        draft_email,

    "save_to_notepad":
        save_to_notepad,

    "save_to_word":
        save_to_word,

    "research_youtube":
        research_youtube,    
}


# =========================================================
# EXECUTE TOOL
# =========================================================

def execute_tool(
    name: str,
    arguments,
):
    """
    Execute one approved local ALFRED tool.
    """

    function = TOOL_FUNCTIONS.get(
        name
    )

    if function is None:

        return (
            f"Unknown tool: {name}"
        )

    try:

        if isinstance(
            arguments,
            str,
        ):

            arguments = json.loads(
                arguments
            )

        if not isinstance(
            arguments,
            dict,
        ):

            arguments = {}

        result = function(
            **arguments
        )

        return str(
            result
        )

    except Exception as error:

        return (
            f"Tool '{name}' failed: "
            f"{error}"
        )

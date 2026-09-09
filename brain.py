import json
import os
import re
import requests

from dotenv import load_dotenv
from groq import Groq

from memory import (
    get_all_memories,
    save_memory,
    search_memories,
    format_memories,
)

from tools.ai_tools import (
    TOOL_DEFINITIONS,
    execute_tool,
)

from hub.device_executor import (
    execute_device_command,
)

# =========================================================
# DEVICE / LOCAL TOOL EXECUTION
# =========================================================

REMOTE_DEVICE_TOOLS = {
    "ping",

    "open_application",

    "open_url",
    "web_search",

    "pc_volume_up",
    "pc_volume_down",
    "pc_volume_mute",
    "pc_volume_unmute",

    "draft_email",
    "send_pending_email",

    "save_to_notepad",
    "save_to_word",

    "research_youtube",
}

# Browser-based media tools must stay local to the PC so they can use the
# existing Brave/CDP path instead of a remote device hub that can fail with
# WinError 1225 when the hub is unavailable or the network route is refused.


def execute_alfred_tool(
    tool_name,
    arguments,
):

    if tool_name in REMOTE_DEVICE_TOOLS:

        print(
            f"[ALFRED] Routing tool through device: "
            f"{tool_name}"
        )

        result = execute_device_command(
            tool_name,
            arguments,
        )

        if result.get(
            "success"
        ):

            return result.get(
                "result"
            )

        return (
            result.get(
                "error"
            )
            or
            "The device could not complete that request."
        )

    print(
        f"[ALFRED] Executing local tool: "
        f"{tool_name}"
    )

    return execute_tool(
        tool_name,
        arguments,
    )

# =========================================================
# CONFIGURATION
# =========================================================

# Modes:
#
# "cloud"  = cloud models only
# "local"  = local model only
# "hybrid" = cloud models, then local fallback
#
MODE = "hybrid"


# =========================================================
# CLOUD MODELS
# =========================================================

load_dotenv()

GROQ_API_KEY = os.getenv(
    "GROQ_API_KEY"
)

if not GROQ_API_KEY:

    raise RuntimeError(
        "GROQ_API_KEY is missing from .env"
    )


groq_client = Groq(
    api_key=GROQ_API_KEY
)


# Cheap / fast default model.
FAST_MODEL = "openai/gpt-oss-20b"

# Stronger model for difficult requests / fallback.
SMART_MODEL = "qwen/qwen3.6-27b"


# =========================================================
# LOCAL MODEL
# =========================================================

LOCAL_API_URL = (
    "http://127.0.0.1:8081/v1/chat/completions"
)

LOCAL_MODEL = (
    r"D:\ALFRED_SLM\models"
    r"\qwen2.5-1.5b-instruct-q4_k_m.gguf"
)

LOCAL_TIMEOUT = 60


# =========================================================
# TOKEN-SAVING CONFIGURATION
# =========================================================

# Keep this small. Older conversations do not need to be
# sent on every request.
MAX_HISTORY_MESSAGES = 6

# Keep memory retrieval small.
MAX_RELEVANT_MEMORIES = 5

# Maximum tool rounds.
MAX_TOOL_ROUNDS = 3

# Short normal response budget.
FAST_MAX_TOKENS = 180

# Slightly larger for the stronger model.
SMART_MAX_TOKENS = 320

# Local model is kept deliberately small.
LOCAL_MAX_TOKENS = 180


# =========================================================
# SYSTEM PROMPT
# =========================================================

SYSTEM_PROMPT = """
You are ALFRED, a private personal AI assistant.

Personality:
- Calm
- Intelligent
- Polite
- Highly competent
- Natural
- Concise
- Slightly witty when appropriate
- Refined British character
- Professional but friendly

Address the user as Sir.

==================================================
LANGUAGE
==================================================

English input:
Respond in English.

Roman Urdu input:
Respond in Roman Urdu.

Urdu-script input:
Respond in Urdu script.

Mixed Urdu-English:
Naturally use Roman Urdu mixed with English.

If speech transcription contains Devanagari but the
meaning is clearly Urdu, understand it as Urdu and reply
in Roman Urdu rather than Hindi.

==================================================
TOOLS
==================================================

Use an approved local tool when the user asks for an action
that tool can actually perform.

Never invent tools.

Never claim an action succeeded unless the tool result
indicates success.

==================================================
MEDIA
==================================================

YouTube requests MUST use play_youtube.

Spotify requests MUST use play_spotify.

Playback control requests MUST use the appropriate
playback-control tool.

Do not claim that something is playing unless the tool
actually succeeded.

Do not substitute another service after a tool failure
unless the user explicitly asks for an alternative.

==================================================
FILES
==================================================

When the user asks to find, locate, search for, or open
a file on the computer, use find_and_open_file.

Do not use open_application for a file request.

Never invent a file path.

Only claim that a file was opened when the file tool
reported success.

==================================================
WEB
==================================================

Use web_search for current or external information.

Use open_webpage for reading a specific webpage.

==================================================
GMAIL RULES
==================================================

When the user asks to write, compose, or draft an email,
use draft_email.

When the user explicitly asks to SEND an email:

- If there is an existing pending draft, use
  send_pending_email.
- If there is no pending draft, use send_pending_email with
  the recipient, subject, and complete email body.

If the user says "send it" after a draft was created, use
send_pending_email without changing the draft unless the
user explicitly requests changes.

If the user asks to modify a pending email and then send it,
use send_pending_email with the complete updated email.

Never claim an email was sent unless the tool reports success.

==================================================
GMAIL MULTI-TURN COMPOSITION
==================================================

Email requests may continue across multiple voice turns.

If the user starts an email request and the message is
incomplete, do not invent the missing sentence.

Keep the recipient, subject, and partial message in the
recent conversation context.

When the user provides the rest of the email in a later
turn, combine the previous request with the new turn.

Example:

User:
"Write a mail to crackly07 at gmail.com telling them that
your app is not..."

Assistant:
Ask briefly for the missing content.

User:
"working correctly on my phone."

Then create one complete email using both turns.

Do not discard the recipient from the previous turn.

==================================================
SPOKEN EMAIL ADDRESS
==================================================

Speech recognition may produce email addresses as spoken
words.

Understand common spoken forms:

" at " -> "@"
" at the " -> "@"
" dot " -> "."
" gmail dot com" -> "gmail.com"
" gmail com" -> "gmail.com"

Normalize the recipient before passing it to Gmail.

Do not invent an email address that was not present in the
user's speech.

==================================================
MEMORY
==================================================

Use supplied memory when relevant.

Do not invent memories.

==================================================
RESPONSE STYLE
==================================================

Keep normal answers concise.

Do not explain internal tool selection.

Do not mention model routing unless the user asks.

If a tool fails, briefly report the real failure.

==================================================
TOOL RESULT RULES
==================================================

Trust actual tool results.

If a tool reports success:
treat the action as successful.

If a tool reports failure:
report the failure.

Never pretend an action happened.

==================================================
YOUTUBE RESEARCH + DOCUMENTS
==================================================

When the user asks to research a topic on YouTube, use
research_youtube.

Do not use play_youtube for research requests unless the
user also asks to play a video.

After research_youtube returns its research text, summarize
the useful information before saving it.

If the user asks for Notepad, use save_to_notepad.

If the user asks for Word, Microsoft Word, or a DOCX file,
use save_to_word.

Do not claim a document was created unless the save tool
reports success.

Preserve source URLs in the research document.

==================================================
YOUTUBE RESEARCH OUTPUT
==================================================

When research_youtube succeeds, the research is stored
locally as the current research packet.

If the user asks to save that research to Word, call
save_to_word with the title only.

If the user asks to save that research to Notepad, call
save_to_notepad with the title only.

Do NOT copy the entire research packet into the tool
arguments.

Do NOT invent research content.

The document tools automatically read the latest research.

==================================================
IMPORTANT
==================================================

Do not waste tokens repeating the user's request.

Do not produce long explanations unless requested.
"""


# =========================================================
# CONVERSATION MEMORY
# =========================================================

messages = []



# =========================================================
# RELEVANT MEMORY
# =========================================================

def get_relevant_memories(
    user_input: str,
):
    try:

        memories = search_memories(
            user_input,
            limit=MAX_RELEVANT_MEMORIES,
        )

        if memories:
            return memories[
                :MAX_RELEVANT_MEMORIES
            ]

        all_memories = get_all_memories()

        if len(all_memories) <= 10:

            return all_memories[
                :MAX_RELEVANT_MEMORIES
            ]

        return []

    except Exception:

        return []


# =========================================================
# MEMORY EXTRACTION
# =========================================================

def should_extract_memory(
    user_input: str,
):

    text = (
        user_input
        .strip()
        .lower()
    )

    if len(text) < 12:
        return False

    indicators = (
        "my name is ",
        "i am ",
        "i'm ",
        "i live ",
        "i study ",
        "i work ",
        "i prefer ",
        "i like ",
        "i don't like ",
        "my project is ",
        "my goal is ",
        "remember that ",
        "i own ",
        "i have ",
    )

    return text.startswith(
        indicators
    )


def extract_memories(
    user_input: str,
):

    if not should_extract_memory(
        user_input
    ):
        return []

    prompt = f"""
Analyze this user message:

{user_input}

Determine whether it contains explicit long-term
information worth remembering.

Return ONLY valid JSON:

{{
    "memories": [
        {{
            "category": "category",
            "key": "key",
            "value": "value"
        }}
    ]
}}

If nothing should be remembered:

{{
    "memories": []
}}
"""

    request = [
        {
            "role": "system",
            "content": (
                "Return valid JSON only. "
                "Be extremely concise."
            ),
        },
        {
            "role": "user",
            "content": prompt,
        },
    ]

    try:

        # Use the cheap model for memory extraction.
        response = groq_client.chat.completions.create(
            model=FAST_MODEL,
            messages=request,
            temperature=0,
            max_tokens=120,
        )

        content = (
            response
            .choices[0]
            .message
            .content
            or ""
        ).strip()

        if content.startswith(
            "```"
        ):

            content = re.sub(
                r"^```(?:json)?\s*",
                "",
                content,
            )

            content = re.sub(
                r"\s*```$",
                "",
                content,
            ).strip()

        parsed = json.loads(
            content
        )

        return parsed.get(
            "memories",
            [],
        )

    except Exception:

        # Memory extraction should never break ALFRED.
        return []


# =========================================================
# SAVE MEMORY
# =========================================================

def remember_from_input(
    user_input: str,
):

    memories_to_save = extract_memories(
        user_input
    )

    if not isinstance(
        memories_to_save,
        list,
    ):
        return

    for memory in memories_to_save:

        if not isinstance(
            memory,
            dict,
        ):
            continue

        category = str(
            memory.get(
                "category",
                "",
            )
        ).strip()

        key = str(
            memory.get(
                "key",
                "",
            )
        ).strip()

        value = str(
            memory.get(
                "value",
                "",
            )
        ).strip()

        if (
            not category
            or not key
            or not value
        ):
            continue

        save_memory(
            category,
            key,
            value,
        )


# =========================================================
# BUILD CONTEXT
# =========================================================

def build_messages(
    user_input: str,
):

    relevant_memories = (
        get_relevant_memories(
            user_input
        )
    )

    memory_text = format_memories(
        relevant_memories
    )

    system_content = (
        SYSTEM_PROMPT
    )

    if memory_text.strip():

        system_content += (
            "\n\n"
            "CURRENT RELEVANT MEMORY:\n"
            + memory_text
        )

    request_messages = [
        {
            "role": "system",
            "content": system_content,
        }
    ]

    # Only keep a short recent history.
    request_messages.extend(
        messages[
            -MAX_HISTORY_MESSAGES:
        ]
    )

    request_messages.append(
        {
            "role": "user",
            "content": user_input,
        }
    )

    return request_messages


# =========================================================
# TOOL FILTERING
# =========================================================
def normalize_spoken_email(
    text: str,
) -> str:

    value = (
        text
        .strip()
        .lower()
    )

    replacements = {
        " at the ": "@",
        " at ": "@",
        " dot ": ".",
        " gmail dot com": "gmail.com",
        " gmail com": "gmail.com",
        " yahoo dot com": "yahoo.com",
        " outlook dot com": "outlook.com",
    }

    for old, new in replacements.items():
        value = value.replace(
            old,
            new,
        )

    value = value.replace(
        " ",
        "",
    )

    return value

def get_tool_definition(
    name: str,
):
    for definition in TOOL_DEFINITIONS:

        try:

            if (
                definition[
                    "function"
                ][
                    "name"
                ]
                == name
            ):

                return definition

        except Exception:

            continue

    return None


def select_tools_for_request(
    user_input: str,
):
    """
    Send only relevant tools to the cloud model.

    This is one of the main token-saving mechanisms.
    """

    text = (
        user_input
        .lower()
        .strip()
    )

    selected_names = set()

    # =====================================================
    # YOUTUBE
    # =====================================================

    youtube_words = (
        "youtube",
        "video",
        "watch",
        "fullscreen",
        "sidemen",
        "formula 1",
        "f1",
    )

    if any(
        word in text
        for word in youtube_words
    ):

        selected_names.update(
            [
                "play_youtube",
                "youtube_control",
            ]
        )

    # =====================================================
    # SPOTIFY
    # =====================================================

    spotify_words = (
        "spotify",
        "song",
        "track",
        "music",
        "album",
        "artist",
        "playlist",
    )

    if any(
        word in text
        for word in spotify_words
    ):

        selected_names.update(
            [
                "play_spotify",
                "spotify_control",
            ]
        )

    # =====================================================
    # FILES
    # =====================================================

    file_words = (
        "file",
        "pdf",
        "document",
        "resume",
        "report",
        "invoice",
        ".docx",
        ".xlsx",
        ".pptx",
        ".txt",
        ".py",
    )

    if any(
        word in text
        for word in file_words
    ):

        selected_names.add(
            "find_and_open_file"
        )

    # =====================================================
    # WINDOWS APPLICATIONS
    # =====================================================

    application_words = (
        "open app",
        "launch",
        "start",
        "open chrome",
        "open brave",
        "open notepad",
        "open calculator",
        "open vscode",
    )

    if any(
        word in text
        for word in application_words
    ):

        selected_names.add(
            "open_application"
        )

    # =====================================================
    # VOLUME
    # =====================================================

    volume_words = (
        "volume",
        "louder",
        "quieter",
        "mute",
        "unmute",
    )

    if any(
        word in text
        for word in volume_words
    ):

        selected_names.update(
            [
                "pc_volume_up",
                "pc_volume_down",
                "pc_volume_mute",
                "pc_volume_unmute",
            ]
        )

    # =====================================================
    # WEB
    # =====================================================

    web_phrases = (
    "search the web",
    "search online",
    "search google",
    "look this up online",
    "look it up online",
    "find online",
    "browse the web",
    "latest news",
    "current news",
    "current information",
    "current price",
    "website for",
)

    if any(
        word in text
        for word in web_phrases
    ):

        selected_names.update(
            [
                "web_search",
                "open_webpage",
            ]
        )

    # =====================================================
    # GMAIL
    # =====================================================

    gmail_words = (
        "email",
        "e-mail",
        "gmail",
        "mail",
        "send an email",
        "send a mail",
        "write an email",
        "write a mail",
        "write on mail",
        "write me a mail",
        "write me an email",
        "draft an email",
        "compose an email",
        "send it",
        "send the email",
        "send that email",
        "send that",
        "tell them that",
        "telling them that",
        "after best regards",
        "add my name",
        "change the email",
        "change the message",
    )

    if any(
        word in text
        for word in gmail_words
    ):

        selected_names.update(
            [
                "draft_email",
                "send_pending_email",
            ]
        )
    # =====================================================
    # GMAIL HAS PRIORITY OVER GENERIC WEB TOOLS
    # =====================================================

    if "draft_email" in selected_names or "send_pending_email" in selected_names:
        selected_names.discard(
            "web_search"
    )

        selected_names.discard(
            "open_webpage"
    )

    
    # =====================================================
    # YOUTUBE RESEARCH
    # =====================================================

    research_words = (
        "research",
        "information",
        "details",
        "detail",
        "learn about",
        "explain",
        "summarize",
        "summary",
        "analyse",
        "analyze",
    )

    youtube_requested = any(
        word in text
        for word in (
            "youtube",
            "video",
            "videos",
        )
    )

    research_requested = any(
        word in text
        for word in research_words
    )

    if youtube_requested and research_requested:

        selected_names.discard(
            "play_youtube"
        )

        selected_names.discard(
            "youtube_control"
        )

        selected_names.add(
            "research_youtube"
        )  
    # =====================================================
    # RESEARCH + DOCUMENT OUTPUT
    # =====================================================

    is_research_request = any(
        phrase in text
        for phrase in (
            "research",
            "research on",
            "research about",
            "find information",
            "gather information",
            "collect information",
            "details about",
            "learn about",
        )
    )

    if is_research_request:

        # YouTube research
        selected_names.add(
            "research_youtube"
        )

        # General web research
        selected_names.update(
            [
                "web_search",
                "open_webpage",
            ]
        )
        if "research_youtube" in selected_names:
            selected_names.discard(
                "play_youtube"
            )

            selected_names.discard(
                "youtube_control"
            )

        # Output destination
        if (
           "word" in text
            or ".docx" in text
            or "microsoft word" in text
            or "word document" in text
        ):
            selected_names.add(
                "save_to_word"
            )

        elif "notepad" in text:
            selected_names.add(
                "save_to_notepad"
            )
    # =====================================================
    # GMAIL HAS PRIORITY OVER GENERIC WEB
    # =====================================================

    if (
        "draft_email" in selected_names
        or "send_pending_email" in selected_names
    ):
        selected_names.discard(
            "web_search"
        )

        selected_names.discard(
            "open_webpage"
        )

    # =====================================================
    # RETURN ONLY RELEVANT TOOLS
    # =====================================================

    if not selected_names:
        return []

    return [
        definition
        for definition in TOOL_DEFINITIONS
        if definition.get(
            "function",
            {},
        ).get(
            "name"
        ) in selected_names
    ]
# =========================================================
# COMPLEXITY ROUTER
# =========================================================

def should_use_smart_model(
    user_input: str,
):
    """
    Heuristic router.

    Most ALFRED requests stay on the cheap model.
    Only clearly complex requests go to Qwen 27B.
    """

    text = (
        user_input
        .lower()
        .strip()
    )

    complex_signals = (
        "explain why",
        "compare",
        "analyze",
        "analyse",
        "debug",
        "design",
        "architect",
        "write code",
        "rewrite code",
        "review code",
        "plan",
        "step by step",
        "deeply",
        "detailed explanation",
        "research",
        "calculate",
        "derive",
        "reason",
        "pros and cons",
        "tradeoff",
        "trade-off",
    )

    return any(
        signal in text
        for signal in complex_signals
    )


# =========================================================
# LOCAL CHAT
# =========================================================

def local_chat(
    request_messages,
    tools=None,
    tool_choice="auto",
    temperature=0.3,
    max_tokens=LOCAL_MAX_TOKENS,
):

    payload = {
        "model": LOCAL_MODEL,
        "messages": request_messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }

    if tools:

        payload["tools"] = tools
        payload["tool_choice"] = tool_choice

    response = requests.post(
        LOCAL_API_URL,
        json=payload,
        timeout=LOCAL_TIMEOUT,
    )

    response.raise_for_status()

    return response.json()


# =========================================================
# CLOUD CHAT
# =========================================================

def cloud_chat(
    model,
    request_messages,
    tools=None,
    tool_choice="auto",
    temperature=0.3,
    max_tokens=180,
):
    kwargs = {
        "model": model,
        "messages": request_messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }

    # Hide reasoning where supported.
    if model == SMART_MODEL:
        kwargs["reasoning_effort"] = "none"
        kwargs["reasoning_format"] = "hidden"

    if tools:
        kwargs["tools"] = tools
        kwargs["tool_choice"] = tool_choice

    return groq_client.chat.completions.create(
        **kwargs
    )
# =========================================================
# NORMALISE TOOL CALLS
# =========================================================

def normalise_tool_calls(
    message,
):

    raw_calls = (
        message.get(
            "tool_calls",
            [],
        )
        if isinstance(
            message,
            dict,
        )
        else getattr(
            message,
            "tool_calls",
            None,
        )
    ) or []

    calls = []

    for call in raw_calls:

        if isinstance(
            call,
            dict,
        ):

            function = call.get(
                "function",
                {},
            )

            calls.append(
                {
                    "id": call.get(
                        "id"
                    ),
                    "name": function.get(
                        "name",
                        "",
                    ),
                    "arguments": function.get(
                        "arguments",
                        "{}",
                    ),
                }
            )

        else:

            calls.append(
                {
                    "id": call.id,
                    "name": call.function.name,
                    "arguments": call.function.arguments,
                }
            )

    return calls


# =========================================================
# TOOL MESSAGE
# =========================================================

def append_tool_call_message(
    request_messages,
    message,
    tool_calls,
):

    content = (
        message.get(
            "content",
            "",
        )
        if isinstance(
            message,
            dict,
        )
        else getattr(
            message,
            "content",
            "",
        )
    ) or ""

    request_messages.append(
        {
            "role": "assistant",
            "content": content,
            "tool_calls": [
                {
                    "id": call["id"],
                    "type": "function",
                    "function": {
                        "name": call["name"],
                        "arguments": call["arguments"],
                    },
                }
                for call in tool_calls
            ],
        }
    )


# =========================================================
# ASK BRAIN
# =========================================================

def ask_brain(
    user_input: str,
) -> str:

    request_messages = build_messages(
        user_input
    )

    # -----------------------------------------------------
    # Local-only mode
    # -----------------------------------------------------

    if MODE == "local":

        try:

            return run_local_brain(
                user_input,
                request_messages,
            )

        except Exception as error:

            print(
                "[ALFRED LOCAL ERROR]",
                error,
            )

            return (
                "My local AI system encountered "
                "an error, Sir."
            )

    # -----------------------------------------------------
    # Cloud / hybrid
    # -----------------------------------------------------

    if MODE not in {
        "cloud",
        "hybrid",
    }:

        return (
            "ALFRED's brain mode is configured incorrectly, Sir."
        )

    try:

        return run_cloud_brain(
            user_input,
            request_messages,
        )

    except Exception as error:

        print(
            "[ALFRED CLOUD ERROR]",
            error,
        )

        if MODE == "cloud":

            return (
                "I couldn't reach my cloud AI "
                "service, Sir."
            )

        print(
            "[ALFRED] Cloud models unavailable. "
            "Falling back to local SLM."
        )

        try:

            return run_local_brain(
                user_input,
                request_messages,
            )

        except Exception as local_error:

            print(
                "[ALFRED LOCAL ERROR]",
                local_error,
            )

            return (
                "I'm having trouble with both "
                "my cloud and local AI systems, Sir."
            )


# =========================================================
# CLOUD BRAIN
# =========================================================

def run_cloud_brain(
    user_input,
    request_messages,
):

    tools = select_tools_for_request(
        user_input
    )

    # -----------------------------------------------------
    # Decide the first cloud model.
    # -----------------------------------------------------

    if should_use_smart_model(
        user_input
    ):

        primary_model = SMART_MODEL

    else:

        primary_model = FAST_MODEL

    fallback_model = (
        SMART_MODEL
        if primary_model == FAST_MODEL
        else FAST_MODEL
    )


    # -----------------------------------------------------
    # First model
    # -----------------------------------------------------

    try:

        return run_model(
            model=primary_model,
            fallback_model=fallback_model,
            user_input=user_input,
            request_messages=request_messages,
            tools=tools,
        )

    except Exception as error:

        print(
            f"[ALFRED] {primary_model} failed:"
        )

        print(
            error
        )

        # Try the other cloud model.
        try:

            print(
                f"[ALFRED] Trying {fallback_model}..."
            )

            result = run_model_once(
                model=fallback_model,
                user_input=user_input,
                request_messages=request_messages,
                tools=tools,
            )

            last_cloud_model = fallback_model

            return result

        except Exception as fallback_error:

            print(
                f"[ALFRED] {fallback_model} failed:"
            )

            print(
                fallback_error
            )

            raise


# =========================================================
# GENERIC CLOUD MODEL RUNNER
# =========================================================

def run_model(
    model,
    fallback_model,
    user_input,
    request_messages,
    tools,
):
    try:
        return run_model_once(
            model=model,
            user_input=user_input,
            request_messages=request_messages,
            tools=tools,
        )

    except Exception as error:

        if not is_rate_limit_error(error):
            raise

        print(
            f"[ALFRED] {model} hit a rate limit."
        )

        print(
            f"[ALFRED] Switching to {fallback_model}."
        )

        return run_model_once(
            model=fallback_model,
            user_input=user_input,
            request_messages=request_messages,
            tools=tools,
        )


# =========================================================
# RATE-LIMIT DETECTION
# =========================================================

def is_rate_limit_error(
    error,
):

    text = str(
        error
    ).lower()

    return (
        "429" in text
        or "rate limit" in text
        or "rate_limit_exceeded" in text
        or "tokens per day" in text
        or "tokens per minute" in text
    )


# =========================================================
# RUN ONE CLOUD MODEL
# =========================================================

def run_model_once(
    model,
    user_input,
    request_messages,
    tools,
):

    for _ in range(
        MAX_TOOL_ROUNDS
    ):

        response = cloud_chat(
            model=model,
            request_messages=request_messages,
            tools=tools,
            tool_choice="auto",
            temperature=0.3,
            max_tokens=(
                SMART_MAX_TOKENS
                if model == SMART_MODEL
                else FAST_MAX_TOKENS
            ),
        )

        message = response.choices[0].message

        tool_calls = (
            message.tool_calls
            or []
        )

        # -------------------------------------------------
        # Normal answer
        # -------------------------------------------------

        if not tool_calls:

            answer = (
                message.content
                or ""
            ).strip()

            if not answer:

                answer = (
                    "I couldn't formulate a response, Sir."
                )

            save_conversation(
                user_input,
                answer,
            )

            return answer

        # -------------------------------------------------
        # Assistant tool call message
        # -------------------------------------------------

        normalized_calls = normalise_tool_calls(
            message
        )

        append_tool_call_message(
            request_messages,
            message,
            normalized_calls,
        )

        # -------------------------------------------------
        # Execute tools
        # -------------------------------------------------

        for call in normalized_calls:

            name = call[
                "name"
            ]

            try:

                arguments = json.loads(
                    call[
                        "arguments"
                    ]
                )

            except Exception:

                arguments = {}

            print(
                f"[{model} TOOL] {name}"
            )

            result = execute_alfred_tool(
                name,
                arguments,
            )

            print(
                f"[{model} TOOL RESULT] {result}"
            )

            request_messages.append(
                {
                    "role": "tool",
                    "tool_call_id": call[
                        "id"
                    ],
                    "content": str(
                        result
                    ),
                }
            )

    return (
        "I wasn't able to complete that request, Sir."
    )


# =========================================================
# LOCAL BRAIN
# =========================================================

def run_local_brain(
    user_input,
    request_messages,
):

    tools = select_tools_for_request(
        user_input
    )

    for _ in range(
        MAX_TOOL_ROUNDS
    ):

        data = local_chat(
            request_messages,
            tools=tools,
            tool_choice="auto",
            temperature=0.2,
            max_tokens=LOCAL_MAX_TOKENS,
        )

        message = data[
            "choices"
        ][
            0
        ][
            "message"
        ]

        tool_calls = normalise_tool_calls(
            message
        )

        # -------------------------------------------------
        # Normal answer
        # -------------------------------------------------

        if not tool_calls:

            answer = (
                message.get(
                    "content",
                    "",
                )
                or ""
            ).strip()

            if not answer:

                answer = (
                    "I couldn't formulate a response, Sir."
                )

            save_conversation(
                user_input,
                answer,
            )

            return answer

        # -------------------------------------------------
        # Assistant tool call
        # -------------------------------------------------

        append_tool_call_message(
            request_messages,
            message,
            tool_calls,
        )

        # -------------------------------------------------
        # Execute
        # -------------------------------------------------

        for call in tool_calls:

            name = call[
                "name"
            ]

            try:

                arguments = json.loads(
                    call[
                        "arguments"
                    ]
                )

            except Exception:

                arguments = {}

            print(
                f"[LOCAL ALFRED TOOL] {name}"
            )

            result = execute_alfred_tool(
                name,
                arguments,
            )

            print(
                f"[LOCAL ALFRED TOOL RESULT] {result}"
            )

            request_messages.append(
                {
                    "role": "tool",
                    "tool_call_id": call[
                        "id"
                    ],
                    "content": str(
                        result
                    ),
                }
            )

    return (
        "I wasn't able to complete that request, Sir."
    )


# =========================================================
# SAVE CONVERSATION
# =========================================================

def save_conversation(
    user_input,
    answer,
):

    messages.append(
        {
            "role": "user",
            "content": user_input,
        }
    )

    messages.append(
        {
            "role": "assistant",
            "content": answer,
        }
    )

    # Keep memory extraction deliberately limited.
    remember_from_input(
        user_input
    )

import json
import os

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


# =========================================================
# CONFIGURATION
# =========================================================

# Options:
#   "cloud"  = Groq only
#   "local"  = local Qwen only
#   "hybrid" = Groq first, local fallback
#
# Recommended:
MODE = "hybrid"


# =========================================================
# CLOUD MODEL
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

CLOUD_MODEL = "qwen/qwen3.6-27b"


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
# GENERAL CONFIG
# =========================================================

MAX_TOOL_ROUNDS = 5
MAX_HISTORY_MESSAGES = 12


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
meaning is clearly Urdu, understand it as Urdu and
reply in Roman Urdu rather than Hindi.

==================================================
TOOLS
==================================================

You have approved local tools.

Use tools when the user asks you to perform an action
that a tool can perform.

Available capabilities include:

- Open approved Windows applications.
- Spotify playback.
- YouTube playback.
- Spotify controls.
- YouTube controls.
- Windows master volume.
- Web search.
- Webpage reading.
- File search/listing.
- Folder creation.
- Opening approved files/folders.
- System information.

Only use approved tools.

Never invent a tool.

Never claim a tool action succeeded unless the tool
result indicates success.

==================================================
WEB
==================================================

Use web_search for current or external information.

Use open_webpage when a specific webpage needs to be
read.

For detailed web research:

1. Search first.
2. Examine the results.
3. Open the relevant source when necessary.
4. Answer using the retrieved information.

==================================================
MEMORY
==================================================

Use supplied long-term memory when relevant.

Do not invent memories.

==================================================
SAFETY
==================================================

Do not execute arbitrary shell commands.

Do not invent successful actions.

Keep normal answers concise.

==================================================
MEDIA COMMAND RULES
==================================================

When the user asks to play, watch, search for, or find
something on YouTube, ALWAYS use the play_youtube tool.

Examples:

"play something from Sidemen"
"play Formula 1 FP1 highlights"
"watch the new Grand Prix highlights"
"find Outdoor Boys on YouTube"

These are YouTube tool requests.

Do NOT respond as if the video is playing unless the
play_youtube tool was actually called and returned a
successful result.

If the tool fails, report the failure.

Do not invent that a video was played.

For Spotify:

"play [song] on Spotify"
"play [artist] on Spotify"
"listen to [song] on Spotify"

must use play_spotify.

Never claim that Spotify or YouTube is playing unless the
corresponding tool actually returned a successful result.

==================================================
FILE COMMAND RULES
==================================================

When the user asks to find, locate, search for, or open a
file on the computer, use the find_and_open_file tool.

Examples:

"Find my resume."
"Open invoice.pdf."
"Find project.py."
"Open the report."
"Where is my presentation?"
"Find the latest budget file."

Do not claim a file was found or opened unless the tool
actually returned a result.

Use the user's filename or identifying words as the search
query.

Do not invent file paths.




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
            limit=10,
        )

        if memories:
            return memories

        all_memories = get_all_memories()

        if len(all_memories) <= 20:
            return all_memories

        return []

    except Exception:

        return []


# =========================================================
# MEMORY EXTRACTION
# =========================================================

def extract_memories(
    user_input: str,
):
    """
    Only call the model for messages that are likely
    to contain a persistent personal fact.
    """

    text = user_input.strip().lower()

    if len(text) < 12:
        return []

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
    )

    if not text.startswith(indicators):
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

    try:

        # Use cloud for memory extraction in hybrid/cloud
        # because it is faster and more reliable.
        if MODE in ("cloud", "hybrid"):

            response = groq_client.chat.completions.create(
                model=CLOUD_MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "Return valid JSON only."
                        ),
                    },
                    {
                        "role": "user",
                        "content": prompt,
                    },
                ],
                temperature=0,
                reasoning_effort="none",
                reasoning_format="hidden",
            )

            content = (
                response
                .choices[0]
                .message
                .content
                .strip()
            )

        else:

            data = local_chat(
                [
                    {
                        "role": "system",
                        "content": (
                            "Return valid JSON only."
                        ),
                    },
                    {
                        "role": "user",
                        "content": prompt,
                    },
                ],
                temperature=0,
                max_tokens=180,
            )

            content = (
                data["choices"][0]["message"]
                .get("content", "")
                .strip()
            )

        if content.startswith("```"):

            content = content.replace(
                "```json",
                "",
            )

            content = content.replace(
                "```",
                "",
            ).strip()

        parsed = json.loads(
            content
        )

        return parsed.get(
            "memories",
            [],
        )

    except Exception:

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
        + "\n\n"
        + "CURRENT RELEVANT MEMORY:\n\n"
        + memory_text
    )

    request_messages = [
        {
            "role": "system",
            "content": system_content,
        }
    ]

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
# LOCAL CHAT
# =========================================================

def local_chat(
    request_messages,
    tools=None,
    tool_choice="auto",
    temperature=0.3,
    max_tokens=180,
):
    payload = {
        "model": LOCAL_MODEL,
        "messages": request_messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }

    if tools is not None:
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
    request_messages,
    tools=None,
    tool_choice="auto",
    temperature=0.5,
    max_tokens=300,
):
    kwargs = {
        "model": CLOUD_MODEL,
        "messages": request_messages,
        "temperature": temperature,
        "reasoning_effort": "none",
        "reasoning_format": "hidden",
    }

    if tools is not None:
        kwargs["tools"] = tools
        kwargs["tool_choice"] = tool_choice

    response = groq_client.chat.completions.create(
        **kwargs
    )

    return response


# =========================================================
# ADD ASSISTANT TOOL CALL MESSAGE
# =========================================================

def append_assistant_tool_message(
    request_messages,
    message,
    tool_calls,
):
    request_messages.append(
        {
            "role": "assistant",
            "content": (
                message.get("content", "")
                if isinstance(message, dict)
                else getattr(
                    message,
                    "content",
                    "",
                )
            ) or "",
            "tool_calls": [
                {
                    "id": (
                        call.get("id")
                        if isinstance(call, dict)
                        else call.id
                    ),
                    "type": "function",
                    "function": {
                        "name": (
                            call["function"]["name"]
                            if isinstance(call, dict)
                            else call.function.name
                        ),
                        "arguments": (
                            call["function"]["arguments"]
                            if isinstance(call, dict)
                            else call.function.arguments
                        ),
                    },
                }
                for call in tool_calls
            ],
        }
    )


# =========================================================
# NORMALISE TOOL CALLS
# =========================================================

def normalise_tool_calls(
    message,
):
    """
    Convert cloud/local tool calls to one common structure.
    """

    raw_calls = (
        message.get("tool_calls", [])
        if isinstance(message, dict)
        else getattr(
            message,
            "tool_calls",
            None,
        )
    ) or []

    calls = []

    for call in raw_calls:

        if isinstance(call, dict):

            function = call.get(
                "function",
                {},
            )

            calls.append(
                {
                    "id": call.get("id"),
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
# ASK BRAIN
# =========================================================

def ask_brain(
    user_input: str,
) -> str:

    request_messages = build_messages(
        user_input
    )

    # =====================================================
    # HYBRID / CLOUD
    # =====================================================

    if MODE in (
        "cloud",
        "hybrid",
    ):

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
                "[ALFRED] Falling back to local SLM."
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

    # =====================================================
    # LOCAL ONLY
    # =====================================================

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

    return (
        "ALFRED's brain mode is configured incorrectly, Sir."
    )


# =========================================================
# CLOUD BRAIN
# =========================================================

def run_cloud_brain(
    user_input,
    request_messages,
):

    for _ in range(
        MAX_TOOL_ROUNDS
    ):

        response = cloud_chat(
            request_messages,
            tools=TOOL_DEFINITIONS,
            tool_choice="auto",
            temperature=0.5,
            max_tokens=300,
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
        # Build clean assistant tool message
        # -------------------------------------------------

        request_messages.append(
            {
                "role": "assistant",
                "content": (
                    message.content
                    or ""
                ),
                "tool_calls": [
                    {
                        "id": call.id,
                        "type": "function",
                        "function": {
                            "name": call.function.name,
                            "arguments": call.function.arguments,
                        },
                    }
                    for call in tool_calls
                ],
            }
        )

        # -------------------------------------------------
        # Execute tools
        # -------------------------------------------------

        for call in tool_calls:

            name = call.function.name
            raw_arguments = call.function.arguments

            try:

                arguments = json.loads(
                    raw_arguments
                )

            except Exception:

                arguments = {}

            print(
                f"[CLOUD ALFRED TOOL] {name}"
            )

            result = execute_tool(
                name,
                arguments,
            )

            print(
                f"[CLOUD ALFRED TOOL RESULT] {result}"
            )

            request_messages.append(
                {
                    "role": "tool",
                    "tool_call_id": call.id,
                    "content": str(result),
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

    for _ in range(
        MAX_TOOL_ROUNDS
    ):

        data = local_chat(
            request_messages,
            tools=TOOL_DEFINITIONS,
            tool_choice="auto",
            temperature=0.3,
            max_tokens=180,
        )

        message = data[
            "choices"
        ][0][
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

        request_messages.append(
            {
                "role": "assistant",
                "content": (
                    message.get(
                        "content",
                        "",
                    )
                    or ""
                ),
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

        # -------------------------------------------------
        # Execute
        # -------------------------------------------------

        for call in tool_calls:

            name = call["name"]

            try:

                arguments = json.loads(
                    call["arguments"]
                )

            except Exception:

                arguments = {}

            print(
                f"[LOCAL ALFRED TOOL] {name}"
            )

            result = execute_tool(
                name,
                arguments,
            )

            print(
                f"[LOCAL ALFRED TOOL RESULT] {result}"
            )

            request_messages.append(
                {
                    "role": "tool",
                    "tool_call_id": call["id"],
                    "content": str(result),
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

    # Memory extraction is deliberately limited to
    # messages that look like explicit personal facts.
    remember_from_input(
        user_input
    )

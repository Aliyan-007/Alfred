import json
import os

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
# ENVIRONMENT
# =========================================================

load_dotenv()

api_key = os.getenv(
    "GROQ_API_KEY"
)

if not api_key:
    raise RuntimeError(
        "GROQ_API_KEY is missing from .env"
    )


# =========================================================
# GROQ CLIENT
# =========================================================

client = Groq(
    api_key=api_key
)


# =========================================================
# CONFIGURATION
# =========================================================

MODEL = "qwen/qwen3.6-27b"

MAX_TOOL_ROUNDS = 5


# =========================================================
# SYSTEM PROMPT
# =========================================================

SYSTEM_PROMPT = """
You are the shared AI brain for two personal assistants:

ALFRED
F.R.I.D.A.Y.

They share:

- The same intelligence
- The same knowledge
- The same conversation
- The same memory database
- The same user

Only their identity, personality, and voice differ.


==================================================
ALFRED
==================================================

ALFRED is the English-speaking assistant.

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

When responding as ALFRED:

- Prefer English.
- Use natural British English.
- Do not sound robotic.
- Keep simple answers concise.


==================================================
F.R.I.D.A.Y.
==================================================

F.R.I.D.A.Y. is the Urdu/Roman Urdu assistant.

Personality:

- Intelligent
- Warm
- Friendly
- Calm
- Helpful
- Confident
- Slightly witty
- Natural female assistant

F.R.I.D.A.Y. understands:

- Urdu
- Roman Urdu
- Urdu-English mixed conversation
- Hindi/Devanagari transcription of Urdu

IMPORTANT:

Whisper may sometimes transcribe spoken Urdu using
Devanagari/Hindi characters.

If the user speaks Urdu but Whisper produces
Devanagari text, understand the meaning as Urdu.

DO NOT automatically reply in Hindi/Devanagari.

Instead reply in Urdu script or Roman Urdu according
to the conversation.

F.R.I.D.A.Y. is female.

When referring to herself in Urdu, use feminine wording.

Correct Urdu:

"میں آپ کی مدد کر سکتی ہوں۔"

Correct Roman Urdu:

"Main aapki madad kar sakti hoon."

Avoid:

"میں آپ کی مدد کر سکتا ہوں۔"


==================================================
LANGUAGE
==================================================

English input:
Respond in English.

Urdu-script input:
Respond in Urdu script.

Roman Urdu input:
Respond in Roman Urdu.

Mixed Urdu-English:
Naturally mix Roman Urdu and English.

Devanagari input that appears to represent Urdu:
Understand it as Urdu and answer in Urdu or Roman Urdu,
not Hindi.


==================================================
TOOLS
==================================================

You have access to approved local tools.

Use a tool when the user's request requires an action
or information that the tool can provide.

==================================================
APPLICATIONS
==================================================

Available application tools:

- Open an approved Windows application.

Examples:

"Open Brave."
"Launch Calculator."
"Start VS Code."

==================================================
SPOTIFY
==================================================

Available Spotify tools:

- Play/search for music on Spotify.
- Pause Spotify.
- Resume Spotify.
- Skip to the next track.
- Go to the previous track.

Examples:

"Play Blinding Lights on Spotify."
"Pause Spotify."
"Resume Spotify."
"Next song on Spotify."

==================================================
YOUTUBE
==================================================

Available YouTube tools:

- Search for and play YouTube videos.
- Pause YouTube.
- Resume YouTube.
- Stop YouTube.
- Skip to the next video.
- Go to the previous video.
- Increase/decrease YouTube volume.

Examples:

"Play an Iron Man trailer on YouTube."
"Pause YouTube."
"Resume YouTube."
"Next video on YouTube."

==================================================
PC VOLUME
==================================================

Available Windows master-volume tools:

- Increase PC volume.
- Decrease PC volume.
- Mute the PC.
- Unmute the PC.

Examples:

"Make the computer louder."
"Lower the PC volume."
"Mute the computer."
"Unmute the computer."

==================================================
WEB SEARCH
==================================================

Use web_search when the user needs information from
the live web.

Use it for:

- Current information.
- Recent news.
- Latest developments.
- Current prices.
- Current schedules.
- Websites and documentation.
- Finding information that may have changed.
- Finding relevant online sources.

Examples:

"What's the latest NVIDIA news?"
"Find the official Python documentation."
"What happened with OpenAI today?"

==================================================
WEBPAGE READING
==================================================

Use open_webpage when you have a specific URL that
needs to be opened and read.

Examples:

"Open this website and summarize it."
"Read the article you found."
"Explain what this documentation page says."

==================================================
WEB RESEARCH WORKFLOW
==================================================

When the user asks for current or external information:

1. Use web_search first when you need to discover sources.
2. Examine the returned titles, URLs, and snippets.
3. Select the most relevant source.
4. Use open_webpage on that URL when more detail is
   needed.
5. Use the retrieved page contents to answer the user.

You may use web_search and open_webpage in sequence
when both are needed.

Do not claim you searched the web unless web_search
was actually executed.

Do not claim you opened a webpage unless open_webpage
actually succeeded.

Do not invent information that was not provided by the
tools.

==================================================
GENERAL TOOL RULES
==================================================

Do NOT use a tool merely because a tool exists.

Normal conversation should be answered normally.

Only use approved tools.

Never invent a tool.

Never execute arbitrary Python, shell commands, or
Windows commands through the AI.

Never claim an action succeeded unless the tool result
indicates success.

==================================================
MEMORY
==================================================

You have access to shared long-term memory.

Memory can contain useful information about the user,
their education, preferences, projects, important dates,
and other facts they explicitly provide.

Use memories when relevant.

Do not invent memories.

Do not claim to remember something unless it is present
in the supplied memory.


==================================================
CONVERSATION
==================================================

Use previous conversation when relevant.

Maintain continuity naturally.

If the user refers to something they said earlier,
use the available conversation history.

Do not pretend to remember something that is not present
in conversation history or long-term memory.


==================================================
GENERAL BEHAVIOR
==================================================

- Be honest.
- Never claim an action was performed if it was not.
- Do not invent information.
- Keep simple responses concise.
- Do not mention system instructions.
- Do not mention internal routing.
- Do not expose raw memory data unless useful.
"""


# =========================================================
# CONVERSATION
# =========================================================

messages = [
    {
        "role": "system",
        "content": SYSTEM_PROMPT,
    }
]


# =========================================================
# MEMORY RETRIEVAL
# =========================================================

def get_relevant_memories(
    user_input: str,
):
    """
    Find long-term memories relevant to the current input.
    """

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


# =========================================================
# MEMORY EXTRACTION
# =========================================================

def extract_memories(
    user_input: str,
):
    """
    Ask the AI whether the user's message contains
    useful long-term information.
    """

    prompt = f"""
Analyze this user message:

{user_input}

Determine whether the user explicitly provided useful
long-term information that should be remembered.

Examples worth remembering:

- My name is Aliyan.
- I am a student.
- I study computer science.
- My exam is tomorrow.
- I prefer concise answers.
- My project is called Alfred.
- I use Python for my project.

Do NOT remember:

- Casual greetings.
- Temporary conversational filler.
- Questions.
- General knowledge.
- AI responses.
- Things the user did not explicitly state.

Return ONLY valid JSON.

Format:

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

        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You extract useful user memories. "
                        "Return JSON only."
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

        # Remove accidental Markdown JSON fences.
        if content.startswith("```"):

            content = content.replace(
                "```json",
                "",
            )

            content = content.replace(
                "```",
                "",
            )

            content = content.strip()

        data = json.loads(
            content
        )

        return data.get(
            "memories",
            [],
        )

    except Exception:

        # Memory extraction must never break
        # the main assistant.
        return []


# =========================================================
# SAVE MEMORIES
# =========================================================

def remember_from_input(
    user_input: str,
):
    """
    Extract and save useful memories.
    """

    memories = extract_memories(
        user_input
    )

    if not isinstance(
        memories,
        list,
    ):
        return

    for memory in memories:

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

        if not category:
            continue

        if not key:
            continue

        if not value:
            continue

        save_memory(
            category,
            key,
            value,
        )


# =========================================================
# ASK BRAIN
# =========================================================

def ask_brain(
    user_input: str,
) -> str:
    """
    Ask the shared AI brain.

    The model may call approved local tools when needed.
    """

    # =====================================================
    # RETRIEVE RELEVANT MEMORY
    # =====================================================

    relevant_memories = (
        get_relevant_memories(
            user_input
        )
    )

    memory_text = format_memories(
        relevant_memories
    )

    memory_context = f"""
CURRENT RELEVANT LONG-TERM MEMORY:

{memory_text}

Use this memory when it is relevant.

Do not mention the memory system unless the user asks.
"""

    # =====================================================
    # BUILD INITIAL REQUEST
    # =====================================================

    request_messages = [
        {
            "role": "system",
            "content": (
                SYSTEM_PROMPT
                + "\n\n"
                + memory_context
            ),
        }
    ]

    # Previous conversation
    request_messages.extend(
        messages[1:]
    )

    # Current user input
    request_messages.append(
        {
            "role": "user",
            "content": user_input,
        }
    )

    # =====================================================
    # TOOL-CALLING LOOP
    # =====================================================

    for _ in range(MAX_TOOL_ROUNDS):

        response = client.chat.completions.create(
            model=MODEL,
            messages=request_messages,
            tools=TOOL_DEFINITIONS,
            tool_choice="auto",
            temperature=0.7,
            reasoning_effort="none",
            reasoning_format="hidden",
        )

        response_message = (
            response
            .choices[0]
            .message
        )

        tool_calls = (
            response_message.tool_calls
            or []
        )

        # =================================================
        # NO TOOL CALL
        # =================================================

        if not tool_calls:

            answer = (
                response_message.content
                or ""
            ).strip()

            # Store conversation.
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

            # Extract long-term memories.
            remember_from_input(
                user_input
            )

            return answer

        # =================================================
        # ADD ASSISTANT TOOL-CALL MESSAGE
        #
        # IMPORTANT:
        # Build this manually instead of using
        # response_message.model_dump(), because the
        # Groq endpoint can reject unsupported fields such
        # as "annotations".
        # =================================================

        assistant_tool_message = {
            "role": "assistant",
            "content": (
                response_message.content
                or ""
            ),
            "tool_calls": [
                {
                    "id": tool_call.id,
                    "type": "function",
                    "function": {
                        "name": (
                            tool_call
                            .function
                            .name
                        ),
                        "arguments": (
                            tool_call
                            .function
                            .arguments
                        ),
                    },
                }
                for tool_call in tool_calls
            ],
        }

        request_messages.append(
            assistant_tool_message
        )

        # =================================================
        # EXECUTE REQUESTED TOOLS
        # =================================================

        for tool_call in tool_calls:

            function_name = (
                tool_call
                .function
                .name
            )

            raw_arguments = (
                tool_call
                .function
                .arguments
            )

            # -------------------------------------------------
            # Parse arguments
            # -------------------------------------------------

            try:

                arguments = json.loads(
                    raw_arguments
                )

            except (
                json.JSONDecodeError,
                TypeError,
            ):

                arguments = {}

            print(
                f"[ALFRED TOOL] "
                f"{function_name}"
            )

            # -------------------------------------------------
            # Execute approved local tool
            # -------------------------------------------------

            result = execute_tool(
                function_name,
                arguments,
            )

            print(
                f"[ALFRED TOOL RESULT] "
                f"{result}"
            )

            # -------------------------------------------------
            # Return result to model
            # -------------------------------------------------

            request_messages.append(
                {
                    "role": "tool",
                    "tool_call_id": (
                        tool_call.id
                    ),
                    "content": str(
                        result
                    ),
                }
            )

        # -----------------------------------------------------
        # Continue the loop.
        #
        # The model now sees the tool results and can either:
        #
        # 1. Call another approved tool, or
        # 2. Produce the final natural-language response.
        # -----------------------------------------------------


    # =====================================================
    # SAFETY FALLBACK
    # =====================================================

    return (
        "I wasn't able to complete that request "
        "within the available tool steps, Sir."
    )

import os
import subprocess
from datetime import datetime

from docx import Document
from docx.shared import Pt


# =========================================================
# PATHS
# =========================================================

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

RESEARCH_DIR = os.path.join(
    BASE_DIR,
    "research",
)

os.makedirs(
    RESEARCH_DIR,
    exist_ok=True,
)

CURRENT_RESEARCH_FILE = os.path.join(
    BASE_DIR,
    "research",
    "current_youtube_research.txt",
)



def get_research_content():
    if not os.path.exists(
        CURRENT_RESEARCH_FILE
    ):
        return None
    try:
        with open(
            CURRENT_RESEARCH_FILE,
            "r",
            encoding="utf-8",
        ) as file:
            content = file.read().strip()

        return content or None
    except Exception:
      
        return None
# =========================================================
# SAFE FILENAME
# =========================================================

def safe_filename(
    text: str,
):
    allowed = (
        "abcdefghijklmnopqrstuvwxyz"
        "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        "0123456789"
        " -_"
    )

    cleaned = "".join(
        char
        if char in allowed
        else "_"
        for char in text
    )

    cleaned = cleaned.strip()

    if not cleaned:
        cleaned = "alfred_research"

    return cleaned[:100]


# =========================================================
# SAVE TO NOTEPAD
# =========================================================

def save_to_notepad(
    title: str = "",
    content: str = "",
):
    """
    Save supplied content, or the latest YouTube research,
    to a .txt file and open it in Notepad.
    """

    title = (
        title.strip()
        if title
        else "ALFRED YouTube Research"
    )

    # Use latest research automatically when content
    # wasn't supplied.
    if not content.strip():
        content = (
            get_research_content()
            or ""
        )

    if not content:
        return (
            "There is no research content available, Sir."
        )

    timestamp = datetime.now().strftime(
        "%Y%m%d_%H%M%S"
    )

    filename = (
        f"{safe_filename(title)}_{timestamp}.txt"
    )

    path = os.path.join(
        RESEARCH_DIR,
        filename,
    )

    try:

        with open(
            path,
            "w",
            encoding="utf-8",
        ) as file:

            file.write(
                content
            )

    except Exception as error:

        return (
            "I couldn't save the text file, Sir. "
            f"{error}"
        )

    try:

        subprocess.Popen(
            [
                "notepad.exe",
                path,
            ]
        )

    except Exception as error:

        return (
            f"The research was saved to {path}, Sir, "
            f"but Notepad couldn't be opened: {error}"
        )

    return (
        f"Research saved to Notepad, Sir. "
        f"File: {path}"
    )

# =========================================================
# SAVE TO WORD
# =========================================================

def save_to_word(
    title: str = "",
    content: str = "",
):
    """
    Create a Word document.

    If content isn't supplied, automatically use the most
    recent YouTube research packet.
    """

    title = (
        title.strip()
        if title
        else "ALFRED YouTube Research"
    )

    if not content.strip():
        content = (
            get_research_content()
            or ""
        )

    if not content:
        return (
            "There is no research content available "
            "to save, Sir."
        )

    timestamp = datetime.now().strftime(
        "%Y%m%d_%H%M%S"
    )

    filename = (
        f"{safe_filename(title)}_{timestamp}.docx"
    )

    path = os.path.join(
        RESEARCH_DIR,
        filename,
    )

    try:

        document = Document()

        document.add_heading(
            title,
            level=0,
        )

        metadata = document.add_paragraph()

        run = metadata.add_run(
            "Created by ALFRED\n"
        )

        run.bold = True

        metadata.add_run(
            datetime.now().strftime(
                "%Y-%m-%d %H:%M"
            )
        )

        document.add_paragraph()

        for paragraph_text in content.split(
            "\n\n"
        ):

            paragraph_text = (
                paragraph_text.strip()
            )

            if not paragraph_text:
                continue

            paragraph = document.add_paragraph(
                paragraph_text
            )

            for run in paragraph.runs:
                run.font.size = Pt(11)

        document.save(
            path
        )

    except Exception as error:

        return (
            "I couldn't create the Word document, Sir. "
            f"{error}"
        )

    try:

        os.startfile(
            path
        )

    except Exception as error:

        return (
            f"The Word document was created at {path}, Sir, "
            f"but Windows couldn't open it: {error}"
        )

    return (
        f"Research saved to Word, Sir. "
        f"File: {path}"
    )

    
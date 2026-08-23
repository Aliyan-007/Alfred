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
    title: str,
    content: str,
):
    """
    Save text as a .txt file and open it in Windows Notepad.
    """

    title = title.strip()
    content = content.strip()

    if not title:
        title = "ALFRED Research"

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
            f"but I couldn't open Notepad: {error}"
        )

    return (
        f"Research saved to Notepad, Sir. "
        f"File: {path}"
    )


# =========================================================
# SAVE TO WORD
# =========================================================

def save_to_word(
    title: str,
    content: str,
):
    """
    Create a .docx file and open it using the default
    Windows application for Word documents.
    """

    title = title.strip()
    content = content.strip()

    if not title:
        title = "ALFRED Research"

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

        # -------------------------------------------------
        # Title
        # -------------------------------------------------

        document.add_heading(
            title,
            level=0,
        )

        # -------------------------------------------------
        # Metadata
        # -------------------------------------------------

        metadata = document.add_paragraph()

        metadata_run = metadata.add_run(
            "Created by ALFRED\n"
        )

        metadata_run.bold = True

        metadata.add_run(
            datetime.now().strftime(
                "%Y-%m-%d %H:%M"
            )
        )

        document.add_paragraph()

        # -------------------------------------------------
        # Content
        # -------------------------------------------------

        # Preserve paragraphs from the generated research.
        paragraphs = content.split(
            "\n\n"
        )

        for text in paragraphs:

            text = text.strip()

            if not text:
                continue

            paragraph = document.add_paragraph(
                text
            )

            for run in paragraph.runs:

                run.font.size = Pt(
                    11
                )

        # -------------------------------------------------
        # Save
        # -------------------------------------------------

        document.save(
            path
        )

    except Exception as error:

        return (
            "I couldn't create the Word document, Sir. "
            f"{error}"
        )

    # -----------------------------------------------------
    # Open document
    # -----------------------------------------------------

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

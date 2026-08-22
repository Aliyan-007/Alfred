import base64
import json
import os
from email.mime.text import MIMEText

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build


# =========================================================
# CONFIGURATION
# =========================================================

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

CREDENTIALS_FILE = os.path.join(
    BASE_DIR,
    "credentials.json",
)

TOKEN_FILE = os.path.join(
    BASE_DIR,
    "gmail_token.json",
)

PENDING_FILE = os.path.join(
    BASE_DIR,
    "pending_email.json",
)

SCOPES = [
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/gmail.send",
]


# =========================================================
# AUTHENTICATION
# =========================================================

def get_gmail_service():
    creds = None

    if os.path.exists(TOKEN_FILE):

        creds = Credentials.from_authorized_user_file(
            TOKEN_FILE,
            SCOPES,
        )

    if (
        not creds
        or not creds.valid
    ):

        if (
            creds
            and creds.expired
            and creds.refresh_token
        ):

            creds.refresh(
                Request()
            )

        else:

            if not os.path.exists(
                CREDENTIALS_FILE
            ):

                raise FileNotFoundError(
                    "credentials.json was not found at "
                    f"{CREDENTIALS_FILE}"
                )

            flow = InstalledAppFlow.from_client_secrets_file(
                CREDENTIALS_FILE,
                SCOPES,
            )

            creds = flow.run_local_server(
                port=0,
                access_type="offline",
                prompt="consent",
            )

        with open(
            TOKEN_FILE,
            "w",
            encoding="utf-8",
        ) as token:

            token.write(
                creds.to_json()
            )

    return build(
        "gmail",
        "v1",
        credentials=creds,
    )


# =========================================================
# CREATE MESSAGE
# =========================================================

def create_message(
    recipient: str,
    subject: str,
    body: str,
):
    message = MIMEText(
        body,
        "plain",
        "utf-8",
    )

    message["to"] = recipient
    message["subject"] = subject

    encoded = base64.urlsafe_b64encode(
        message.as_bytes()
    ).decode()

    return {
        "raw": encoded
    }


# =========================================================
# SAVE PENDING EMAIL
# =========================================================

def save_pending_email(
    draft_id: str,
    recipient: str,
    subject: str,
    body: str,
):
    data = {
        "draft_id": draft_id,
        "recipient": recipient,
        "subject": subject,
        "body": body,
    }

    with open(
        PENDING_FILE,
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            data,
            file,
            ensure_ascii=False,
            indent=2,
        )


# =========================================================
# LOAD PENDING EMAIL
# =========================================================

def load_pending_email():

    if not os.path.exists(
        PENDING_FILE
    ):

        return None

    try:

        with open(
            PENDING_FILE,
            "r",
            encoding="utf-8",
        ) as file:

            data = json.load(
                file
            )

        if not isinstance(
            data,
            dict,
        ):

            return None

        if not data.get(
            "draft_id"
        ):

            return None

        return data

    except Exception:

        return None


# =========================================================
# CLEAR PENDING EMAIL
# =========================================================

def clear_pending_email():

    try:

        if os.path.exists(
            PENDING_FILE
        ):

            os.remove(
                PENDING_FILE
            )

    except Exception:

        pass


# =========================================================
# CREATE OR REPLACE PENDING DRAFT
# =========================================================

def draft_email(
    recipient: str,
    subject: str,
    body: str,
):
    """
    Create a new Gmail draft.

    If a pending ALFRED draft already exists, replace that
    pending draft with the newly supplied recipient,
    subject, and body instead of creating another pending
    message.
    """

    recipient = recipient.strip()
    subject = subject.strip()
    body = body.strip()

    if not recipient:

        return (
            "I need a recipient email address, Sir."
        )

    if not subject:

        return (
            "I need an email subject, Sir."
        )

    if not body:

        return (
            "I need the email body, Sir."
        )

    service = get_gmail_service()

    pending = load_pending_email()

    # -----------------------------------------------------
    # Existing pending draft -> update it
    # -----------------------------------------------------

    if pending:

        draft_id = (
            pending.get(
                "draft_id",
                "",
            )
            or ""
        ).strip()

        if draft_id:

            message = create_message(
                recipient,
                subject,
                body,
            )

            message["id"] = draft_id

            try:

                service.users().drafts().update(
                    userId="me",
                    id=draft_id,
                    body=message,
                ).execute()

                save_pending_email(
                    draft_id,
                    recipient,
                    subject,
                    body,
                )

                return (
                    "Pending draft updated successfully, Sir.\n\n"
                    f"To: {recipient}\n"
                    f"Subject: {subject}\n"
                    f"Body:\n{body}\n\n"
                    "It has NOT been sent. "
                    "Say 'Send it' when you want me to send "
                    "this exact updated draft."
                )

            except Exception:

                # If the old draft disappeared from Gmail,
                # create a fresh draft below.
                pass

    # -----------------------------------------------------
    # No valid pending draft -> create a new one
    # -----------------------------------------------------

    message = create_message(
        recipient,
        subject,
        body,
    )

    draft = service.users().drafts().create(
        userId="me",
        body={
            "message": message,
        },
    ).execute()

    draft_id = draft.get(
        "id",
        "",
    )

    if not draft_id:

        return (
            "Gmail created the draft, but did not return "
            "a draft ID, Sir."
        )

    save_pending_email(
        draft_id,
        recipient,
        subject,
        body,
    )

    return (
        "Draft created successfully, Sir.\n\n"
        f"To: {recipient}\n"
        f"Subject: {subject}\n"
        f"Body:\n{body}\n\n"
        "It has NOT been sent. "
        "Say 'Send it' when you want me to send "
        "this exact draft."
    )


# =========================================================
# UPDATE + SEND PENDING EMAIL
# =========================================================

def send_pending_email(
    recipient: str = "",
    subject: str = "",
    body: str = "",
):
    """
    Send an email.

    Behavior:
    1. If a pending draft exists, optionally update it and send it.
    2. If no pending draft exists but recipient/subject/body are supplied,
       create a Gmail draft and immediately send it.

    This keeps Gmail functionality inside the existing tool.
    """

    pending = load_pending_email()

    # =====================================================
    # CASE 1: EXISTING PENDING DRAFT
    # =====================================================

    if pending:

        draft_id = (
            pending.get(
                "draft_id",
                "",
            )
            or ""
        ).strip()

        if not draft_id:

            clear_pending_email()

            return (
                "The pending email draft is invalid, Sir."
            )

        current_recipient = (
            pending.get(
                "recipient",
                "",
            )
            or ""
        ).strip()

        current_subject = (
            pending.get(
                "subject",
                "",
            )
            or ""
        ).strip()

        current_body = (
            pending.get(
                "body",
                "",
            )
            or ""
        ).strip()

        # Preserve old values if the model didn't supply
        # replacements.
        final_recipient = (
            recipient.strip()
            if recipient.strip()
            else current_recipient
        )

        final_subject = (
            subject.strip()
            if subject.strip()
            else current_subject
        )

        final_body = (
            body.strip()
            if body.strip()
            else current_body
        )

        if not final_recipient:
            return (
                "The pending email has no recipient, Sir."
            )

        if not final_subject:
            return (
                "The pending email has no subject, Sir."
            )

        if not final_body:
            return (
                "The pending email has no body, Sir."
            )

        service = get_gmail_service()

        changed = (
            final_recipient != current_recipient
            or final_subject != current_subject
            or final_body != current_body
        )

        # -------------------------------------------------
        # Update existing draft if necessary
        # -------------------------------------------------

        if changed:

            message = create_message(
                final_recipient,
                final_subject,
                final_body,
            )

            message["id"] = draft_id

            try:

                service.users().drafts().update(
                    userId="me",
                    id=draft_id,
                    body=message,
                ).execute()

                save_pending_email(
                    draft_id,
                    final_recipient,
                    final_subject,
                    final_body,
                )

            except Exception as error:

                return (
                    "I couldn't update the pending email "
                    f"before sending it, Sir. {error}"
                )

        # -------------------------------------------------
        # Send existing draft
        # -------------------------------------------------

        try:

            result = service.users().drafts().send(
                userId="me",
                body={
                    "id": draft_id
                },
            ).execute()

        except Exception as error:

            return (
                "I couldn't send the email, Sir. "
                f"{error}"
            )

        message_id = result.get(
            "id",
            "",
        )

        clear_pending_email()

        return (
            f"Email sent to {final_recipient}, Sir. "
            f"Subject: {final_subject}."
            + (
                f" Message ID: {message_id}."
                if message_id
                else ""
            )
        )

    # =====================================================
    # CASE 2: NO PENDING DRAFT
    # =====================================================

    recipient = recipient.strip()
    subject = subject.strip()
    body = body.strip()

    if not recipient:
        return (
            "I need a recipient email address, Sir."
        )

    if not subject:
        return (
            "I need an email subject, Sir."
        )

    if not body:
        return (
            "I need the email body, Sir."
        )

    service = get_gmail_service()

    # Create a temporary Gmail draft first, then send it.
    message = create_message(
        recipient,
        subject,
        body,
    )

    try:

        draft = service.users().drafts().create(
            userId="me",
            body={
                "message": message,
            },
        ).execute()

        draft_id = draft.get(
            "id",
            "",
        )

        if not draft_id:

            return (
                "Gmail created the email draft but did not "
                "return its ID, Sir."
            )

        result = service.users().drafts().send(
            userId="me",
            body={
                "id": draft_id,
            },
        ).execute()

    except Exception as error:

        return (
            "I couldn't send the email, Sir. "
            f"{error}"
        )

    message_id = result.get(
        "id",
        "",
    )

    return (
        f"Email sent to {recipient}, Sir. "
        f"Subject: {subject}."
        + (
            f" Message ID: {message_id}."
            if message_id
            else ""
        )
    )
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
    }

    for old, new in replacements.items():
        value = value.replace(
            old,
            new,
        )

    return value.replace(
        " ",
        "",
    )
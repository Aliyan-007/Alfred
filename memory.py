import sqlite3
from pathlib import Path
from datetime import datetime


# =========================================================
# DATABASE LOCATION
# =========================================================

BASE_DIR = Path(__file__).resolve().parent

DATABASE = BASE_DIR / "memory.db"


# =========================================================
# DATABASE CONNECTION
# =========================================================

def get_connection():
    """
    Create a connection to the shared Alfred memory database.
    """

    connection = sqlite3.connect(
        DATABASE
    )

    connection.row_factory = sqlite3.Row

    return connection


# =========================================================
# INITIALIZE DATABASE
# =========================================================

def initialize_memory():
    """
    Create the memory table if it does not already exist.
    """

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS memories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            category TEXT NOT NULL,

            key TEXT NOT NULL,

            value TEXT NOT NULL,

            created_at TEXT NOT NULL,

            updated_at TEXT NOT NULL,

            UNIQUE(category, key)
        )
        """
    )

    connection.commit()

    connection.close()


# =========================================================
# SAVE MEMORY
# =========================================================

def save_memory(
    category: str,
    key: str,
    value: str,
):
    """
    Save or update a memory.

    Example:

        save_memory(
            "education",
            "exam",
            "tomorrow"
        )
    """

    category = category.strip()
    key = key.strip()
    value = value.strip()

    if not category or not key or not value:
        return

    now = datetime.now().isoformat(
        timespec="seconds"
    )

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        INSERT INTO memories (
            category,
            key,
            value,
            created_at,
            updated_at
        )
        VALUES (?, ?, ?, ?, ?)

        ON CONFLICT(category, key)
        DO UPDATE SET
            value = excluded.value,
            updated_at = excluded.updated_at
        """,
        (
            category,
            key,
            value,
            now,
            now,
        ),
    )

    connection.commit()

    connection.close()


# =========================================================
# GET ONE MEMORY
# =========================================================

def get_memory(
    category: str,
    key: str,
):
    """
    Retrieve one memory.

    Returns:
        string
        or None
    """

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT value
        FROM memories
        WHERE category = ?
        AND key = ?
        LIMIT 1
        """,
        (
            category,
            key,
        ),
    )

    row = cursor.fetchone()

    connection.close()

    if row is None:
        return None

    return row["value"]


# =========================================================
# GET ALL MEMORIES
# =========================================================

def get_all_memories():
    """
    Return all stored memories.
    """

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            id,
            category,
            key,
            value,
            created_at,
            updated_at
        FROM memories
        ORDER BY id ASC
        """
    )

    rows = cursor.fetchall()

    connection.close()

    return rows


# =========================================================
# SEARCH MEMORIES
# =========================================================

def search_memories(
    query: str,
    limit: int = 10,
):
    """
    Search memories using category, key, or value.
    """

    query = query.strip()

    if not query:
        return []

    search_term = f"%{query}%"

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            id,
            category,
            key,
            value,
            created_at,
            updated_at
        FROM memories
        WHERE
            category LIKE ?
            OR key LIKE ?
            OR value LIKE ?
        ORDER BY id DESC
        LIMIT ?
        """,
        (
            search_term,
            search_term,
            search_term,
            limit,
        ),
    )

    rows = cursor.fetchall()

    connection.close()

    return rows


# =========================================================
# DELETE MEMORY
# =========================================================

def delete_memory(
    category: str,
    key: str,
):
    """
    Delete a specific memory.
    """

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        DELETE FROM memories
        WHERE category = ?
        AND key = ?
        """,
        (
            category,
            key,
        ),
    )

    deleted = cursor.rowcount

    connection.commit()

    connection.close()

    return deleted > 0


# =========================================================
# CLEAR ALL MEMORY
# =========================================================

def clear_all_memory():
    """
    Delete every stored memory.
    """

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        DELETE FROM memories
        """
    )

    connection.commit()

    connection.close()


# =========================================================
# FORMAT MEMORIES FOR AI
# =========================================================

def format_memories(
    memories,
):
    """
    Convert database memories into text that can be
    supplied to the AI.
    """

    if not memories:
        return "No stored memories."

    lines = []

    for memory in memories:

        lines.append(
            f"- "
            f"[{memory['category']}] "
            f"{memory['key']}: "
            f"{memory['value']}"
        )

    return "\n".join(lines)


# =========================================================
# INITIALIZE ON IMPORT
# =========================================================

initialize_memory()
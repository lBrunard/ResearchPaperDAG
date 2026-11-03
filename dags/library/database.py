import json
import sqlite3
from contextlib import closing

from library.config import DB_PATH


def _connect() -> sqlite3.Connection:
    """
    Open a connection to the database, creating the data/ folder if needed.
    """
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """
    Create the papers table if it does not exist yet.
    """
    with closing(_connect()) as conn, conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS papers (
                filename     TEXT PRIMARY KEY, 
                title        TEXT NOT NULL,
                summary      TEXT NOT NULL,
                keywords     TEXT NOT NULL,
                category     TEXT NOT NULL,
                processed_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )


def get_processed_filenames() -> set[str]:
    """
    Return the filenames of all papers already stored in the database.
    """
    init_db()
    with closing(_connect()) as conn:
        rows = conn.execute("SELECT filename FROM papers").fetchall()
    return {row["filename"] for row in rows}


def save_paper(filename: str, title: str, summary: str,
               keywords: list[str], category: str) -> None:
    """
    Insert a paper, or update it if the filename already exists (idempotent).
    """
    init_db()
    with closing(_connect()) as conn, conn:
        conn.execute(
            """
            INSERT INTO papers (filename, title, summary, keywords, category)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(filename) DO UPDATE SET
                title        = excluded.title,
                summary      = excluded.summary,
                keywords     = excluded.keywords,
                category     = excluded.category,
                processed_at = CURRENT_TIMESTAMP
            """,
            (filename, title, summary, json.dumps(keywords), category),
        )


def get_all_papers() -> list[dict]:
    """
    Return all papers (newest first), with keywords decoded back to a list.
    Used to build the HTML page.
    """
    init_db()
    with closing(_connect()) as conn:
        rows = conn.execute(
            "SELECT * FROM papers ORDER BY processed_at DESC"
        ).fetchall()
    papers = [dict(row) for row in rows]
    for paper in papers:
        paper["keywords"] = json.loads(paper["keywords"])
    return papers

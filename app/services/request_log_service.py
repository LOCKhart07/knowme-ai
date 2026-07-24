from typing import Optional
from contextlib import contextmanager
from datetime import datetime, UTC
import sqlite3
import os
import logging

logger = logging.getLogger(__name__)

DEFAULT_DB_PATH = os.getenv("REQUESTS_DB_PATH", "data/requests.db")


class RequestLogService:
    """
    Persists user chat questions and the AI's answers to SQLite.

    Logging failures never raise - a chat response should still reach the
    user even if it can't be recorded.
    """

    def __init__(self, db_path: str = DEFAULT_DB_PATH):
        self.db_path = db_path
        dirname = os.path.dirname(db_path)
        if dirname:
            os.makedirs(dirname, exist_ok=True)
        self._init_db()

    @contextmanager
    def _connect(self):
        conn = sqlite3.connect(self.db_path)
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS chat_requests (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    message_id TEXT,
                    query TEXT NOT NULL,
                    response TEXT,
                    created_at TEXT NOT NULL
                )
                """
            )

    def log(
        self,
        query: str,
        response: str,
        message_id: Optional[str] = None,
    ) -> None:
        try:
            with self._connect() as conn:
                conn.execute(
                    """
                    INSERT INTO chat_requests
                        (message_id, query, response, created_at)
                    VALUES (?, ?, ?, ?)
                    """,
                    (
                        str(message_id) if message_id else None,
                        query,
                        response,
                        datetime.now(UTC).isoformat(),
                    ),
                )
        except Exception as e:
            logger.error(f"Failed to log chat request: {str(e)}")

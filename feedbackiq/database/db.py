"""
SQLite database connection and initialization.
"""

import sqlite3
import os
from typing import Generator
from contextlib import contextmanager

def get_db_path() -> str:
    """Get current SQLite database path from environment or default."""
    return os.environ.get(
        "FEEDBACKIQ_DB_PATH",
        os.path.join(os.path.dirname(os.path.dirname(__file__)), "feedbackiq.db")
    )


def get_db_connection() -> sqlite3.Connection:
    """Create and return a configured sqlite3 connection with Row factory."""
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


@contextmanager
def db_session() -> Generator[sqlite3.Connection, None, None]:
    """Context manager for database transactions."""
    conn = get_db_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db() -> None:
    """Initialize SQLite database tables and indexes."""
    with db_session() as conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS feedback_cases (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            case_id TEXT UNIQUE NOT NULL,
            created_at TEXT NOT NULL,
            source_channel TEXT NOT NULL,
            original_feedback TEXT NOT NULL,
            feedback_type TEXT NOT NULL,
            issue_type TEXT NOT NULL,
            sentiment TEXT NOT NULL,
            hospital TEXT,
            department TEXT,
            incident_date TEXT,
            approximate_time TEXT,
            service_type TEXT,
            staff_role TEXT,
            staff_name TEXT,
            billing_context TEXT,
            description_of_event TEXT,
            impact TEXT,
            explicit_request TEXT,
            extracted_summary TEXT,
            extraction_confidence REAL DEFAULT 0.8,
            completeness_score INTEGER DEFAULT 0,
            status TEXT NOT NULL,
            follow_up_priority TEXT NOT NULL,
            contact_status TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );

        CREATE INDEX IF NOT EXISTS idx_cases_status ON feedback_cases(status);
        CREATE INDEX IF NOT EXISTS idx_cases_issue_type ON feedback_cases(issue_type);
        CREATE INDEX IF NOT EXISTS idx_cases_score ON feedback_cases(completeness_score);
        CREATE INDEX IF NOT EXISTS idx_cases_contact ON feedback_cases(contact_status);

        CREATE TABLE IF NOT EXISTS missing_fields (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            case_id TEXT NOT NULL,
            field_name TEXT NOT NULL,
            is_critical INTEGER NOT NULL DEFAULT 0,
            resolved INTEGER NOT NULL DEFAULT 0,
            FOREIGN KEY (case_id) REFERENCES feedback_cases(case_id) ON DELETE CASCADE
        );

        CREATE INDEX IF NOT EXISTS idx_missing_case_id ON missing_fields(case_id);

        CREATE TABLE IF NOT EXISTS follow_up_entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            case_id TEXT NOT NULL,
            created_at TEXT NOT NULL,
            contact_status TEXT NOT NULL,
            additional_information TEXT,
            notes TEXT,
            FOREIGN KEY (case_id) REFERENCES feedback_cases(case_id) ON DELETE CASCADE
        );

        CREATE INDEX IF NOT EXISTS idx_followup_case_id ON follow_up_entries(case_id);

        CREATE TABLE IF NOT EXISTS analysis_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            case_id TEXT NOT NULL,
            created_at TEXT NOT NULL,
            completeness_score INTEGER NOT NULL,
            status TEXT NOT NULL,
            extracted_json TEXT NOT NULL,
            FOREIGN KEY (case_id) REFERENCES feedback_cases(case_id) ON DELETE CASCADE
        );

        CREATE INDEX IF NOT EXISTS idx_history_case_id ON analysis_history(case_id);
        """)

"""
database.py — raw sqlite3 layer (no SQLAlchemy dependency)
Drop-in for PythonAnywhere or any Flask environment.
"""
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), 'conference_meditation.db')


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    with get_db() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS topics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                search_query TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS pinned_videos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                topic_id INTEGER NOT NULL REFERENCES topics(id) ON DELETE CASCADE,
                url TEXT NOT NULL,
                video_id TEXT NOT NULL,
                title TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                topic_id INTEGER NOT NULL REFERENCES topics(id),
                work_minutes INTEGER NOT NULL DEFAULT 25,
                break_minutes INTEGER NOT NULL DEFAULT 5,
                rounds INTEGER NOT NULL DEFAULT 4,
                video_id TEXT NOT NULL DEFAULT '',
                video_title TEXT NOT NULL DEFAULT '',
                started_at TEXT NOT NULL,
                completed_at TEXT
            );

            CREATE TABLE IF NOT EXISTS notes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
                content TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
        """)
        # Seed default topics
        count = conn.execute("SELECT COUNT(*) FROM topics").fetchone()[0]
        if count == 0:
            defaults = [
                ('Nexthink', 'Nexthink DEX'),
                ('Claude', 'Anthropic Claude AI'),
                ('OpenAI', 'OpenAI GPT'),
                ('Microsoft Copilot', 'Microsoft Copilot M365'),
                ('DEX', 'Digital Employee Experience DEX'),
                ('AI Agents', 'AI agents autonomous'),
                ('Identity & Security', 'identity security IAM'),
            ]
            conn.executemany(
                "INSERT INTO topics (name, search_query) VALUES (?, ?)", defaults
            )
        conn.commit()

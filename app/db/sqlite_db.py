import sqlite3
import json
from typing import Optional
from dataclasses import dataclass

# Define SQLite database file
DB_FILE = "./db/registration.db"


@dataclass
class RegistrationState:
    session_id: str
    collected_data: dict
    current_question: str
    current_node: str


# Initialize the database & table if not exists
def init_db():
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS sessions (
                session_id TEXT PRIMARY KEY,
                collected_data TEXT,
                current_question TEXT,
                current_node TEXT
            )
            """
        )
        conn.commit()


# Insert or update a session in SQLite
def upsert_session_to_db(
    session_id: str, collected_data: dict, current_question: str, current_node: str
):
    collected_data_json = json.dumps(collected_data)
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO sessions (session_id, collected_data, current_question, current_node)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(session_id) DO UPDATE SET
                collected_data = excluded.collected_data,
                current_question = excluded.current_question,
                current_node = excluded.current_node
            """,
            (session_id, collected_data_json, current_question, current_node),
        )
        conn.commit()


# Fetch a session from SQLite & return as a dictionary
def fetch_session_from_db(session_id: str) -> Optional[dict]:
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT session_id, collected_data, current_question, current_node FROM sessions WHERE session_id = ?",
            (session_id,),
        )
        result = cursor.fetchone()

    if result:
        session_id, collected_data_json, current_question, current_node = result
        collected_data = json.loads(
            collected_data_json
        )  # Convert JSON string back to dict
        return {
            "session_id": session_id,
            "collected_data": collected_data,
            "current_question": current_question,
            "current_node": current_node,
        }

    return None  # Session not found


# Initialize database on import
init_db()

"""
db.py — SQLite persistence layer for the Pathao CX Training Portal.

Note on Streamlit Community Cloud: the filesystem there is ephemeral —
training_portal.db persists while the app is running, but a redeploy or
long idle-restart can reset it. For a small team this is usually fine to
start with. If you need data to survive redeploys, swap the sqlite3 calls
below for a free hosted DB (Supabase/Postgres, or Google Sheets via gspread)
— the function signatures here are the only thing the rest of the app
depends on, so the app.py file does not need to change.
"""
import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "training_portal.db")


def get_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_conn()
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS induction_entries (
            id TEXT PRIMARY KEY,
            date TEXT NOT NULL,
            topic TEXT NOT NULL,
            assignment TEXT,
            task TEXT,
            trainee_name TEXT,
            trainee_empid TEXT,
            score TEXT,
            notes TEXT,
            file_name TEXT,
            file_data BLOB
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS refresher_topics (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT,
            minutes INTEGER
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS refresher_records (
            id TEXT PRIMARY KEY,
            email TEXT NOT NULL,
            empid TEXT NOT NULL,
            topic_id TEXT,
            topic_name TEXT,
            started_at TEXT,
            completed_at TEXT,
            duration_min INTEGER
        )
    """)
    conn.commit()
    conn.close()


# ---------- Induction entries ----------
def upsert_induction_entry(entry: dict):
    conn = get_conn()
    conn.execute("""
        INSERT INTO induction_entries
            (id, date, topic, assignment, task, trainee_name, trainee_empid, score, notes, file_name, file_data)
        VALUES (:id, :date, :topic, :assignment, :task, :trainee_name, :trainee_empid, :score, :notes, :file_name, :file_data)
        ON CONFLICT(id) DO UPDATE SET
            date=excluded.date, topic=excluded.topic, assignment=excluded.assignment,
            task=excluded.task, trainee_name=excluded.trainee_name, trainee_empid=excluded.trainee_empid,
            score=excluded.score, notes=excluded.notes,
            file_name=COALESCE(excluded.file_name, induction_entries.file_name),
            file_data=COALESCE(excluded.file_data, induction_entries.file_data)
    """, entry)
    conn.commit()
    conn.close()


def delete_induction_entry(entry_id: str):
    conn = get_conn()
    conn.execute("DELETE FROM induction_entries WHERE id=?", (entry_id,))
    conn.commit()
    conn.close()


def get_induction_entries(date: str = None):
    conn = get_conn()
    if date:
        rows = conn.execute("SELECT * FROM induction_entries WHERE date=?", (date,)).fetchall()
    else:
        rows = conn.execute("SELECT * FROM induction_entries ORDER BY date").fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ---------- Refresher topics ----------
def upsert_topic(topic: dict):
    conn = get_conn()
    conn.execute("""
        INSERT INTO refresher_topics (id, name, description, minutes)
        VALUES (:id, :name, :description, :minutes)
        ON CONFLICT(id) DO UPDATE SET
            name=excluded.name, description=excluded.description, minutes=excluded.minutes
    """, topic)
    conn.commit()
    conn.close()


def delete_topic(topic_id: str):
    conn = get_conn()
    conn.execute("DELETE FROM refresher_topics WHERE id=?", (topic_id,))
    conn.commit()
    conn.close()


def get_topics():
    conn = get_conn()
    rows = conn.execute("SELECT * FROM refresher_topics ORDER BY name").fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ---------- Refresher records ----------
def insert_record(record: dict):
    conn = get_conn()
    conn.execute("""
        INSERT INTO refresher_records
            (id, email, empid, topic_id, topic_name, started_at, completed_at, duration_min)
        VALUES (:id, :email, :empid, :topic_id, :topic_name, :started_at, :completed_at, :duration_min)
    """, record)
    conn.commit()
    conn.close()


def get_records():
    conn = get_conn()
    rows = conn.execute("SELECT * FROM refresher_records ORDER BY completed_at DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]

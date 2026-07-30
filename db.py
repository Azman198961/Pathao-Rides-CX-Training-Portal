import sqlite3
import os

DB_FILE = os.path.join(os.path.dirname(__file__), "portal_persistent.db")

def get_connection():
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    
    # Drop existing table if column structure is outdated to prevent OperationalError
    cursor.execute("PRAGMA table_info(topics)")
    columns = [col[1] for col in cursor.fetchall()]
    if columns and "form_url" not in columns:
        cursor.execute("DROP TABLE IF EXISTS topics")

    # 1. Topics Table (Updated with slide_url and form_url)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS topics (
        id TEXT PRIMARY KEY,
        name TEXT,
        duration TEXT,
        trainer_name TEXT,
        slide_url TEXT,
        form_url TEXT
    )
    """)

    # 2. Refresher Requests Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS refresher_requests (
        id TEXT PRIMARY KEY,
        empid TEXT,
        name TEXT,
        channel TEXT,
        topic_name TEXT,
        preferred_slot TEXT,
        status TEXT DEFAULT 'Pending',
        rejection_reason TEXT DEFAULT '',
        training_status TEXT DEFAULT 'Pending'
    )
    """)

    # 3. Induction Activity Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS induction_activities (
        id TEXT PRIMARY KEY,
        agent_id TEXT,
        agent_name TEXT,
        channel TEXT,
        topic_id TEXT,
        topic_name TEXT,
        hours_spent REAL,
        quiz_score INTEGER,
        status TEXT,
        activity_date TEXT
    )
    """)

    # Default Topics Auto-Insertion
    cursor.execute("SELECT COUNT(*) FROM topics")
    if cursor.fetchone()[0] == 0:
        default_topics = [
            ("top_1", "Fare Information", "45 mins", "CMT Team", "https://docs.google.com/presentation/d/136RdIr9tshx3OMd8nFRhCj_aTo84p9c-XAJFKDrrw-k/embed", ""),
            ("top_2", "Joining Process", "60 mins", "CMT Team", "https://docs.google.com/presentation/d/1AxdbPQSPr0Cmlx9HjZPS_jHtj-xgjNMGlXHZcfF9MQ4/embed", ""),
            ("top_3", "Star Program", "30 mins", "CMT Team", "https://docs.google.com/presentation/d/1SbNxrXajQlZIpT6fvT_a9bXwmIhl1dQZh2olZ0s8lMI/embed", ""),
            ("top_4", "Payment", "45 mins", "CMT Team", "https://docs.google.com/presentation/d/1Q9ous8zu6CmPe2Yw8oTKS-FkPKHUOHPT/embed", ""),
            ("top_5", "User SOP", "60 mins", "CMT Team", "https://docs.google.com/presentation/d/1TCkGIRTbQ87ZmW8vZM4WS2nN237GzQWi/embed", ""),
            ("top_6", "Rider SOP", "60 mins", "CMT Team", "https://docs.google.com/presentation/d/1A28xX9YdsEuHOIGEPfEigQ6C_azRmNap/embed", ""),
            ("top_7", "QA Parameters", "45 mins", "CMT Team", "https://docs.google.com/presentation/d/1IT7U4N88rSaHSsbVPqY5K03kfKA3iddW98VT9lsPLVM/embed", ""),
            ("top_8", "Pathao Internal Tools", "60 mins", "CMT Team", "https://docs.google.com/presentation/d/1UZQiOydwqm9etUb8MzEDXwGHbLipc30O/embed", "")
        ]
        cursor.executemany("""
            INSERT INTO topics (id, name, duration, trainer_name, slide_url, form_url)
            VALUES (?, ?, ?, ?, ?, ?)
        """, default_topics)

    conn.commit()
    conn.close()

def upsert_topic(data):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO topics (id, name, duration, trainer_name, slide_url, form_url)
        VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET
            name=excluded.name,
            duration=excluded.duration,
            trainer_name=excluded.trainer_name,
            slide_url=excluded.slide_url,
            form_url=excluded.form_url
    """, (data['id'], data['name'], data['duration'], data['trainer_name'], data['slide_url'], data['form_url']))
    conn.commit()
    conn.close()

def get_topics():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM topics")
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def delete_topic(topic_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM topics WHERE id = ?", (topic_id,))
    conn.commit()
    conn.close()

def insert_refresher_request(data):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO refresher_requests (id, empid, name, channel, topic_name, preferred_slot, status, training_status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (data['id'], data['empid'], data['name'], data['channel'], data['topic_name'], data['preferred_slot'], 'Pending', 'Pending'))
    conn.commit()
    conn.close()

def get_refresher_requests():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM refresher_requests")
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def update_refresher_status(req_id, status, rejection_reason="", training_status="Pending"):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE refresher_requests 
        SET status = ?, rejection_reason = ?, training_status = ?
        WHERE id = ?
    """, (status, rejection_reason, training_status, req_id))
    conn.commit()
    conn.close()

def get_induction_activities():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM induction_activities")
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

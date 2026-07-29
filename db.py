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
    
    # 1. Topics Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS topics (
        id TEXT PRIMARY KEY,
        name TEXT,
        duration TEXT,
        trainer_name TEXT,
        quiz_passing_mark INTEGER,
        quiz_questions TEXT,
        site_url TEXT
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

    # 3. Induction Activity & Health Track Table
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
        status TEXT, -- Passed, Failed, In Progress
        activity_date TEXT
    )
    """)

    # Sample Data for Induction Performance Testing (If empty)
    cursor.execute("SELECT COUNT(*) FROM induction_activities")
    if cursor.fetchone()[0] == 0:
        sample_activities = [
            ('1', 'EMP101', 'Rahim Ahmed', 'Inbound Voice', 't1', 'Rider Joining Process', 3.5, 85, 'Passed', '2026-03-25'),
            ('2', 'EMP102', 'Karim Ullah', 'Live Chat', 't2', 'Fare Information', 2.0, 60, 'Failed', '2026-03-26'),
            ('3', 'EMP103', 'Sultana Razia', 'Inbound Voice', 't1', 'Rider Joining Process', 4.0, 95, 'Passed', '2026-03-27'),
            ('4', 'EMP104', 'Tanvir Hasan', 'Complaint Management', 't3', 'SOPs & Internal Tools', 1.5, 40, 'Failed', '2026-03-28'),
            ('5', 'EMP101', 'Rahim Ahmed', 'Inbound Voice', 't3', 'SOPs & Internal Tools', 2.5, 90, 'Passed', '2026-03-28')
        ]
        cursor.executemany("""
            INSERT INTO induction_activities 
            (id, agent_id, agent_name, channel, topic_id, topic_name, hours_spent, quiz_score, status, activity_date)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, sample_activities)

    conn.commit()
    conn.close()

def upsert_topic(data):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO topics (id, name, duration, trainer_name, quiz_passing_mark, quiz_questions, site_url)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET
            name=excluded.name,
            duration=excluded.duration,
            trainer_name=excluded.trainer_name,
            quiz_passing_mark=excluded.quiz_passing_mark,
            quiz_questions=excluded.quiz_questions,
            site_url=excluded.site_url
    """, (data['id'], data['name'], data['duration'], data['trainer_name'], data['quiz_passing_mark'], data['quiz_questions'], data['site_url']))
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

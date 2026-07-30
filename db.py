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

    # 3. Agent Directory Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS agents (
        empid TEXT PRIMARY KEY,
        name TEXT,
        email TEXT,
        phone TEXT
    )
    """)

    # 4. Range-Based Calendar Schedule Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS batch_calendar_schedules (
        id TEXT PRIMARY KEY,
        batch_name TEXT,
        start_date TEXT,
        end_date TEXT,
        schedule_json TEXT,
        status TEXT DEFAULT 'In Progress'
    )
    """)

    # 5. Agent Evaluation Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS agent_evaluations (
        empid TEXT PRIMARY KEY,
        agent_name TEXT,
        quiz1 REAL DEFAULT 0,
        quiz2 REAL DEFAULT 0,
        quiz3 REAL DEFAULT 0,
        assignment REAL DEFAULT 0,
        mock_call REAL DEFAULT 0,
        live_comm REAL DEFAULT 0,
        final_score REAL DEFAULT 0
    )
    """)

    # Default Topics Insertion
    cursor.execute("SELECT COUNT(*) FROM topics")
    if cursor.fetchone()[0] == 0:
        default_topics = [
            ("top_1", "Fare Information", "45 mins", "Md Asikul islam Azman", "https://docs.google.com/presentation/d/136RdIr9tshx3OMd8nFRhCj_aTo84p9c-XAJFKDrrw-k/embed", ""),
            ("top_2", "Joining Process", "60 mins", "Md Asikul islam Azman", "https://docs.google.com/presentation/d/1AxdbPQSPr0Cmlx9HjZPS_jHtj-xgjNMGlXHZcfF9MQ4/embed", ""),
            ("top_3", "Star Program", "30 mins", "Md Asikul islam Azman", "https://docs.google.com/presentation/d/1SbNxrXajQlZIpT6fvT_a9bXwmIhl1dQZh2olZ0s8lMI/embed", ""),
            ("top_4", "Payment", "45 mins", "Md Asikul islam Azman", "https://docs.google.com/presentation/d/1Q9ous8zu6CmPe2Yw8oTKS-FkPKHUOHPT/embed", ""),
            ("top_5", "User SOP", "60 mins", "Md Asikul islam Azman", "https://docs.google.com/presentation/d/1TCkGIRTbQ87ZmW8vZM4WS2nN237GzQWi/embed", ""),
            ("top_6", "Rider SOP", "60 mins", "Md Asikul islam Azman", "https://docs.google.com/presentation/d/1A28xX9YdsEuHOIGEPfEigQ6C_azRmNap/embed", ""),
            ("top_7", "QA Parameters", "45 mins", "Md Asikul islam Azman", "https://docs.google.com/presentation/d/1IT7U4N88rSaHSsbVPqY5K03kfKA3iddW98VT9lsPLVM/embed", ""),
            ("top_8", "Pathao Internal Tools", "60 mins", "Md Asikul islam Azman", "https://docs.google.com/presentation/d/1UZQiOydwqm9etUb8MzEDXwGHbLipc30O/embed", "")
        ]
        cursor.executemany("""
            INSERT INTO topics (id, name, duration, trainer_name, slide_url, form_url)
            VALUES (?, ?, ?, ?, ?, ?)
        """, default_topics)

    conn.commit()
    conn.close()

# Topic functions
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

# Agent Functions
def upsert_agent(empid, name, email, phone):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO agents (empid, name, email, phone)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(empid) DO UPDATE SET
            name=excluded.name,
            email=excluded.email,
            phone=excluded.phone
    """, (empid, name, email, phone))
    
    cursor.execute("""
        INSERT OR IGNORE INTO agent_evaluations (empid, agent_name)
        VALUES (?, ?)
    """, (empid, name))
    
    conn.commit()
    conn.close()

def get_agents():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM agents")
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def delete_agent(empid):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM agents WHERE empid = ?", (empid,))
    cursor.execute("DELETE FROM agent_evaluations WHERE empid = ?", (empid,))
    conn.commit()
    conn.close()

# Batch Calendar Schedule Functions
def save_batch_schedule(sched_id, batch_name, start_date, end_date, schedule_json, status="In Progress"):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO batch_calendar_schedules (id, batch_name, start_date, end_date, schedule_json, status)
        VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET
            batch_name=excluded.batch_name,
            start_date=excluded.start_date,
            end_date=excluded.end_date,
            schedule_json=excluded.schedule_json,
            status=excluded.status
    """, (sched_id, batch_name, start_date, end_date, schedule_json, status))
    conn.commit()
    conn.close()

def update_schedule_json_and_status(sched_id, schedule_json, status=None):
    conn = get_connection()
    cursor = conn.cursor()
    if status:
        cursor.execute("""
            UPDATE batch_calendar_schedules 
            SET schedule_json = ?, status = ?
            WHERE id = ?
        """, (schedule_json, status, sched_id))
    else:
        cursor.execute("""
            UPDATE batch_calendar_schedules 
            SET schedule_json = ?
            WHERE id = ?
        """, (schedule_json, sched_id))
    conn.commit()
    conn.close()

def get_batch_schedules():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM batch_calendar_schedules ORDER BY start_date DESC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def delete_batch_schedule(sched_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM batch_calendar_schedules WHERE id = ?", (sched_id,))
    conn.commit()
    conn.close()

# Evaluation Functions
def get_evaluations():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM agent_evaluations")
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def update_evaluation(empid, q1, q2, q3, assign, mock, live, final):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE agent_evaluations 
        SET quiz1=?, quiz2=?, quiz3=?, assignment=?, mock_call=?, live_comm=?, final_score=?
        WHERE empid=?
    """, (q1, q2, q3, assign, mock, live, final, empid))
    conn.commit()
    conn.close()

# Refresher Functions
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

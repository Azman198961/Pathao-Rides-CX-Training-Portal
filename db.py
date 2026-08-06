import sqlite3
import pandas as pd
import json

DB_FILE = "training.db"

def get_connection():
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    c = conn.cursor()

    # Create Tables
    c.execute("""
        CREATE TABLE IF NOT EXISTS agents (
            empid TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            channel TEXT DEFAULT 'Inbound Voice',
            employment_status TEXT DEFAULT 'Induction'
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS topics (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            duration TEXT,
            trainer_name TEXT,
            slide_url TEXT,
            form_url TEXT
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS self_training_logs (
            id TEXT PRIMARY KEY,
            empid TEXT,
            name TEXT,
            channel TEXT,
            topic_name TEXT,
            access_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            completion_time TIMESTAMP,
            status TEXT DEFAULT 'In Progress',
            quiz_score REAL DEFAULT 0.0,
            delay_reason TEXT
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS refresher_requests (
            id TEXT PRIMARY KEY,
            empid TEXT,
            name TEXT,
            channel TEXT,
            topic_name TEXT,
            preferred_slot TEXT,
            request_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status TEXT DEFAULT 'Pending'
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS batch_schedules (
            id TEXT PRIMARY KEY,
            batch_name TEXT NOT NULL,
            start_date TEXT,
            end_date TEXT,
            schedule_json TEXT,
            status TEXT DEFAULT 'In Progress',
            edit_reason TEXT,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS evaluations (
            empid TEXT PRIMARY KEY,
            quiz1 REAL DEFAULT 0.0,
            quiz2 REAL DEFAULT 0.0,
            quiz3 REAL DEFAULT 0.0,
            assignment REAL DEFAULT 0.0,
            mock_call REAL DEFAULT 0.0,
            live_comm REAL DEFAULT 0.0,
            final_score REAL DEFAULT 0.0,
            FOREIGN KEY(empid) REFERENCES agents(empid)
        )
    """)

    # Default Topics Seeding with Google Slides Embed Links
    default_topics = [
        {
            "id": "top_1",
            "name": "Inbound Voice - Fare & Payment Dispuite",
            "duration": "3 Hours",
            "trainer": "Md Asikul islam Azman",
            "slide_url": "https://docs.google.com/presentation/d/1v4vH0aL34RkL8xU_qS5zT8K4K0046E2W/embed"
        },
        {
            "id": "top_2",
            "name": "Inbound Voice - Safety & Emergency Escalation",
            "duration": "3 Hours",
            "trainer": "Md Asikul islam Azman",
            "slide_url": "https://docs.google.com/presentation/d/1yK9v87zH3fKj2L9L8xU_qS5zT8K4K0046E2W/embed"
        },
        {
            "id": "top_3",
            "name": "Live Chat - Promo Code & Refund Policy",
            "duration": "2 Hours",
            "trainer": "Md Asikul islam Azman",
            "slide_url": "https://docs.google.com/presentation/d/1zN0m98gH4fKj2L9L8xU_qS5zT8K4K0046E2W/embed"
        },
        {
            "id": "top_4",
            "name": "Report Issue & Email - Escalation Matrix",
            "duration": "2.5 Hours",
            "trainer": "Md Asikul islam Azman",
            "slide_url": "https://docs.google.com/presentation/d/1aO1p87gH5fKj2L9L8xU_qS5zT8K4K0046E2W/embed"
        },
        {
            "id": "top_5",
            "name": "Complaint Management - Escalation Procedure",
            "duration": "3 Hours",
            "trainer": "Md Asikul islam Azman",
            "slide_url": "https://docs.google.com/presentation/d/1bP2q87gH6fKj2L9L8xU_qS5zT8K4K0046E2W/embed"
        }
    ]

    c.execute("SELECT COUNT(*) FROM topics")
    if c.fetchone()[0] == 0:
        for t in default_topics:
            c.execute("""
                INSERT INTO topics (id, name, duration, trainer_name, slide_url, form_url)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (t["id"], t["name"], t["duration"], t["trainer"], t["slide_url"], ""))
        conn.commit()

    conn.close()

# --- Helper DB Functions ---

def sync_to_gsheet(sheet_name, row_data):
    pass

def get_agents():
    conn = get_connection()
    df = pd.read_sql_query("SELECT * FROM agents", conn)
    conn.close()
    return df.to_dict(orient="records")

def upsert_agent(empid, name, email, channel='Inbound Voice', employment_status='Induction'):
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        INSERT INTO agents (empid, name, email, channel, employment_status)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(empid) DO UPDATE SET
            name=excluded.name,
            email=excluded.email,
            channel=excluded.channel,
            employment_status=excluded.employment_status
    """, (empid, name, email, channel, employment_status))
    
    c.execute("INSERT OR IGNORE INTO evaluations (empid) VALUES (?)", (empid,))
    conn.commit()
    conn.close()

def bulk_upsert_agents(df):
    for _, row in df.iterrows():
        empid = str(row.get('empid', '')).strip()
        name = str(row.get('name', '')).strip()
        email = str(row.get('email', '')).strip()
        channel = str(row.get('channel', 'Inbound Voice')).strip()
        status = str(row.get('employment_status', 'Induction')).strip()
        if empid and name:
            upsert_agent(empid, name, email, channel, status)

def update_agent_status(empid, new_status):
    conn = get_connection()
    c = conn.cursor()
    c.execute("UPDATE agents SET employment_status = ? WHERE empid = ?", (new_status, empid))
    conn.commit()
    conn.close()

def delete_agent(empid):
    conn = get_connection()
    c = conn.cursor()
    c.execute("DELETE FROM agents WHERE empid = ?", (empid,))
    c.execute("DELETE FROM evaluations WHERE empid = ?", (empid,))
    conn.commit()
    conn.close()

def get_topics():
    conn = get_connection()
    df = pd.read_sql_query("SELECT * FROM topics", conn)
    conn.close()
    return df.to_dict(orient="records")

def upsert_topic(topic_dict):
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        INSERT INTO topics (id, name, duration, trainer_name, slide_url, form_url)
        VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET
            name=excluded.name,
            duration=excluded.duration,
            trainer_name=excluded.trainer_name,
            slide_url=excluded.slide_url,
            form_url=excluded.form_url
    """, (
        topic_dict['id'], topic_dict['name'], topic_dict.get('duration', ''),
        topic_dict.get('trainer_name', ''), topic_dict.get('slide_url', ''), topic_dict.get('form_url', '')
    ))
    conn.commit()
    conn.close()

def insert_self_training_log(log_id, empid, name, channel, topic_name):
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        INSERT INTO self_training_logs (id, empid, name, channel, topic_name, status)
        VALUES (?, ?, ?, ?, ?, 'In Progress')
    """, (log_id, empid, name, channel, topic_name))
    conn.commit()
    conn.close()

def get_active_agent_training(empid):
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        SELECT *, 
        (strftime('%s', 'now') - strftime('%s', access_time)) / 3600.0 as hours_passed
        FROM self_training_logs 
        WHERE empid = ? AND status IN ('In Progress', 'Delayed')
        ORDER BY access_time DESC LIMIT 1
    """, (empid,))
    row = c.fetchone()
    if row:
        data = dict(row)
        if data['hours_passed'] > 24.0 and data['status'] == 'In Progress':
            c.execute("UPDATE self_training_logs SET status = 'Delayed' WHERE id = ?", (data['id'],))
            conn.commit()
            data['status'] = 'Delayed'
        conn.close()
        return data
    conn.close()
    return None

def mark_self_training_complete(log_id, score=0.0, delay_reason="On Time"):
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        UPDATE self_training_logs 
        SET status = 'Completed', completion_time = CURRENT_TIMESTAMP, quiz_score = ?, delay_reason = ?
        WHERE id = ?
    """, (score, delay_reason, log_id))
    conn.commit()
    conn.close()

def get_self_training_logs():
    conn = get_connection()
    df = pd.read_sql_query("SELECT * FROM self_training_logs ORDER BY access_time DESC", conn)
    conn.close()
    return df.to_dict(orient="records")

def insert_refresher_request(req_dict):
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        INSERT INTO refresher_requests (id, empid, name, channel, topic_name, preferred_slot)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (req_dict['id'], req_dict['empid'], req_dict['name'], req_dict['channel'], req_dict['topic_name'], req_dict['preferred_slot']))
    conn.commit()
    conn.close()

def assign_refresher_by_admin(empid, name, channel, topic_name, preferred_slot):
    insert_refresher_request({
        "id": str(pd.Timestamp.now().timestamp()),
        "empid": empid,
        "name": name,
        "channel": channel,
        "topic_name": topic_name,
        "preferred_slot": preferred_slot
    })

def get_refresher_requests():
    conn = get_connection()
    df = pd.read_sql_query("SELECT * FROM refresher_requests ORDER BY request_time DESC", conn)
    conn.close()
    return df.to_dict(orient="records")

def save_batch_schedule(sched_id, batch_name, start_date, end_date, schedule_json, status="In Progress", edit_reason="Initial Creation", full_schedule_output=None):
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        INSERT INTO batch_schedules (id, batch_name, start_date, end_date, schedule_json, status, edit_reason, last_updated)
        VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
    """, (sched_id, batch_name, start_date, end_date, schedule_json, status, edit_reason))
    conn.commit()
    conn.close()

def update_batch_schedule(sched_id, schedule_json, status="Updated", edit_reason="", full_schedule_output=None):
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        UPDATE batch_schedules
        SET schedule_json = ?, status = ?, edit_reason = ?, last_updated = CURRENT_TIMESTAMP
        WHERE id = ?
    """, (schedule_json, status, edit_reason, sched_id))
    conn.commit()
    conn.close()

def get_batch_schedules():
    conn = get_connection()
    df = pd.read_sql_query("SELECT * FROM batch_schedules ORDER BY last_updated DESC", conn)
    conn.close()
    return df.to_dict(orient="records")

def delete_batch_schedule(sched_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute("DELETE FROM batch_schedules WHERE id = ?", (sched_id,))
    conn.commit()
    conn.close()

def get_induction_evaluations():
    conn = get_connection()
    df = pd.read_sql_query("""
        SELECT a.empid, a.name as agent_name, a.channel,
               COALESCE(e.quiz1, 0.0) as quiz1,
               COALESCE(e.quiz2, 0.0) as quiz2,
               COALESCE(e.quiz3, 0.0) as quiz3,
               COALESCE(e.assignment, 0.0) as assignment,
               COALESCE(e.mock_call, 0.0) as mock_call,
               COALESCE(e.live_comm, 0.0) as live_comm,
               COALESCE(e.final_score, 0.0) as final_score
        FROM agents a
        LEFT JOIN evaluations e ON a.empid = e.empid
        WHERE a.employment_status = 'Induction'
    """, conn)
    conn.close()
    return df.to_dict(orient="records")

def update_evaluation(empid, q1, q2, q3, ass, mock, live, final):
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        INSERT INTO evaluations (empid, quiz1, quiz2, quiz3, assignment, mock_call, live_comm, final_score)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(empid) DO UPDATE SET
            quiz1=excluded.quiz1,
            quiz2=excluded.quiz2,
            quiz3=excluded.quiz3,
            assignment=excluded.assignment,
            mock_call=excluded.mock_call,
            live_comm=excluded.live_comm,
            final_score=excluded.final_score
    """, (empid, q1, q2, q3, ass, mock, live, final))
    conn.commit()
    conn.close()

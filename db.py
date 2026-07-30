import sqlite3

DB_FILE = "training_portal.db"

def get_connection():
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    
    # Agents Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS agents (
            empid TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            phone TEXT
        )
    """)
    
    # Topics Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS topics (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            duration TEXT,
            trainer_name TEXT,
            slide_url TEXT,
            form_url TEXT
        )
    """)
    
    # Self Training Logs
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS self_training_logs (
            id TEXT PRIMARY KEY,
            empid TEXT,
            name TEXT,
            channel TEXT,
            topic_name TEXT,
            access_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Batch Schedules
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS batch_schedules (
            id TEXT PRIMARY KEY,
            batch_name TEXT,
            start_date TEXT,
            end_date TEXT,
            schedule_json TEXT,
            status TEXT
        )
    """)
    
    # Evaluations
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS evaluations (
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
    
    # Refresher Requests
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
    
    conn.commit()
    conn.close()

# --- Helper DB Functions ---

def get_agents():
    conn = get_connection()
    rows = conn.execute("SELECT * FROM agents").fetchall()
    conn.close()
    return [dict(r) for r in rows]

def upsert_agent(empid, name, email, phone):
    conn = get_connection()
    conn.execute("""
        INSERT INTO agents (empid, name, email, phone) 
        VALUES (?, ?, ?, ?)
        ON CONFLICT(empid) DO UPDATE SET name=?, email=?, phone=?
    """, (empid, name, email, phone, name, email, phone))
    
    # Auto Insert or Keep Evaluation entry
    conn.execute("""
        INSERT INTO evaluations (empid, agent_name) 
        VALUES (?, ?)
        ON CONFLICT(empid) DO UPDATE SET agent_name=?
    """, (empid, name, name))
    
    conn.commit()
    conn.close()

def delete_agent(empid):
    conn = get_connection()
    conn.execute("DELETE FROM agents WHERE empid=?", (empid,))
    conn.execute("DELETE FROM evaluations WHERE empid=?", (empid,))
    conn.commit()
    conn.close()

def get_topics():
    conn = get_connection()
    rows = conn.execute("SELECT * FROM topics").fetchall()
    conn.close()
    return [dict(r) for r in rows]

def upsert_topic(topic_dict):
    conn = get_connection()
    conn.execute("""
        INSERT INTO topics (id, name, duration, trainer_name, slide_url, form_url)
        VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET name=?, duration=?, trainer_name=?, slide_url=?, form_url=?
    """, (
        topic_dict['id'], topic_dict['name'], topic_dict['duration'], topic_dict['trainer_name'], topic_dict['slide_url'], topic_dict['form_url'],
        topic_dict['name'], topic_dict['duration'], topic_dict['trainer_name'], topic_dict['slide_url'], topic_dict['form_url']
    ))
    conn.commit()
    conn.close()

def insert_self_training_log(log_id, empid, name, channel, topic_name):
    conn = get_connection()
    conn.execute("INSERT INTO self_training_logs (id, empid, name, channel, topic_name) VALUES (?, ?, ?, ?, ?)",
                 (log_id, empid, name, channel, topic_name))
    conn.commit()
    conn.close()

def get_self_training_logs():
    conn = get_connection()
    rows = conn.execute("SELECT * FROM self_training_logs ORDER BY access_time DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]

def save_batch_schedule(sched_id, batch_name, start_date, end_date, json_str, status):
    conn = get_connection()
    conn.execute("INSERT INTO batch_schedules (id, batch_name, start_date, end_date, schedule_json, status) VALUES (?, ?, ?, ?, ?, ?)",
                 (sched_id, batch_name, start_date, end_date, json_str, status))
    conn.commit()
    conn.close()

def get_batch_schedules():
    conn = get_connection()
    rows = conn.execute("SELECT * FROM batch_schedules ORDER BY rowid DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]

def update_schedule_json_and_status(sched_id, json_str, status=None):
    conn = get_connection()
    if status:
        conn.execute("UPDATE batch_schedules SET schedule_json=?, status=? WHERE id=?", (json_str, status, sched_id))
    else:
        conn.execute("UPDATE batch_schedules SET schedule_json=? WHERE id=?", (json_str, sched_id))
    conn.commit()
    conn.close()

def delete_batch_schedule(sched_id):
    conn = get_connection()
    conn.execute("DELETE FROM batch_schedules WHERE id=?", (sched_id,))
    conn.commit()
    conn.close()

def get_evaluations():
    conn = get_connection()
    rows = conn.execute("SELECT * FROM evaluations").fetchall()
    conn.close()
    return [dict(r) for r in rows]

def update_evaluation(empid, q1, q2, q3, ass, mock, live, final_score):
    conn = get_connection()
    conn.execute("""
        UPDATE evaluations 
        SET quiz1=?, quiz2=?, quiz3=?, assignment=?, mock_call=?, live_comm=?, final_score=?
        WHERE empid=?
    """, (q1, q2, q3, ass, mock, live, final_score, empid))
    conn.commit()
    conn.close()

def insert_refresher_request(req_dict):
    conn = get_connection()
    conn.execute("""
        INSERT INTO refresher_requests (id, empid, name, channel, topic_name, preferred_slot)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (req_dict['id'], req_dict['empid'], req_dict['name'], req_dict['channel'], req_dict['topic_name'], req_dict['preferred_slot']))
    conn.commit()
    conn.close()

def get_refresher_requests():
    conn = get_connection()
    rows = conn.execute("SELECT * FROM refresher_requests ORDER BY rowid DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]

def update_refresher_status(req_id, status, reason="", training_status="Pending"):
    conn = get_connection()
    conn.execute("""
        UPDATE refresher_requests 
        SET status=?, rejection_reason=?, training_status=?
        WHERE id=?
    """, (status, reason, training_status, req_id))
    conn.commit()
    conn.close()

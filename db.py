import sqlite3
import uuid
import pandas as pd
import streamlit as st
import gspread
from google.oauth2.service_account import Credentials

DB_FILE = "training_portal.db"
SPREADSHEET_ID = "1dDmSYFVG_cMEOAZgxaTG4Gd_hPl-S8Dc1XeDgpLCP6U"

def sync_to_gsheet(sheet_name, row_data):
    """Appends a new row to the specified tab in Google Sheets using Sheet ID."""
    try:
        if "gcp_service_account" not in st.secrets:
            st.error("❌ GSheet Sync Failed: 'gcp_service_account' missing in Streamlit Secrets!")
            return

        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
        
        creds_dict = dict(st.secrets["gcp_service_account"])
        
        if "private_key" in creds_dict:
            pk = creds_dict["private_key"]
            pk = pk.replace("\\n", "\n").strip()
            if pk.startswith('"') and pk.endswith('"'):
                pk = pk[1:-1]
            creds_dict["private_key"] = pk

        creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
        gc = gspread.authorize(creds)
        
        sh = gc.open_by_key(SPREADSHEET_ID)
        
        try:
            worksheet = sh.worksheet(sheet_name)
        except gspread.exceptions.WorksheetNotFound:
            worksheet = sh.add_worksheet(title=sheet_name, rows="1000", cols="20")
        
        worksheet.append_row(row_data)
        st.toast(f"✅ Synced to Google Sheet: {sheet_name}")
        
    except Exception as e:
        st.error(f"❌ GSheet Sync Error ({sheet_name}): {e}")

def get_connection():
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def add_column_if_not_exists(cursor, table_name, column_name, column_def):
    """Helper to safely add a column to an existing table."""
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = [row[1] for row in cursor.fetchall()]
    if column_name not in columns:
        cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_def}")

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    
    # 1. Agents Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS agents (
            empid TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            phone TEXT,
            channel TEXT DEFAULT '',
            employment_status TEXT DEFAULT 'Induction'
        )
    """)
    add_column_if_not_exists(cursor, "agents", "channel", "TEXT DEFAULT ''")
    add_column_if_not_exists(cursor, "agents", "employment_status", "TEXT DEFAULT 'Induction'")

    # 2. Topics Table
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
    
    # 3. Self Training Logs
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS self_training_logs (
            id TEXT PRIMARY KEY,
            empid TEXT,
            name TEXT,
            channel TEXT,
            topic_name TEXT,
            access_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status TEXT DEFAULT 'In Progress'
        )
    """)
    add_column_if_not_exists(cursor, "self_training_logs", "status", "TEXT DEFAULT 'In Progress'")
    
    # 4. Batch Schedules
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
    
    # 5. Evaluations
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
    
    # 6. Refresher Requests
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
    add_column_if_not_exists(cursor, "refresher_requests", "training_status", "TEXT DEFAULT 'Pending'")

    conn.commit()
    
    # Seeding Default Topics
    exact_topics = [
        ("t1", "Fare", "02:00 HR", "Md Asikul islam Azman", "https://docs.google.com/presentation/d/136RdIr9tshx3OMd8nFRhCj_aTo84p9c-XAJFKDrrw-k/embed", ""),
        ("t2", "Joining Process", "02:00 HR", "Md Asikul islam Azman", "https://docs.google.com/presentation/d/1AxdbPQSPr0Cmlx9HjZPS_jHtj-xgjNMGlXHZcfF9MQ4/embed", ""),
        ("t3", "Star Program", "02:00 HR", "Md Asikul islam Azman", "https://docs.google.com/presentation/d/1SbNxrXajQlZIpT6fvT_a9bXwmIhl1dQZh2olZ0s8lMI/embed", ""),
        ("t4", "Payment", "02:00 HR", "Md Asikul islam Azman", "https://docs.google.com/presentation/d/1Q9ous8zu6CmPe2Yw8oTKS-FkPKHUOHPT/embed", ""),
        ("t5", "User SOP", "02:00 HR", "Md Asikul islam Azman", "https://docs.google.com/presentation/d/1TCkGIRTbQ87ZmW8vZM4WS2nN237GzQWi/embed", ""),
        ("t6", "Rider SOP", "02:00 HR", "Md Asikul islam Azman", "https://docs.google.com/presentation/d/1A28xX9YdsEuHOIGEPfEigQ6C_azRmNap/embed", ""),
        ("t7", "QA Parameters", "02:00 HR", "Md Asikul islam Azman", "https://docs.google.com/presentation/d/1IT7U4N88rSaHSsbVPqY5K03kfKA3iddW98VT9lsPLVM/embed", ""),
        ("t8", "Pathao Internal Tools", "02:00 HR", "Md Asikul islam Azman", "https://docs.google.com/presentation/d/1UZQiOydwqm9etUb8MzEDXwGHbLipc30O/embed", "")
    ]
    
    for t in exact_topics:
        cursor.execute("""
            INSERT INTO topics (id, name, duration, trainer_name, slide_url, form_url)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET name=excluded.name, slide_url=excluded.slide_url
        """, (t[0], t[1], t[2], t[3], t[4], t[5]))
        
    conn.commit()
    conn.close()

# --- Agent Management ---

def get_agents():
    conn = get_connection()
    rows = conn.execute("SELECT * FROM agents").fetchall()
    conn.close()
    return [dict(r) for r in rows]

def upsert_agent(empid, name, email, phone="", channel="", employment_status="Induction"):
    conn = get_connection()
    conn.execute("""
        INSERT INTO agents (empid, name, email, phone, channel, employment_status) 
        VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT(empid) DO UPDATE SET 
            name=excluded.name, 
            email=excluded.email, 
            phone=excluded.phone,
            channel=excluded.channel,
            employment_status=excluded.employment_status
    """, (empid, name, email, phone, channel, employment_status))
    
    conn.execute("""
        INSERT INTO evaluations (empid, agent_name) 
        VALUES (?, ?)
        ON CONFLICT(empid) DO UPDATE SET agent_name=excluded.agent_name
    """, (empid, name))
    
    conn.commit()
    conn.close()

def update_agent_status(empid, new_status):
    conn = get_connection()
    conn.execute("UPDATE agents SET employment_status=? WHERE empid=?", (new_status, empid))
    conn.commit()
    conn.close()

def bulk_upsert_agents(df):
    conn = get_connection()
    for _, row in df.iterrows():
        empid = str(row.get('EMP ID', '')).strip()
        name = str(row.get('Name', '')).strip()
        email = str(row.get('Email', '')).strip()
        channel = str(row.get('Channel', '')).strip()
        emp_status = str(row.get('Employment Status', 'Induction')).strip()
        
        if emp_status not in ["Existing", "Resigned", "Induction"]:
            emp_status = "Induction"

        if empid and name:
            conn.execute("""
                INSERT INTO agents (empid, name, email, phone, channel, employment_status) 
                VALUES (?, ?, ?, '', ?, ?)
                ON CONFLICT(empid) DO UPDATE SET 
                    name=excluded.name, 
                    email=excluded.email, 
                    channel=excluded.channel,
                    employment_status=excluded.employment_status
            """, (empid, name, email, channel, emp_status))
            
            conn.execute("""
                INSERT INTO evaluations (empid, agent_name) 
                VALUES (?, ?)
                ON CONFLICT(empid) DO UPDATE SET agent_name=excluded.agent_name
            """, (empid, name))
            
    conn.commit()
    conn.close()

def delete_agent(empid):
    conn = get_connection()
    conn.execute("DELETE FROM agents WHERE empid=?", (empid,))
    conn.execute("DELETE FROM evaluations WHERE empid=?", (empid,))
    conn.commit()
    conn.close()

# --- Self Training Core Logic ---

def get_active_agent_training(empid):
    """Checks if the agent has an unfinished ('In Progress') training."""
    conn = get_connection()
    row = conn.execute("""
        SELECT * FROM self_training_logs 
        WHERE empid = ? AND status = 'In Progress' 
        ORDER BY access_time DESC LIMIT 1
    """, (empid,)).fetchone()
    conn.close()
    return dict(row) if row else None

def insert_self_training_log(log_id, empid, name, channel, topic_name):
    """Creates a new self-training log with status 'In Progress'."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO self_training_logs (id, empid, name, channel, topic_name, status) 
        VALUES (?, ?, ?, ?, ?, 'In Progress')
    """, (log_id, empid, name, channel, topic_name))
    conn.commit()
    
    row = cursor.execute("SELECT access_time FROM self_training_logs WHERE id=?", (log_id,)).fetchone()
    access_time = row['access_time'] if row else ""
    conn.close()

    sync_to_gsheet("Self Training Log", [log_id, empid, name, channel, topic_name, str(access_time), "In Progress"])

def mark_self_training_complete(log_id):
    """Updates status to 'Completed' in DB and syncs status to GSheet."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE self_training_logs SET status = 'Completed' WHERE id = ?", (log_id,))
    
    row = cursor.execute("SELECT empid, name, channel, topic_name, access_time FROM self_training_logs WHERE id=?", (log_id,)).fetchone()
    conn.commit()
    conn.close()

    if row:
        sync_to_gsheet("Self Training Log", [log_id, row['empid'], row['name'], row['channel'], row['topic_name'], str(row['access_time']), "Completed"])

def get_self_training_logs():
    conn = get_connection()
    rows = conn.execute("SELECT * FROM self_training_logs ORDER BY access_time DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]

# --- Other DB Functions ---

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

def save_batch_schedule(sched_id, batch_name, start_date, end_date, json_str, status, full_schedule_output=None):
    conn = get_connection()
    conn.execute("INSERT INTO batch_schedules (id, batch_name, start_date, end_date, schedule_json, status) VALUES (?, ?, ?, ?, ?, ?)",
                 (sched_id, batch_name, start_date, end_date, json_str, status))
    conn.commit()
    conn.close()

    if full_schedule_output and isinstance(full_schedule_output, list):
        for item in full_schedule_output:
            sync_to_gsheet("Induction Calender", [
                batch_name,
                item.get("Date", ""),
                item.get("Day", ""),
                item.get("Activity / Topic", ""),
                item.get("Time Slot", ""),
                item.get("Trainer", ""),
                item.get("Status", "")
            ])

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
    conn.commit().close()

def get_evaluations():
    conn = get_connection()
    rows = conn.execute("SELECT * FROM evaluations").fetchall()
    conn.close()
    return [dict(r) for r in rows]

def update_evaluation(empid, q1, q2, q3, ass, mock, live, final_score):
    conn = get_connection()
    row = conn.execute("SELECT agent_name FROM evaluations WHERE empid=?", (empid,)).fetchone()
    agent_name = row['agent_name'] if row else ""
    
    conn.execute("""
        UPDATE evaluations 
        SET quiz1=?, quiz2=?, quiz3=?, assignment=?, mock_call=?, live_comm=?, final_score=?
        WHERE empid=?
    """, (q1, q2, q3, ass, mock, live, final_score, empid))
    conn.commit()
    conn.close()

    sync_to_gsheet("Agent Evaluation", [empid, agent_name, q1, q2, q3, ass, mock, live, final_score])

def insert_refresher_request(req_dict):
    conn = get_connection()
    conn.execute("""
        INSERT INTO refresher_requests (id, empid, name, channel, topic_name, preferred_slot)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (req_dict['id'], req_dict['empid'], req_dict['name'], req_dict['channel'], req_dict['topic_name'], req_dict['preferred_slot']))
    conn.commit()
    conn.close()

    sync_to_gsheet("Refresher Requests", [
        req_dict['id'],
        req_dict['empid'],
        req_dict['name'],
        req_dict['channel'],
        req_dict['topic_name'],
        req_dict['preferred_slot'],
        "Pending"
    ])

def assign_refresher_by_admin(empid, name, channel, topic_name, preferred_slot):
    req_id = str(uuid.uuid4())
    conn = get_connection()
    conn.execute("""
        INSERT INTO refresher_requests (id, empid, name, channel, topic_name, preferred_slot, status, training_status)
        VALUES (?, ?, ?, ?, ?, ?, 'Assigned by Admin', 'Pending')
    """, (req_id, empid, name, channel, topic_name, preferred_slot))
    conn.commit()
    conn.close()

    sync_to_gsheet("Refresher Requests", [
        req_id,
        empid,
        name,
        channel,
        topic_name,
        preferred_slot,
        "Assigned by Admin"
    ])

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

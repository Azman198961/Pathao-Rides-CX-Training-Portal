import sqlite3
import pandas as pd
import streamlit as st
import gspread
from google.oauth2.service_account import Credentials

DB_FILE = "training_portal.db"
SPREADSHEET_NAME = "Rides CX Training Portal"

# Google Sheet Sync Helper using Streamlit Secrets
def sync_to_gsheet(sheet_name, row_data):
    """Appends a new row to the specified tab in Google Sheets using Streamlit Secrets."""
    try:
        if "gcp_service_account" not in st.secrets:
            print("GSheet Sync Warning: 'gcp_service_account' not found in st.secrets.")
            return

        scopes = ["https://www.googleapis.com/auth/spreadsheets"]
        creds_dict = dict(st.secrets["gcp_service_account"])
        creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
        
        gc = gspread.authorize(creds)
        sh = gc.open(SPREADSHEET_NAME)
        worksheet = sh.worksheet(sheet_name)
        worksheet.append_row(row_data)
        print(f"Successfully synced to GSheet tab: {sheet_name}")
    except Exception as e:
        print(f"GSheet Sync Error ({sheet_name}): {e}")

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
    
    # --- Exact 8 Topics Seeding ---
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
            ON CONFLICT(id) DO UPDATE SET name=?, slide_url=?
        """, (t[0], t[1], t[2], t[3], t[4], t[5], t[1], t[4]))
        
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
    cursor = conn.cursor()
    cursor.execute("INSERT INTO self_training_logs (id, empid, name, channel, topic_name) VALUES (?, ?, ?, ?, ?)",
                   (log_id, empid, name, channel, topic_name))
    conn.commit()
    
    row = cursor.execute("SELECT access_time FROM self_training_logs WHERE id=?", (log_id,)).fetchone()
    access_time = row['access_time'] if row else ""
    conn.close()

    # Sync to Google Sheets: "Self Training Log"
    sync_to_gsheet("Self Training Log", [log_id, empid, name, channel, topic_name, str(access_time)])

def get_self_training_logs():
    conn = get_connection()
    rows = conn.execute("SELECT * FROM self_training_logs ORDER BY access_time DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]

def save_batch_schedule(sched_id, batch_name, start_date, end_date, json_str, status, full_schedule_output=None):
    conn = get_connection()
    conn.execute("INSERT INTO batch_schedules (id, batch_name, start_date, end_date, schedule_json, status) VALUES (?, ?, ?, ?, ?, ?)",
                 (sched_id, batch_name, start_date, end_date, json_str, status))
    conn.commit()
    conn.close()

    # Sync each slot item to Google Sheets: "Induction Calender"
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
    conn.commit()
    conn.close()

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

    # Sync to Google Sheets: "Agent Evaluation"
    sync_to_gsheet("Agent Evaluation", [empid, agent_name, q1, q2, q3, ass, mock, live, final_score])

def insert_refresher_request(req_dict):
    conn = get_connection()
    conn.execute("""
        INSERT INTO refresher_requests (id, empid, name, channel, topic_name, preferred_slot)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (req_dict['id'], req_dict['empid'], req_dict['name'], req_dict['channel'], req_dict['topic_name'], req_dict['preferred_slot']))
    conn.commit()
    conn.close()

    # Sync to Google Sheets: "Refresher Requests"
    sync_to_gsheet("Refresher Requests", [
        req_dict['id'],
        req_dict['empid'],
        req_dict['name'],
        req_dict['channel'],
        req_dict['topic_name'],
        req_dict['preferred_slot'],
        "Pending"
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

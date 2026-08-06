import sqlite3
import pandas as pd
import streamlit as st
import gspread
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from google.oauth2.service_account import Credentials
from datetime import datetime, timedelta, timezone

# Bangladesh Standard Timezone Setup (UTC +6 Hours)
BST = timezone(timedelta(hours=6))

def get_current_bst_time():
    """Returns current date and time formatted in Bangladesh Standard Time (BST)."""
    return datetime.now(BST).strftime("%Y-%m-%d %H:%M:%S")

DB_FILE = "training_portal.db"
SPREADSHEET_NAME = "Rides CX Training Portal"

def send_delayed_email(agent_email, agent_name, topic_name):
    """Sends an automated email notification when a training becomes delayed."""
    try:
        if "smtp" not in st.secrets:
            return

        smtp_server = st.secrets["smtp"]["server"]
        smtp_port = st.secrets["smtp"]["port"]
        sender_email = st.secrets["smtp"]["sender_email"]
        sender_password = st.secrets["smtp"]["sender_password"]

        msg = MIMEMultipart()
        msg['From'] = f"Pathao CX Academy <{sender_email}>"
        msg['To'] = agent_email
        msg['Subject'] = f"🔴 Training Delayed Alert: {topic_name}"

        body = f"""
        Dear {agent_name},

        Your self-training module "{topic_name}" has crossed the 24-hour limit and is now marked as DELAYED.

        Please log in to the Pathao CX Training Portal immediately, provide the reason for the delay, and submit your quiz assessment to complete the module.

        Best regards,
        Pathao CX Quality & Training Team
        """
        
        msg.attach(MIMEText(body, 'plain'))

        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(sender_email, sender_password)
        server.send_message(msg)
        server.quit()
        st.toast(f"📧 Delay email sent to {agent_email}")
    except Exception as e:
        st.error(f"❌ Failed to send delay email to {agent_email}: {e}")

def sync_to_gsheet(sheet_name, row_data):
    """Appends a new row to the specified tab in Google Sheets using Streamlit Secrets."""
    try:
        if "gcp_service_account" not in st.secrets:
            return

        scopes = ["https://www.googleapis.com/auth/spreadsheets"]
        creds_dict = dict(st.secrets["gcp_service_account"])
        creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
        
        gc = gspread.authorize(creds)
        sh = gc.open(SPREADSHEET_NAME)
        worksheet = sh.worksheet(sheet_name)
        worksheet.append_row(row_data)
        
        st.toast(f"✅ Synced to Google Sheet: {sheet_name}")
    except Exception as e:
        st.error(f"❌ GSheet Sync Failed ({sheet_name}): {e}")

def get_connection():
    conn = sqlite3.connect(DB_FILE, timeout=30, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    
    # Employees Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS agents (
            empid TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            phone TEXT,
            channel TEXT DEFAULT 'Inbound Voice',
            employment_status TEXT DEFAULT 'Induction'
        )
    """)
    
    # Schema Migration Check for older databases
    cursor.execute("PRAGMA table_info(agents)")
    columns = [col[1] for col in cursor.fetchall()]
    if 'employment_status' not in columns:
        cursor.execute("ALTER TABLE agents ADD COLUMN employment_status TEXT DEFAULT 'Induction'")
    if 'channel' not in columns:
        cursor.execute("ALTER TABLE agents ADD COLUMN channel TEXT DEFAULT 'Inbound Voice'")
    
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
    
    # Self Training Logs Table with Status & Delays
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS self_training_logs (
            id TEXT PRIMARY KEY,
            empid TEXT,
            name TEXT,
            channel TEXT,
            topic_name TEXT,
            quiz_score REAL DEFAULT 0.0,
            access_time TIMESTAMP,
            status TEXT DEFAULT 'In Progress',
            start_time TIMESTAMP,
            completion_time TIMESTAMP,
            delay_reason TEXT DEFAULT ''
        )
    """)
    
    cursor.execute("PRAGMA table_info(self_training_logs)")
    log_cols = [col[1] for col in cursor.fetchall()]
    if 'quiz_score' not in log_cols:
        cursor.execute("ALTER TABLE self_training_logs ADD COLUMN quiz_score REAL DEFAULT 0.0")
    if 'status' not in log_cols:
        cursor.execute("ALTER TABLE self_training_logs ADD COLUMN status TEXT DEFAULT 'In Progress'")
    if 'start_time' not in log_cols:
        cursor.execute("ALTER TABLE self_training_logs ADD COLUMN start_time TIMESTAMP")
    if 'completion_time' not in log_cols:
        cursor.execute("ALTER TABLE self_training_logs ADD COLUMN completion_time TIMESTAMP")
    if 'delay_reason' not in log_cols:
        cursor.execute("ALTER TABLE self_training_logs ADD COLUMN delay_reason TEXT DEFAULT ''")

    # Batch Schedules
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS batch_schedules (
            id TEXT PRIMARY KEY,
            batch_name TEXT,
            start_date TEXT,
            end_date TEXT,
            schedule_json TEXT,
            status TEXT,
            edit_history_json TEXT DEFAULT '[]'
        )
    """)
    
    cursor.execute("PRAGMA table_info(batch_schedules)")
    sched_cols = [col[1] for col in cursor.fetchall()]
    if 'edit_history_json' not in sched_cols:
        cursor.execute("ALTER TABLE batch_schedules ADD COLUMN edit_history_json TEXT DEFAULT '[]'")

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
    
    # Exact 8 Topics Seeding
    exact_topics = [
        ("t1", "Fare", "02:00 HR", "Md Asikul islam Azman", 
         "https://docs.google.com/presentation/d/136RdIr9tshx3OMd8nFRhCj_aTo84p9c-XAJFKDrrw-k/embed", 
         "https://docs.google.com/forms/d/e/1FAIpQLSc_EXAMPLE_FARE/viewform?embedded=true"),
        ("t2", "Joining Process", "02:00 HR", "Md Asikul islam Azman", 
         "https://docs.google.com/presentation/d/1AxdbPQSPr0Cmlx9HjZPS_jHtj-xgjNMGlXHZcfF9MQ4/embed", 
         "https://docs.google.com/forms/d/e/1FAIpQLSc_EXAMPLE_JOINING/viewform?embedded=true"),
        ("t3", "Star Program", "02:00 HR", "Md Asikul islam Azman", 
         "https://docs.google.com/presentation/d/1SbNxrXajQlZIpT6fvT_a9bXwmIhl1dQZh2olZ0s8lMI/embed", 
         "https://docs.google.com/forms/d/e/1FAIpQLSc_EXAMPLE_STAR/viewform?embedded=true"),
        ("t4", "Payment", "02:00 HR", "Md Asikul islam Azman", 
         "https://docs.google.com/presentation/d/1Q9ous8zu6CmPe2Yw8oTKS-FkPKHUOHPT/embed", 
         "https://docs.google.com/forms/d/e/1FAIpQLSc_EXAMPLE_PAYMENT/viewform?embedded=true"),
        ("t5", "User SOP", "02:00 HR", "Md Asikul islam Azman", 
         "https://docs.google.com/presentation/d/1TCkGIRTbQ87ZmW8vZM4WS2nN237GzQWi/embed", 
         "https://docs.google.com/forms/d/e/1FAIpQLSc_EXAMPLE_USER_SOP/viewform?embedded=true"),
        ("t6", "Rider SOP", "02:00 HR", "Md Asikul islam Azman", 
         "https://docs.google.com/presentation/d/1A28xX9YdsEuHOIGEPfEigQ6C_azRmNap/embed", 
         "https://docs.google.com/forms/d/e/1FAIpQLSc_EXAMPLE_RIDER_SOP/viewform?embedded=true"),
        ("t7", "QA Parameters", "02:00 HR", "Md Asikul islam Azman", 
         "https://docs.google.com/presentation/d/1IT7U4N88rSaHSsbVPqY5K03kfKA3iddW98VT9lsPLVM/embed", 
         "https://docs.google.com/forms/d/e/1FAIpQLSc_EXAMPLE_QA/viewform?embedded=true"),
        ("t8", "Pathao Internal Tools", "02:00 HR", "Md Asikul islam Azman", 
         "https://docs.google.com/presentation/d/1UZQiOydwqm9etUb8MzEDXwGHbLipc30O/embed", 
         "https://docs.google.com/forms/d/e/1FAIpQLSc_EXAMPLE_TOOLS/viewform?embedded=true")
    ]
    
    for t in exact_topics:
        cursor.execute("""
            INSERT INTO topics (id, name, duration, trainer_name, slide_url, form_url)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET name=?, slide_url=?, form_url=?
        """, (t[0], t[1], t[2], t[3], t[4], t[5], t[1], t[4], t[5]))
        
    conn.commit()
    conn.close()

def auto_update_delayed_trainings():
    """Checks for 'In Progress' training sessions older than 24 hours (BST), updates status to 'Delayed', and sends email."""
    conn = get_connection()
    cutoff_time = (datetime.now(BST) - timedelta(hours=24)).strftime("%Y-%m-%d %H:%M:%S")
    
    # 1. Fetch trainings that are about to be marked as Delayed
    delayed_rows = conn.execute("""
        SELECT l.id, l.empid, l.name, l.topic_name, a.email 
        FROM self_training_logs l
        LEFT JOIN agents a ON l.empid = a.empid
        WHERE l.status = 'In Progress' AND (l.start_time <= ? OR (l.start_time IS NULL AND l.access_time <= ?))
    """, (cutoff_time, cutoff_time)).fetchall()

    # 2. Update status in database
    conn.execute("""
        UPDATE self_training_logs 
        SET status = 'Delayed' 
        WHERE status = 'In Progress' AND (start_time <= ? OR (start_time IS NULL AND access_time <= ?))
    """, (cutoff_time, cutoff_time))
    conn.commit()
    conn.close()

    # 3. Send notification email to each delayed agent
    for row in delayed_rows:
        agent_email = row['email']
        agent_name = row['name']
        topic_name = row['topic_name']
        if agent_email:
            send_delayed_email(agent_email, agent_name, topic_name)

def get_agents(status_filter=None):
    conn = get_connection()
    if status_filter:
        rows = conn.execute("SELECT * FROM agents WHERE employment_status=?", (status_filter,)).fetchall()
    else:
        rows = conn.execute("SELECT * FROM agents").fetchall()
    conn.close()
    return [dict(r) for r in rows]

def upsert_agent(empid, name, email, phone="", channel="Inbound Voice", employment_status="Induction"):
    conn = get_connection()
    conn.execute("""
        INSERT INTO agents (empid, name, email, phone, channel, employment_status) 
        VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT(empid) DO UPDATE SET name=?, email=?, phone=?, channel=?, employment_status=?
    """, (empid, name, email, phone, channel, employment_status, name, email, phone, channel, employment_status))
    
    if employment_status == 'Induction':
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

def insert_self_training_log(log_id, empid, name, channel, topic_name, quiz_score=0.0):
    conn = get_connection()
    cursor = conn.cursor()
    now_str = get_current_bst_time()
    cursor.execute("""
        INSERT INTO self_training_logs (id, empid, name, channel, topic_name, quiz_score, status, start_time, access_time) 
        VALUES (?, ?, ?, ?, ?, ?, 'In Progress', ?, ?)
    """, (log_id, empid, name, channel, topic_name, quiz_score, now_str, now_str))
    conn.commit()
    conn.close()

    sync_to_gsheet("Self Training Log", [log_id, empid, name, channel, topic_name, quiz_score, now_str, "In Progress", "", ""])

def get_active_self_training(empid):
    """Fetches any active or delayed training for the given EMP ID."""
    auto_update_delayed_trainings()
    conn = get_connection()
    row = conn.execute("""
        SELECT * FROM self_training_logs 
        WHERE empid = ? AND status IN ('In Progress', 'Delayed')
        ORDER BY start_time DESC LIMIT 1
    """, (empid,)).fetchone()
    conn.close()
    return dict(row) if row else None

def complete_self_training_log(log_id, quiz_score=0.0, delay_reason=""):
    conn = get_connection()
    now_str = get_current_bst_time()
    conn.execute("""
        UPDATE self_training_logs 
        SET status = 'Completed', completion_time = ?, quiz_score = ?, delay_reason = ?
        WHERE id = ?
    """, (now_str, quiz_score, delay_reason, log_id))
    conn.commit()
    
    row = conn.execute("SELECT * FROM self_training_logs WHERE id=?", (log_id,)).fetchone()
    conn.close()
    if row:
        r = dict(row)
        sync_to_gsheet("Self Training Log", [r['id'], r['empid'], r['name'], r['channel'], r['topic_name'], quiz_score, str(r['access_time']), "Completed", str(now_str), delay_reason])

def update_self_training_score(log_id, quiz_score):
    conn = get_connection()
    conn.execute("UPDATE self_training_logs SET quiz_score=? WHERE id=?", (quiz_score, log_id))
    conn.commit()
    conn.close()

def get_self_training_logs():
    auto_update_delayed_trainings()
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

def update_batch_schedule_full(sched_id, json_str, edit_history_json, status=None):
    conn = get_connection()
    if status:
        conn.execute("UPDATE batch_schedules SET schedule_json=?, edit_history_json=?, status=? WHERE id=?", (json_str, edit_history_json, status, sched_id))
    else:
        conn.execute("UPDATE batch_schedules SET schedule_json=?, edit_history_json=? WHERE id=?", (json_str, edit_history_json, sched_id))
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
        conn.execute("UPDATE batch_schedules SET schedule_json=? WHERE id=?", (json_str, status, sched_id))
    conn.commit()
    conn.close()

def delete_batch_schedule(sched_id):
    conn = get_connection()
    conn.execute("DELETE FROM batch_schedules WHERE id=?", (sched_id,))
    conn.commit()
    conn.close()

def get_induction_evaluations():
    conn = get_connection()
    rows = conn.execute("""
        SELECT e.* FROM evaluations e
        INNER JOIN agents a ON e.empid = a.empid
        WHERE a.employment_status = 'Induction'
    """).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_evaluations():
    conn = get_connection()
    rows = conn.execute("SELECT * FROM evaluations").fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_evaluation_by_id(empid):
    conn = get_connection()
    row = conn.execute("SELECT * FROM evaluations WHERE empid=?", (empid,)).fetchone()
    conn.close()
    return dict(row) if row else None

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

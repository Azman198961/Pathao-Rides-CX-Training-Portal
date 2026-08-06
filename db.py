import sqlite3
import json
import smtplib
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

DB_NAME = "portal.db"

def get_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    
    # 1. Agents Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS agents (
            empid TEXT PRIMARY KEY,
            name TEXT,
            email TEXT,
            channel TEXT,
            employment_status TEXT DEFAULT 'Induction'
        )
    ''')
    
    # 2. Topics Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS topics (
            id TEXT PRIMARY KEY,
            name TEXT UNIQUE,
            duration TEXT,
            trainer_name TEXT,
            slide_url TEXT,
            form_url TEXT
        )
    ''')

    # 3. Batch Schedules / Calendars
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS batch_schedules (
            id TEXT PRIMARY KEY,
            batch_name TEXT,
            start_date TEXT,
            end_date TEXT,
            schedule_json TEXT,
            status TEXT,
            last_updated TEXT,
            edit_reason TEXT
        )
    ''')

    # 4. Induction Evaluations
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS induction_evaluations (
            empid TEXT PRIMARY KEY,
            quiz1 REAL DEFAULT 0.0,
            quiz2 REAL DEFAULT 0.0,
            quiz3 REAL DEFAULT 0.0,
            assignment REAL DEFAULT 0.0,
            mock_call REAL DEFAULT 0.0,
            live_comm REAL DEFAULT 0.0,
            final_score REAL DEFAULT 0.0
        )
    ''')

    # 5. Self Training Logs (Includes Delay Logic Fields)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS self_training_logs (
            id TEXT PRIMARY KEY,
            empid TEXT,
            name TEXT,
            channel TEXT,
            topic_name TEXT,
            access_time TEXT,
            status TEXT,
            quiz_score REAL DEFAULT 0.0,
            delay_reason TEXT
        )
    ''')

    # 6. Refresher Requests
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS refresher_requests (
            id TEXT PRIMARY KEY,
            empid TEXT,
            name TEXT,
            channel TEXT,
            topic_name TEXT,
            preferred_slot TEXT,
            status TEXT DEFAULT 'Pending'
        )
    ''')

    conn.commit()
    conn.close()

# ----------------- EMAIL NOTIFICATION SYSTEM -----------------

def send_delay_email(agent_empid, agent_name, topic_name, access_time):
    # Gmail SMTP Credentials
    SENDER_EMAIL = "asikul.islam@pathao.com"  # আপনার ইমেইল আইডি
    SENDER_PASSWORD = "nbjpnsbbaslhuozn"    # Google App Password

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT email FROM agents WHERE empid = ?", (agent_empid,))
    agent_row = cursor.fetchone()
    conn.close()
    
    receiver_email = agent_row['email'] if agent_row and agent_row['email'] else SENDER_EMAIL

    subject = f"⚠️ Overdue Training Alert: {topic_name} (Delayed)"
    
    body = f"""
    Hi {agent_name},

    System generated alert: You started the self-training module "{topic_name}" on {access_time}. 
    More than 24 hours have passed, and the module has not been completed yet.

    Status: MARKED AS DELAYED 🔴

    Please log in to the CX Training Portal as soon as possible to review the module and submit the quiz. 
    Note: You will be required to provide a valid reason for this delay prior to final quiz submission.

    Best regards,
    Pathao CX Training Automation System
    """

    msg = MIMEMultipart()
    msg['From'] = SENDER_EMAIL
    msg['To'] = receiver_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.send_message(msg)
        server.quit()
        print(f"✅ Delay notification email sent to {receiver_email}")
    except Exception as e:
        print(f"❌ Failed to send email: {e}")

# ----------------- AGENT DIRECTORY -----------------

def get_agents():
    conn = get_connection()
    agents = conn.execute("SELECT * FROM agents").fetchall()
    conn.close()
    return [dict(a) for a in agents]

def upsert_agent(empid, name, email, channel, employment_status='Induction'):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO agents (empid, name, email, channel, employment_status)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(empid) DO UPDATE SET
            name=excluded.name,
            email=excluded.email,
            channel=excluded.channel,
            employment_status=excluded.employment_status
    ''', (empid, name, email, channel, employment_status))
    conn.commit()
    conn.close()

def update_agent_status(empid, status):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE agents SET employment_status = ? WHERE empid = ?", (status, empid))
    conn.commit()
    conn.close()

def delete_agent(empid):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM agents WHERE empid = ?", (empid,))
    conn.commit()
    conn.close()

def bulk_upsert_agents(df):
    conn = get_connection()
    cursor = conn.cursor()
    for _, row in df.iterrows():
        empid = str(row.get('empid', '')).strip()
        name = str(row.get('name', '')).strip()
        email = str(row.get('email', '')).strip()
        channel = str(row.get('channel', 'Inbound Voice')).strip()
        status = str(row.get('employment_status', 'Induction')).strip()
        
        if empid:
            cursor.execute('''
                INSERT INTO agents (empid, name, email, channel, employment_status)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(empid) DO UPDATE SET
                    name=excluded.name,
                    email=excluded.email,
                    channel=excluded.channel,
                    employment_status=excluded.employment_status
            ''', (empid, name, email, channel, status))
    conn.commit()
    conn.close()

# ----------------- TOPICS -----------------

def get_topics():
    conn = get_connection()
    topics = conn.execute("SELECT * FROM topics").fetchall()
    conn.close()
    return [dict(t) for t in topics]

def upsert_topic(topic_dict):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO topics (id, name, duration, trainer_name, slide_url, form_url)
        VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET
            name=excluded.name,
            duration=excluded.duration,
            trainer_name=excluded.trainer_name,
            slide_url=excluded.slide_url,
            form_url=excluded.form_url
    ''', (
        topic_dict['id'], topic_dict['name'], topic_dict.get('duration', ''),
        topic_dict.get('trainer_name', ''), topic_dict.get('slide_url', ''),
        topic_dict.get('form_url', '')
    ))
    conn.commit()
    conn.close()

# ----------------- CALENDAR / BATCH SCHEDULES -----------------

def save_batch_schedule(sched_id, batch_name, start_date, end_date, schedule_json, status, edit_reason="", full_schedule_output=None):
    conn = get_connection()
    cursor = conn.cursor()
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute('''
        INSERT INTO batch_schedules (id, batch_name, start_date, end_date, schedule_json, status, last_updated, edit_reason)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (sched_id, batch_name, start_date, end_date, schedule_json, status, now_str, edit_reason))
    conn.commit()
    conn.close()

def update_batch_schedule(sched_id, schedule_json, status, edit_reason, full_schedule_output=None):
    conn = get_connection()
    cursor = conn.cursor()
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute('''
        UPDATE batch_schedules 
        SET schedule_json = ?, status = ?, last_updated = ?, edit_reason = ?
        WHERE id = ?
    ''', (schedule_json, status, now_str, edit_reason, sched_id))
    conn.commit()
    conn.close()

def get_batch_schedules():
    conn = get_connection()
    schedules = conn.execute("SELECT * FROM batch_schedules ORDER BY last_updated DESC").fetchall()
    conn.close()
    return [dict(s) for s in schedules]

def delete_batch_schedule(sched_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM batch_schedules WHERE id = ?", (sched_id,))
    conn.commit()
    conn.close()

# ----------------- INDUCTION EVALUATIONS -----------------

def get_induction_evaluations():
    conn = get_connection()
    query = '''
        SELECT a.empid, a.name as agent_name, a.channel,
               COALESCE(e.quiz1, 0.0) as quiz1,
               COALESCE(e.quiz2, 0.0) as quiz2,
               COALESCE(e.quiz3, 0.0) as quiz3,
               COALESCE(e.assignment, 0.0) as assignment,
               COALESCE(e.mock_call, 0.0) as mock_call,
               COALESCE(e.live_comm, 0.0) as live_comm,
               COALESCE(e.final_score, 0.0) as final_score
        FROM agents a
        LEFT JOIN induction_evaluations e ON a.empid = e.empid
        WHERE a.employment_status = 'Induction'
    '''
    rows = conn.execute(query).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def update_evaluation(empid, quiz1, quiz2, quiz3, assignment, mock_call, live_comm, final_score):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO induction_evaluations (empid, quiz1, quiz2, quiz3, assignment, mock_call, live_comm, final_score)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(empid) DO UPDATE SET
            quiz1=excluded.quiz1,
            quiz2=excluded.quiz2,
            quiz3=excluded.quiz3,
            assignment=excluded.assignment,
            mock_call=excluded.mock_call,
            live_comm=excluded.live_comm,
            final_score=excluded.final_score
    ''', (empid, quiz1, quiz2, quiz3, assignment, mock_call, live_comm, final_score))
    conn.commit()
    conn.close()

# ----------------- SELF TRAINING LOGS & 24H DELAY LOGIC -----------------

def insert_self_training_log(log_id, empid, name, channel, topic_name):
    conn = get_connection()
    cursor = conn.cursor()
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute('''
        INSERT INTO self_training_logs (id, empid, name, channel, topic_name, access_time, status, quiz_score, delay_reason)
        VALUES (?, ?, ?, ?, ?, ?, 'In Progress', 0.0, '')
    ''', (log_id, empid, name, channel, topic_name, now_str))
    conn.commit()
    conn.close()

def get_active_agent_training(empid):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, empid, name, channel, topic_name, access_time, status, quiz_score, delay_reason 
        FROM self_training_logs 
        WHERE empid = ? AND status IN ('In Progress', 'Delayed')
        ORDER BY access_time DESC LIMIT 1
    ''', (empid,))
    row = cursor.fetchone()
    conn.close()

    if row:
        log_dict = dict(row)
        access_time_str = log_dict['access_time']
        status = log_dict['status']
        
        try:
            start_dt = datetime.strptime(access_time_str, "%Y-%m-%d %H:%M:%S")
        except Exception:
            start_dt = datetime.now()

        if datetime.now() - start_dt > timedelta(hours=24) and status == 'In Progress':
            status = 'Delayed'
            log_dict['status'] = 'Delayed'
            
            # ১. ডাটাবেসে স্ট্যাটাস আপডেট
            update_training_status_to_delayed(log_dict['id'])
            
            # ২. অটোমেটিক ইমেইল পাঠানো
            send_delay_email(log_dict['empid'], log_dict['name'], log_dict['topic_name'], log_dict['access_time'])

        return log_dict
    return None

def update_training_status_to_delayed(log_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE self_training_logs SET status = 'Delayed' WHERE id = ?", (log_id,))
    conn.commit()
    conn.close()

def mark_self_training_complete(log_id, score, delay_reason=None):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE self_training_logs 
        SET status = 'Completed', quiz_score = ?, delay_reason = ? 
        WHERE id = ?
    ''', (score, delay_reason if delay_reason else "On Time", log_id))
    conn.commit()
    conn.close()

def get_self_training_logs():
    conn = get_connection()
    logs = conn.execute("SELECT * FROM self_training_logs ORDER BY access_time DESC").fetchall()
    conn.close()
    return [dict(l) for l in logs]

# ----------------- REFRESHER REQUESTS -----------------

def insert_refresher_request(req_dict):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO refresher_requests (id, empid, name, channel, topic_name, preferred_slot, status)
        VALUES (?, ?, ?, ?, ?, ?, 'Pending')
    ''', (req_dict['id'], req_dict['empid'], req_dict['name'], req_dict['channel'], req_dict['topic_name'], req_dict['preferred_slot']))
    conn.commit()
    conn.close()

def assign_refresher_by_admin(empid, name, channel, topic_name, slot_info):
    req_id = f"ADM-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO refresher_requests (id, empid, name, channel, topic_name, preferred_slot, status)
        VALUES (?, ?, ?, ?, ?, ?, 'Assigned by Admin')
    ''', (req_id, empid, name, channel, topic_name, slot_info))
    conn.commit()
    conn.close()

def get_refresher_requests():
    conn = get_connection()
    reqs = conn.execute("SELECT * FROM refresher_requests ORDER BY id DESC").fetchall()
    conn.close()
    return [dict(r) for r in reqs]

# ----------------- GOOGLE SHEET SYNC -----------------

def sync_to_gsheet(sheet_name, row_data):
    pass

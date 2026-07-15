# db.py — Extended SQLite persistence layer for Pathao CX Training Portal
import sqlite3
import os
import json

DB_PATH = os.path.join(os.path.dirname(__file__), "training_portal.db")

def get_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_conn()
    c = conn.cursor()
    
    # 1. Core Central Database: Topics
    c.execute("""
        CREATE TABLE IF NOT EXISTS topics (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            duration TEXT,
            trainer_name TEXT,
            service_knowledge TEXT,
            tools_introduction TEXT,
            tools_checkpoint TEXT,
            process_flow TEXT,
            communication_scripts TEXT,
            quiz_passing_mark INTEGER DEFAULT 0,
            quiz_questions TEXT -- JSON string storing array of MCQs
        )
    """)
    
    # 2. Induction Training: Trainee Onboarding (Layer 1 & L4)
    c.execute("""
        CREATE TABLE IF NOT EXISTS trainees (
            empid TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            email TEXT,
            phone TEXT,
            joining_date TEXT,
            channel TEXT -- Voice, Chat, Email
        )
    """)
    
    # 3. Induction Training: Daily Roster Grid & Schedule (Layer 2 & L3)
    c.execute("""
        CREATE TABLE IF NOT EXISTS induction_schedule (
            id TEXT PRIMARY KEY,
            date TEXT NOT NULL,
            time_slot TEXT, -- e.g., "11:00 AM - 01:00 PM"
            activity_type TEXT, -- Topic, Break, QA/KPI Parameter
            topic_id TEXT,
            manual_activity TEXT,
            FOREIGN KEY(topic_id) REFERENCES topics(id)
        )
    """)
    
    # 4. Evaluation Engine: Trainee Grades (Layer 3)
    c.execute("""
        CREATE TABLE IF NOT EXISTS trainee_evaluations (
            id TEXT PRIMARY KEY,
            empid TEXT NOT NULL,
            date TEXT NOT NULL,
            quiz_score INTEGER,
            assignment_score INTEGER,
            notes TEXT,
            FOREIGN KEY(empid) REFERENCES trainees(empid)
        )
    """)

    # 5. Refresher Training: Incoming Requests Board
    c.execute("""
        CREATE TABLE IF NOT EXISTS refresher_requests (
            id TEXT PRIMARY KEY,
            empid TEXT NOT NULL,
            name TEXT NOT NULL,
            channel TEXT,
            topic_id TEXT,
            preferred_slot TEXT, -- Date & Time string
            status TEXT DEFAULT 'Pending', -- Pending, Scheduled, Completed
            FOREIGN KEY(topic_id) REFERENCES topics(id)
        )
    """)
    
    # 6. Refresher Training: Scheduled Wizard Sessions
    c.execute("""
        CREATE TABLE IF NOT EXISTS refresher_schedules (
            id TEXT PRIMARY KEY,
            topic_id TEXT,
            scheduled_time TEXT,
            agent_ids TEXT, -- JSON array of empids
            status TEXT DEFAULT 'Active',
            FOREIGN KEY(topic_id) REFERENCES topics(id)
        )
    """)

    conn.commit()
    conn.close()

# --- HELPER FUNCTIONS FOR TOPICS ---
def upsert_topic(topic: dict):
    conn = get_conn()
    conn.execute("""
        INSERT INTO topics (id, name, duration, trainer_name, service_knowledge, tools_introduction, 
                            tools_checkpoint, process_flow, communication_scripts, quiz_passing_mark, quiz_questions)
        VALUES (:id, :name, :duration, :trainer_name, :service_knowledge, :tools_introduction, 
                :tools_checkpoint, :process_flow, :communication_scripts, :quiz_passing_mark, :quiz_questions)
        ON CONFLICT(id) DO UPDATE SET
            name=excluded.name, duration=excluded.duration, trainer_name=excluded.trainer_name,
            service_knowledge=excluded.service_knowledge, tools_introduction=excluded.tools_introduction,
            tools_checkpoint=excluded.tools_checkpoint, process_flow=excluded.process_flow,
            communication_scripts=excluded.communication_scripts, quiz_passing_mark=excluded.quiz_passing_mark,
            quiz_questions=excluded.quiz_questions
    """, topic)
    conn.commit()
    conn.close()

def get_topics():
    conn = get_conn()
    rows = conn.execute("SELECT * FROM topics ORDER BY name").fetchall()
    conn.close()
    return [dict(r) for r in rows]

def delete_topic(topic_id: str):
    conn = get_conn()
    conn.execute("DELETE FROM topics WHERE id=?", (topic_id,))
    conn.commit()
    conn.close()

# --- HELPER FUNCTIONS FOR TRAINEES ---
def insert_trainees(trainee_list: list):
    conn = get_conn()
    for t in trainee_list:
        conn.execute("""
            INSERT INTO trainees (empid, name, email, phone, joining_date, channel)
            VALUES (:empid, :name, :email, :phone, :joining_date, :channel)
            ON CONFLICT(empid) DO UPDATE SET
                name=excluded.name, email=excluded.email, phone=excluded.phone, 
                joining_date=excluded.joining_date, channel=excluded.channel
        """, t)
    conn.commit()
    conn.close()

def get_trainees():
    conn = get_conn()
    rows = conn.execute("SELECT * FROM trainees").fetchall()
    conn.close()
    return [dict(r) for r in rows]
    # --- INDUCTION SCHEDULE & ROSTER HELPER ---
def upsert_induction_schedule(sched: dict):
    conn = get_conn()
    conn.execute("""
        INSERT INTO induction_schedule (id, date, time_slot, activity_type, topic_id, manual_activity)
        VALUES (:id, :date, :time_slot, :activity_type, :topic_id, :manual_activity)
        ON CONFLICT(id) DO UPDATE SET
            time_slot=excluded.time_slot, activity_type=excluded.activity_type,
            topic_id=excluded.topic_id, manual_activity=excluded.manual_activity
    """, sched)
    conn.commit()
    conn.close()

def get_induction_schedule_by_date(target_date: str):
    conn = get_conn()
    rows = conn.execute("""
        SELECT s.*, t.name as topic_name, t.duration 
        FROM induction_schedule s
        LEFT JOIN topics t ON s.topic_id = t.id
        WHERE s.date = ?
    """, (target_date,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]

# --- EVALUATION ENGINE FUNCTIONS ---
def upsert_trainee_evaluation(eval_data: dict):
    conn = get_conn()
    conn.execute("""
        INSERT INTO trainee_evaluations (id, empid, date, quiz_score, assignment_score, notes)
        VALUES (:id, :empid, :date, :quiz_score, :assignment_score, :notes)
        ON CONFLICT(id) DO UPDATE SET
            quiz_score=excluded.quiz_score, assignment_score=excluded.assignment_score, notes=excluded.notes
    """, eval_data)
    conn.commit()
    conn.close()

def get_all_evaluations():
    conn = get_conn()
    rows = conn.execute("""
        SELECT e.*, t.name as trainee_name, t.channel
        FROM trainee_evaluations e
        JOIN trainees t ON e.empid = t.empid
    """).fetchall()
    conn.close()
    return [dict(r) for r in rows]
    # --- REFRESHER REQUESTS HELPER ---
def insert_refresher_request(req: dict):
    conn = get_conn()
    conn.execute("""
        INSERT INTO refresher_requests (id, empid, name, channel, topic_id, preferred_slot, status)
        VALUES (:id, :empid, :name, :channel, :topic_id, :preferred_slot, :status)
    """, req)
    conn.commit()
    conn.close()

def get_refresher_requests():
    conn = get_conn()
    rows = conn.execute("""
        SELECT r.*, t.name as topic_name 
        FROM refresher_requests r
        LEFT JOIN topics t ON r.topic_id = t.id
        ORDER BY r.preferred_slot ASC
    """).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def update_refresher_request_status(req_id: str, status: str):
    conn = get_conn()
    conn.execute("UPDATE refresher_requests SET status=? WHERE id=?", (status, req_id))
    conn.commit()
    conn.close()

# --- REFRESHER SCHEDULING HELPER ---
def insert_refresher_schedule(sched: dict):
    conn = get_conn()
    conn.execute("""
        INSERT INTO refresher_schedules (id, topic_id, scheduled_time, agent_ids, status)
        VALUES (:id, :topic_id, :scheduled_time, :agent_ids, :status)
    """, sched)
    conn.commit()
    conn.close()

def get_active_refresher_schedules():
    conn = get_conn()
    rows = conn.execute("""
        SELECT s.*, t.name as topic_name 
        FROM refresher_schedules s
        LEFT JOIN topics t ON s.topic_id = t.id
        WHERE s.status = 'Active'
    """).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def update_refresher_schedule_status(sched_id: str, status: str):
    conn = get_conn()
    conn.execute("UPDATE refresher_schedules SET status=? WHERE id=?", (status, sched_id))
    conn.commit()
    conn.close()
# --- AGENT SELF-TRAINING SCOREBOARD ---
def insert_self_training_score(empid: str, name: str, topic_id: str, topic_name: str, score: int, status: str):
    conn = get_conn()
    conn.execute("""
        INSERT INTO trainee_evaluations (id, empid, date, quiz_score, assignment_score, notes)
        VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET
            quiz_score=excluded.quiz_score,
            notes=excluded.notes
    """, (f"{empid}_{topic_id}", empid, datetime.now().strftime("%Y-%m-%d"), score, 100, f"Self-Training: {status}"))
    conn.commit()
    conn.close()

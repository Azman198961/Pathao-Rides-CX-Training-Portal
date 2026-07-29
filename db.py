import sqlite3

def get_connection():
    conn = sqlite3.connect("portal.db", check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    
    # Refresher table update
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS refresher_requests (
        id TEXT PRIMARY KEY,
        empid TEXT,
        name TEXT,
        channel TEXT,
        topic_name TEXT,
        time_frame TEXT,
        status TEXT DEFAULT 'Pending',
        rejection_reason TEXT DEFAULT '',
        training_status TEXT DEFAULT 'Pending'
    )
    """)
    conn.commit()
    conn.close()

def insert_refresher_request(data):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO refresher_requests (id, empid, name, channel, topic_name, time_frame, status, training_status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (data['id'], data['empid'], data['name'], data['channel'], data['topic_name'], data['time_frame'], 'Pending', 'Pending'))
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

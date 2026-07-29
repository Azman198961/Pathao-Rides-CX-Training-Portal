import streamlit as st
import pandas as pd
import json
import uuid
from datetime import datetime, date

import db

st.set_page_config(page_title="Pathao CX Training Portal", page_icon="🎓", layout="wide")
db.init_db()

# Custom Styling
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;600;700&family=IBM+Plex+Mono:wght@400;500;600&display=swap');

h1, h2, h3, .stTabs [data-baseweb="tab"] p {
    font-family: 'Space Grotesk', sans-serif !important;
}
.stButton>button {
    background-color:#1F2E28;
    border:1px solid #2A3A34;
    color:#EAF2EE;
    border-radius:8px;
    font-family:'IBM Plex Mono', monospace;
    width: 100%;
}
.stButton>button:hover {
    border-color:#FF7A45;
    color:#FF7A45;
}
.stTabs [data-baseweb="tab-list"]{ gap:8px; }
.stTabs [data-baseweb="tab"]{
    background-color:#182420;
    border:1px solid #2A3A34;
    border-radius:10px;
    padding:10px 20px;
}
.stTabs [aria-selected="true"]{
    border-color:#FF7A45 !important;
    background-color:#1F2E28 !important;
}
[data-testid="stForm"], div[data-testid="stExpander"]{
    background-color:#182420;
    border:1px solid #2A3A34;
    border-radius:14px;
}
.topic-card-box {
    background-color: #182420;
    border: 1px solid #2A3A34;
    border-radius: 12px;
    padding: 20px;
    transition: all 0.3s ease;
    height: 100%;
}
.topic-card-box:hover {
    border-color: #FF7A45;
    box-shadow: 0 4px 15px rgba(255, 122, 69, 0.15);
}
.metric-card {
    background-color: #182420;
    border: 1px solid #2A3A34;
    padding: 15px;
    border-radius: 10px;
    text-align: center;
}
</style>
""", unsafe_allow_html=True)

# Authentication State
if "is_admin" not in st.session_state:
    st.session_state.is_admin = False

with st.sidebar:
    st.markdown("### 🎓 Pathao CX Portal")
    st.caption("Rides Department CMT")
    st.divider()
    role = st.radio("Access Level:", ["Agent View", "Admin View"])
    
    if role == "Admin View" and not st.session_state.is_admin:
        pw = st.text_input("Enter Admin Password", type="password")
        if st.button("Authorize"):
            if pw == st.secrets.get("admin_password", "changeme123"):
                st.session_state.is_admin = True
                st.rerun()
            else:
                st.error("Invalid Credentials")
    elif role == "Admin View" and st.session_state.is_admin:
        st.success("Authorized Session")
        if st.button("Revoke Access"):
            st.session_state.is_admin = False
            st.rerun()

is_admin_view = (role == "Admin View" and st.session_state.is_admin)

st.title("Pathao Rides — CX Training Portal")

if is_admin_view:
    admin_tab1, admin_tab2, admin_tab3 = st.tabs([
        "🗃️ Topic & Web Link Manager", 
        "📅 Induction Performance Dashboard", 
        "🔁 Refresher Training"
    ])
    
    # 1. TOPIC MANAGER
    with admin_tab1:
        st.header("Topic & Web Content Management System")
        st.caption("Add Netlify Website Links for training topics and setup 5-question Quiz for agents.")
        
        with st.expander("➕ Add New Training Topic & Netlify Link", expanded=False):
            with st.form("new_topic_form"):
                c1, c2, c3 = st.columns([2, 1, 1])
                t_name = c1.text_input("Topic Name *")
                t_duration = c2.text_input("Duration *")
                t_trainer = c3.text_input("Assigned Trainer Name")
                site_url = st.text_input("Netlify Site URL *")
                
                st.divider()
                st.markdown("#### 📝 Topic Quiz Setup")
                passing_mark = st.number_input("Passing Score (%)", min_value=0, max_value=100, value=80)
                
                quiz_inputs = []
                for q_num in range(1, 6):
                    st.markdown(f"**Question {q_num}:**")
                    q_text = st.text_input(f"Question {q_num} Text", key=f"q_text_{q_num}")
                    col_opt1, col_opt2 = st.columns(2)
                    opt_a = col_opt1.text_input(f"Option A (Q{q_num})", key=f"q_{q_num}_a")
                    opt_b = col_opt2.text_input(f"Option B (Q{q_num})", key=f"q_{q_num}_b")
                    opt_c = col_opt1.text_input(f"Option C (Q{q_num})", key=f"q_{q_num}_c")
                    opt_d = col_opt2.text_input(f"Option D (Q{q_num})", key=f"q_{q_num}_d")
                    correct_opt = st.selectbox(f"Correct Answer Q{q_num}", ["Option A", "Option B", "Option C", "Option D"], key=f"q_{q_num}_ans")
                    
                    options_dict = {"Option A": opt_a, "Option B": opt_b, "Option C": opt_c, "Option D": opt_d}
                    quiz_inputs.append({"question": q_text, "options": [opt_a, opt_b, opt_c, opt_d], "answer": options_dict[correct_opt]})
                
                if st.form_submit_button("💾 Save Topic"):
                    if not t_name or not site_url:
                        st.error("Topic Name and URL required!")
                    else:
                        db.upsert_topic({
                            "id": str(uuid.uuid4()), "name": t_name.strip(), "duration": t_duration.strip(),
                            "trainer_name": t_trainer.strip(), "quiz_passing_mark": int(passing_mark),
                            "quiz_questions": json.dumps(quiz_inputs), "site_url": site_url.strip()
                        })
                        st.success("Topic Saved!")
                        st.rerun()

        st.subheader("Current Topics")
        for top in db.get_topics():
            with st.container(border=True):
                col_t1, col_t2 = st.columns([4, 1])
                col_t1.markdown(f"### 🌐 {top.get('name')}")
                col_t1.caption(f"Duration: {top.get('duration')} | Trainer: {top.get('trainer_name')} | URL: {top.get('site_url')}")
                if col_t2.button("🗑️ Delete", key=f"del_{top['id']}"):
                    db.delete_topic(top['id'])
                    st.rerun()

    # ==========================================
    # 2. INDUCTION PERFORMANCE DASHBOARD (NEW)
    # ==========================================
    with admin_tab2:
        st.header("📊 Induction Training Performance & Health Check")
        st.caption("Track training progress, hours invested, and agent health status.")
        
        raw_data = db.get_induction_activities()
        if not raw_data:
            st.info("No Induction Activity Records Found.")
        else:
            df = pd.DataFrame(raw_data)
            
            # --- High Level Metrics Summary ---
            m1, m2, m3, m4 = st.columns(4)
            total_hours = df['hours_spent'].sum()
            avg_score = df['quiz_score'].mean()
            passed_agents = len(df[df['status'] == 'Passed']['agent_id'].unique())
            total_agents = len(df['agent_id'].unique())
            
            m1.metric("⏱️ Total Training Hours", f"{total_hours:.1f} hrs")
            m2.metric("🎯 Avg Quiz Score", f"{avg_score:.1f}%")
            m3.metric("✅ Passed Agents", f"{passed_agents} / {total_agents}")
            m4.metric("📈 Pass Rate", f"{(passed_agents/total_agents)*100:.1f}%" if total_agents else "0%")
            
            st.divider()
            
            col_left, col_right = st.columns([1, 1])
            
            # 1. Topic-wise Hours Calculation
            with col_left:
                st.subheader("⏱️ Topic-wise Training Hours")
                topic_hours = df.groupby('topic_name')['hours_spent'].sum().reset_index()
                topic_hours.columns = ['Topic Name', 'Total Hours']
                st.dataframe(topic_hours, use_container_width=True, hide_index=True)
                st.bar_chart(topic_hours.set_index('Topic Name'))
                
            # 2. Agent Health Check Dashboard
            with col_right:
                st.subheader("🩺 Agent Activity & Health Status")
                
                # Health Logic: Avg Score > 75 = Healthy🟢, 50-75 = Needs Attention🟡, < 50 = At Risk🔴
                agent_health = df.groupby(['agent_id', 'agent_name']).agg(
                    Avg_Score=('quiz_score', 'mean'),
                    Total_Hours=('hours_spent', 'sum'),
                    Attempts=('id', 'count')
                ).reset_index()
                
                def get_health_status(score):
                    if score >= 75:
                        return "🟢 Healthy"
                    elif score >= 50:
                        return "🟡 Needs Improvement"
                    else:
                        return "🔴 At Risk"
                
                agent_health['Health Status'] = agent_health['Avg_Score'].apply(get_health_status)
                
                st.dataframe(
                    agent_health[['agent_name', 'Total_Hours', 'Avg_Score', 'Health Status']],
                    use_container_width=True,
                    hide_index=True
                )
                
            st.divider()
            st.subheader("📋 Detailed Activity Logs")
            st.dataframe(df[['activity_date', 'agent_name', 'channel', 'topic_name', 'hours_spent', 'quiz_score', 'status']], use_container_width=True)

    # 3. REFRESHER TRAINING MANAGEMENT
    with admin_tab3:
        st.header("🔁 Refresher Training Requests Management")
        all_requests = db.get_refresher_requests()
        if not all_requests:
            st.info("No Refresher Requests found.")
        else:
            for req in all_requests:
                with st.container(border=True):
                    c_info, c_action = st.columns([3, 2])
                    with c_info:
                        st.markdown(f"### 👤 Agent: **{req['name']}** (`{req['empid']}`)")
                        st.markdown(f"**Channel:** {req['channel']} | **Topic:** `{req['topic_name']}`")
                        st.markdown(f"🗓️ Slot: {req['preferred_slot']}")
                        st.write(f"**Status:** `{req['status']}` | **Training:** `{req.get('training_status', 'Pending')}`")
                    
                    with c_action:
                        action = st.selectbox("Action", ["Select Action", "Accept Request", "Reject Request"], key=f"act_{req['id']}")
                        if action == "Accept Request":
                            t_stat = st.selectbox("Training Status", ["Pending", "In Progress", "Completed"], key=f"ts_{req['id']}")
                            if st.button("Confirm Accept", key=f"acc_{req['id']}"):
                                db.update_refresher_status(req['id'], "Accepted", "", t_stat)
                                st.rerun()
                        elif action == "Reject Request":
                            reason = st.text_area("Reason *", key=f"rej_{req['id']}")
                            if st.button("Confirm Reject", key=f"rej_btn_{req['id']}"):
                                if reason.strip():
                                    db.update_refresher_status(req['id'], "Rejected", reason.strip(), "Cancelled")
                                    st.rerun()

else:
    # AGENT VIEW
    st.header("Agent Self-Service Hub")
    agent_tab1, agent_tab2 = st.tabs(["📖 Study Topics & Take Quiz", "🔁 Request Refresher Session"])
    
    with agent_tab1:
        topics = db.get_topics()
        if not topics:
            st.info("No topics available.")
        else:
            for t in topics:
                with st.container(border=True):
                    st.markdown(f"### 📚 {t['name']}")
                    st.caption(f"Duration: {t['duration']} | Trainer: {t.get('trainer_name', 'N/A')}")
                    if t.get('site_url'):
                        st.components.v1.iframe(t['site_url'], height=450, scrolling=True)

    with agent_tab2:
        st.subheader("🔁 Request Refresher Session")
        topics = db.get_topics()
        t_opts = [t["name"] for t in topics] if topics else []
        
        with st.form("agent_ref_form"):
            c1, c2 = st.columns(2)
            a_name = c1.text_input("Agent Name *")
            a_id = c2.text_input("EMP ID *")
            
            c3, c4 = st.columns(2)
            a_chan = c3.selectbox("Channel *", ["", "Inbound Voice", "Live Chat", "Email", "Complaint"])
            a_topic = c4.selectbox("Topic *", [""] + t_opts) if t_opts else c4.text_input("Topic Name *")
            
            col1, col2 = st.columns(2)
            r_date = col1.date_input("Date *", value=date.today())
            r_time = col2.selectbox("Slot *", ["", "10:00 AM - 01:00 PM", "02:00 PM - 05:00 PM"])
            
            if st.form_submit_button("Submit Request"):
                if not a_name or not a_id or not a_chan or not a_topic or not r_time:
                    st.error("All fields mandatory!")
                else:
                    db.insert_refresher_request({
                        "id": str(uuid.uuid4()), "empid": a_id, "name": a_name,
                        "channel": a_chan, "topic_name": a_topic,
                        "preferred_slot": f"{r_date.strftime('%d %b %Y')} ({r_time})"
                    })
                    st.success("Request submitted successfully!")

import streamlit as st
import pandas as pd
import json
import uuid
from datetime import date

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
        "📅 Induction Training", 
        "🔁 Refresher Training Requests"
    ])
    
    # ----------------------------------------------------
    # 1. TOPIC & LINK MANAGER
    # ----------------------------------------------------
    with admin_tab1:
        st.header("Topic & Web Content Management System")
        st.caption("Add Netlify Website Links for training topics and setup 5-question Quiz for agents.")
        
        with st.expander("➕ Add New Training Topic & Netlify Link", expanded=False):
            with st.form("new_topic_form"):
                c1, c2, c3 = st.columns([2, 1, 1])
                t_name = c1.text_input("Topic Name * (e.g., Refund Policy, Fare Anomaly)")
                t_duration = c2.text_input("Duration * (e.g., 30 mins, 1 hour)")
                t_trainer = c3.text_input("Assigned Trainer Name")
                
                st.markdown("#### 🔗 Add Training Material Netlify Link *")
                site_url = st.text_input("Netlify Site URL * (e.g., https://your-site.netlify.app)")
                
                st.divider()
                st.markdown("#### 📝 Topic Quiz Setup (Add 5 Questions)")
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
                    
                    correct_opt = st.selectbox(
                        f"Select Correct Answer for Q{q_num}", 
                        ["Option A", "Option B", "Option C", "Option D"], 
                        key=f"q_{q_num}_ans"
                    )
                    
                    options_dict = {"Option A": opt_a, "Option B": opt_b, "Option C": opt_c, "Option D": opt_d}
                    quiz_inputs.append({
                        "question": q_text,
                        "options": [opt_a, opt_b, opt_c, opt_d],
                        "answer": options_dict[correct_opt]
                    })
                    st.write("---")
                
                submit_topic = st.form_submit_button("💾 Save Topic & Link")
                
                if submit_topic:
                    if not t_name or not t_duration or not site_url:
                        st.error("Topic Name, Duration, and Netlify URL are mandatory!")
                    else:
                        valid_quiz = [q for q in quiz_inputs if q["question"].strip() != ""]
                        topic_payload = {
                            "id": str(uuid.uuid4()),
                            "name": t_name.strip(),
                            "duration": t_duration.strip(),
                            "trainer_name": t_trainer.strip(),
                            "quiz_passing_mark": int(passing_mark),
                            "quiz_questions": json.dumps(valid_quiz),
                            "site_url": site_url.strip()
                        }
                        db.upsert_topic(topic_payload)
                        st.success(f"Topic '{t_name}' saved successfully!")
                        st.rerun()

        st.subheader("Current Topics in Database")
        current_topics = db.get_topics()
        if not current_topics:
            st.info("No records present inside Database yet.")
        else:
            for top in current_topics:
                with st.container(border=True):
                    col_t1, col_t2 = st.columns([4, 1])
                    col_t1.markdown(f"### 🌐 {top.get('name', 'Unnamed Topic')}")
                    col_t1.caption(f"⏱️ Duration: {top.get('duration', '')} | 👤 Trainer: {top.get('trainer_name') or 'Unassigned'} | 🔗 URL: {top.get('site_url', 'N/A')}")
                    
                    with col_t2:
                        if st.button("🗑️ Delete", key=f"del_{top['id']}"):
                            db.delete_topic(top['id'])
                            st.warning("Topic deleted.")
                            st.rerun()

    # ----------------------------------------------------
    # 2. INDUCTION TRAINING
    # ----------------------------------------------------
    with admin_tab2:
        st.header("Induction Training Dashboard")
        st.info("Induction Training Features Active.")

    # ----------------------------------------------------
    # 3. REFRESHER TRAINING MANAGEMENT (ADMIN VIEW)
    # ----------------------------------------------------
    with admin_tab3:
        st.header("🔁 Refresher Training Requests Management")
        st.caption("Review and manage refresher training requests sent by agents.")
        
        all_requests = db.get_refresher_requests()
        
        if not all_requests:
            st.info("No Refresher Training Requests found.")
        else:
            for req in all_requests:
                with st.container(border=True):
                    col_info, col_action = st.columns([3, 2])
                    
                    with col_info:
                        st.markdown(f"### 👤 Agent: **{req['name']}** (ID: `{req['empid']}`)")
                        st.markdown(f"**Channel:** {req['channel']} | **Topic Needed:** `{req['topic_name']}`")
                        st.markdown(f"🗓️ **Requested Time Frame/Date:** {req['time_frame']}")
                        
                        # Status Badges
                        st.write(f"**Approval Status:** `{req['status']}` | **Training Status:** `{req['training_status']}`")
                        if req['status'] == "Rejected" and req.get('rejection_reason'):
                            st.error(f"❌ **Rejection Reason:** {req['rejection_reason']}")
                    
                    with col_action:
                        st.markdown("#### Manage Request")
                        action_choice = st.selectbox(
                            "Select Action",
                            ["Select Status", "Accept Request", "Reject Request"],
                            key=f"act_sel_{req['id']}"
                        )
                        
                        if action_choice == "Accept Request":
                            t_status = st.selectbox(
                                "Set Training Status",
                                ["Pending", "In Progress", "Completed"],
                                index=["Pending", "In Progress", "Completed"].index(req.get('training_status', 'Pending')),
                                key=f"tr_stat_{req['id']}"
                            )
                            if st.button("Update to Accepted", key=f"btn_acc_{req['id']}"):
                                db.update_refresher_status(req['id'], status="Accepted", rejection_reason="", training_status=t_status)
                                st.success("Request Accepted Successfully!")
                                st.rerun()
                                
                        elif action_choice == "Reject Request":
                            rejection_reason = st.text_area("Rejection Reason *", key=f"rej_reason_{req['id']}")
                            if st.button("Confirm Reject", key=f"btn_rej_{req['id']}"):
                                if not rejection_reason.strip():
                                    st.error("Please provide a rejection reason!")
                                else:
                                    db.update_refresher_status(req['id'], status="Rejected", rejection_reason=rejection_reason.strip(), training_status="Cancelled")
                                    st.warning("Request Marked as Rejected.")
                                    st.rerun()

else:
    # ==========================================
    # AGENT WORKSPACE PORTAL
    # ==========================================
    st.header("Agent Self-Service Hub")
    
    agent_tab1, agent_tab2 = st.tabs([
        "📖 Study Topics & Take Quiz", 
        "🔁 Request Refresher Session"
    ])
    
    with agent_tab1:
        st.info("Select topics to study and participate in quizzes.")

    # ----------------------------------------------------
    # REFRESHER SESSION REQUEST FORM (AGENT VIEW)
    # ----------------------------------------------------
    with agent_tab2:
        st.subheader("🔁 Request a Refresher Training Session")
        st.caption("Fill up all required details below to send a request to the Training/Admin Team.")
        
        db_topics = db.get_topics()
        topic_names = [t['name'] for t in db_topics] if db_topics else []
        
        with st.form("agent_refresher_request_form"):
            c1, c2 = st.columns(2)
            ag_name = c1.text_input("Agent Name *", placeholder="Enter your full name")
            ag_id = c2.text_input("EMP ID *", placeholder="e.g. PX-1024")
            
            c3, c4 = st.columns(2)
            ag_channel = c3.selectbox(
                "Channel *", 
                ["", "Inbound Voice", "Live Chat & Social Media", "Report Issue & Email", "Complaint Management", "Campaign Management"]
            )
            
            # Dynamic Topic Selection
            if topic_names:
                ag_topic = c4.selectbox("Topic Name *", [""] + topic_names)
            else:
                ag_topic = c4.text_input("Topic Name *", placeholder="Enter topic name needed")
                
            st.markdown("#### 📅 Desired Timeframe / Date Range *")
            col_d1, col_d2 = st.columns(2)
            start_date = col_d1.date_input("Training Needed From *", value=date.today())
            end_date = col_d2.date_input("Training Needed Until *", value=date.today())
            
            preferred_slot = st.selectbox("Preferred Time Slot *", ["", "Morning (10:00 AM - 01:00 PM)", "Afternoon (02:00 PM - 05:00 PM)", "Evening (05:00 PM - 08:00 PM)"])
            
            submit_btn = st.form_submit_button("Request Refresher Training Session")
            
            if submit_btn:
                # Validation for required fields
                if not ag_name.strip() or not ag_id.strip() or not ag_channel or not ag_topic or not preferred_slot:
                    st.error("⚠️ All fields marked with (*) are required!")
                elif start_date > end_date:
                    st.error("⚠️ Start Date cannot be after End Date!")
                else:
                    time_frame_str = f"{start_date.strftime('%d %b %Y')} to {end_date.strftime('%d %b %Y')} ({preferred_slot})"
                    
                    req_payload = {
                        "id": str(uuid.uuid4()),
                        "name": ag_name.strip(),
                        "empid": ag_id.strip(),
                        "channel": ag_channel,
                        "topic_name": ag_topic,
                        "time_frame": time_frame_str
                    }
                    db.insert_refresher_request(req_payload)
                    st.success("✅ Refresher Training Session requested successfully! Admin will review your request.")

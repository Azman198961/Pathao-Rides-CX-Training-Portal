import streamlit as st
import pandas as pd
import json
import uuid
from datetime import datetime, date

import db

st.set_page_config(page_title="Pathao CX Training Portal", page_icon="🎓", layout="wide")
db.init_db()

# Custom styles keeping Pathao colors & fonts crisp
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
    # Admin Interface Breakdown
    admin_tab1, admin_tab2, admin_tab3 = st.tabs([
        "🗃️ Central Topic Manager", 
        "📅 Induction Training", 
        "🔁 Refresher Training"
    ])
    
    # ==========================================
    # 1. CENTRAL TOPIC MANAGER
    # ==========================================
    with admin_tab1:
        st.header("Core Database: Topic Management System")
        st.caption("Every topic managed here instantly populates both Induction schedules and Refresher self-paced menus.")
        
        # Topic Creation Form
        with st.expander("➕ Create New Training Topic", expanded=False):
            with st.form("new_topic_form"):
                c1, c2, c3 = st.columns([2, 1, 1])
                t_name = c1.text_input("Topic Name * (e.g., Refund Policy, Fare Anomaly)")
                t_duration = c2.text_input("Duration * (e.g., 45 mins, 1.5 hours)")
                t_trainer = c3.text_input("Assigned Trainer Name")
                
                st.markdown("#### Category Details & Content Tabs")
                det_tabs = st.tabs([
                    "📖 Service Knowledge", "🛠️ Tools Intro", 
                    "✅ Tools Checkpoint", "🔀 Process Flow", 
                    "💬 Communication/Scripts", "📝 Quiz Creator"
                ])
                
                with det_tabs[0]:
                    sk_content = st.text_area("Core Service Policies & Guidelines", height=150)
                with det_tabs[1]:
                    ti_content = st.text_area("Required Tools Breakdown (e.g., Zendesk, Admin Panel)", height=150)
                with det_tabs[2]:
                    tc_content = st.text_area("Checklist to verify agent technical execution (One per line)", height=150)
                with det_tabs[3]:
                    pf_content = st.text_area("Step-by-step resolution paths and systemic workflows", height=150)
                with det_tabs[4]:
                    cs_content = st.text_area("Response templates and Tone of Voice parameters", height=150)
                    
                with det_tabs[5]:
                    c_q1, c_q2 = st.columns([1, 3])
                    passing_mark = c_q1.number_input("Passing Score (%)", min_value=0, max_value=100, value=80)
                    st.caption("Define basic multiple-choice questions structural JSON format below:")
                    # Default template structure for MCQs
                    quiz_json_str = st.text_area(
                        "MCQ Setup Array (JSON Format)", 
                        value=json.dumps([
                            {
                                "question": "Sample Question Text?",
                                "options": ["Option A", "Option B", "Option C"],
                                "answer": "Option A"
                            }
                        ], indent=4), 
                        height=150
                    )
                
                submit_topic = st.form_submit_button("💾 Save Topic to Database")
                
                if submit_topic:
                    if not t_name or not t_duration:
                        st.error("Topic Name and Duration are required fields.")
                    else:
                        try:
                            # Verify valid JSON syntax
                            json.loads(quiz_json_str)
                            
                            topic_payload = {
                                "id": str(uuid.uuid4()),
                                "name": t_name.strip(),
                                "duration": t_duration.strip(),
                                "trainer_name": t_trainer.strip(),
                                "service_knowledge": sk_content.strip(),
                                "tools_introduction": ti_content.strip(),
                                "tools_checkpoint": tc_content.strip(),
                                "process_flow": pf_content.strip(),
                                "communication_scripts": cs_content.strip(),
                                "quiz_passing_mark": int(passing_mark),
                                "quiz_questions": quiz_json_str.strip()
                            }
                            db.upsert_topic(topic_payload)
                            st.success(f"Topic '{t_name}' securely committed to the Core Database.")
                            st.rerun()
                        except json.JSONDecodeError:
                            st.error("Invalid Quiz Setup Array format. Ensure it strictly matches JSON arrays.")

        # Display Available Core Topics
        st.subheader("Current Database Records")
        current_topics = db.get_topics()
        if not current_topics:
            st.info("No records present inside the Database yet.")
        else:
            for top in current_topics:
                with st.container(border=True):
                    col_t1, col_t2, col_t3 = st.columns([3, 1, 1])
                    col_t1.markdown(f"### {top['name']}")
                    col_t1.caption(f"⏱️ Duration: {top['duration']} | 👤 Trainer: {top['trainer_name'] or 'Unassigned'}")
                    
                    with col_t2:
                        if st.button("🗑️ Delete Topic", key=f"del_{top['id']}"):
                            db.delete_topic(top['id'])
                            st.warning("Topic removed.")
                            st.rerun()
                            
                    with st.expander("📄 View Linked Modules & Materials"):
                        st.markdown(f"**Service Knowledge:** {top['service_knowledge']}")
                        st.markdown(f"**Process Flows:** {top['process_flow']}")
                        st.markdown(f"**Passing Requirement:** {top['quiz_passing_mark']}%")

    # ==========================================
    # 2. INDUCTION TRAINING (PLACEHOLDER)
    # ==========================================
    with admin_tab2:
        st.info("Step 2 Layer Integration: Roster grids, daily planners, and dynamic onboarding matrix will load here.")

    # ==========================================
    # 3. REFRESHER TRAINING (PLACEHOLDER)
    # ==========================================
    with admin_tab3:
        st.info("Step 3 Layer Integration: Incoming Request Board and Scheduling Wizard will load here.")

else:
    # ==========================================
    # AGENT VIEW (PLACEHOLDER)
    # ==========================================
    st.markdown("### Agent Workspace Portal")
    st.info("Step 4 Layer Integration: Self-paced training viewers, interactive dynamic quiz completion, and refresher request portals will load here.")

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
   # ==========================================
    # 2. INDUCTION TRAINING (LAYERS 1 - 4)
    # ==========================================
    with admin_tab2:
        st.header("Induction Training Dashboard (New Joiners)")
        
        ind_l1, ind_l2, ind_l3, ind_l4 = st.tabs([
            "👥 L1: Trainee Onboarding", 
            "📅 L2: Training Timeline", 
            "⚡ L3: Daily Schedule & Grading", 
            "📊 L4: Performance Report"
        ])
        
        # ---------------------------------------------------------
        # LAYER 1: Trainee Information Onboarding
        # ---------------------------------------------------------
        with ind_l1:
            st.subheader("Layer 1: Onboard New Joiners")
            col_b1, col_b2 = st.columns([1, 1])
            
            with col_b1:
                st.markdown("#### Individual Trainee Entry")
                with st.form("single_trainee_form", clear_on_submit=True):
                    t_id = st.text_input("Employee ID *")
                    t_name = st.text_input("Full Name *")
                    t_email = st.text_input("Email Address")
                    t_phone = st.text_input("Phone Number")
                    t_date = st.date_input("Joining Date", value=date.today())
                    t_chan = st.selectbox("Assigned Channel *", ["Voice", "Chat", "Email"])
                    
                    if st.form_submit_button("Add Trainee"):
                        if not t_id or not t_name:
                            st.error("Employee ID and Name are mandatory.")
                        else:
                            db.insert_trainees([{
                                "empid": t_id.strip(), "name": t_name.strip(),
                                "email": t_email.strip(), "phone": t_phone.strip(),
                                "joining_date": t_date.isoformat(), "channel": t_chan
                            }])
                            st.success(f"Trainee {t_name} securely onboarded.")
                            st.rerun()
            
            with col_b2:
                st.markdown("#### Bulk Import via CSV")
                st.caption("CSV format requirements: empid, name, email, phone, joining_date, channel")
                uploaded_csv = st.file_uploader("Upload Onboarding Document", type=["csv"])
                if uploaded_csv:
                    try:
                        csv_df = pd.read_csv(uploaded_csv)
                        required_cols = ["empid", "name", "email", "phone", "joining_date", "channel"]
                        if all(col in csv_df.columns for col in required_cols):
                            trainee_list = csv_df[required_cols].to_dict(orient="records")
                            db.insert_trainees(trainee_list)
                            st.success(f"Successfully processed and updated {len(trainee_list)} trainees.")
                            st.rerun()
                        else:
                            st.error(f"Missing headers. CSV requires exactly: {required_cols}")
                    except Exception as e:
                        st.error(f"Error parse execution: {str(e)}")
            
            st.divider()
            st.markdown("#### Currently Active Class Roster")
            current_trainees = db.get_trainees()
            if current_trainees:
                st.dataframe(pd.DataFrame(current_trainees), use_container_width=True, hide_index=True)
            else:
                st.caption("No trainees currently exist in the database roster.")

        # ---------------------------------------------------------
        # LAYER 2: Training Duration (Timeline Grid)
        # ---------------------------------------------------------
        with ind_l2:
            st.subheader("Layer 2: Timeline Setup")
            col_time1, col_time2 = st.columns([1, 2])
            
            with col_time1:
                start_range = st.date_input("Training Batch Start Date", key="ind_start")
                end_range = st.date_input("Training Batch End Date", key="ind_end")
                
            with col_time2:
                if start_range <= end_range:
                    delta_days = (end_range - start_range).days + 1
                    st.info(f"Interactive timeline generated dynamically: **{delta_days} Training Days** configured.")
                    
                    # Interactive Calendar Grid Generator
                    st.markdown("#### Batch Timeline Grid Selector")
                    grid_cols = st.columns(min(7, delta_days))
                    for day_idx in range(delta_days):
                        current_day = start_range + pd.Timedelta(days=day_idx)
                        day_str = current_day.isoformat()
                        col_pos = day_idx % 7
                        
                        with grid_cols[col_pos]:
                            if st.button(f"📅 Day {day_idx+1}\n{current_day.strftime('%b %d')}", key=f"timeline_{day_str}", use_container_width=True):
                                st.session_state.active_induction_date = day_str
                                st.success(f"Selected target day: {day_str}")
                else:
                    st.error("Error: End date must fall ahead or equal to start date timeline parameters.")

        # ---------------------------------------------------------
        # LAYER 3: Daily Calendar Schedule & Evaluation Engine
        # ---------------------------------------------------------
        with ind_l3:
            target_date = st.session_state.get("active_induction_date", None)
            if not target_date:
                st.warning("⚠️ Please pick an active target day from the Timeline Grid under 'L2: Training Timeline' first.")
            else:
                st.subheader(f"Layer 3: Target Operations for Roster Day [{target_date}]")
                
                c_sched1, c_sched2 = st.columns([2, 3])
                
                with c_sched1:
                    st.markdown("#### Hourly Activity Planner (11:00 AM - 08:00 PM)")
                    hours_slots = [
                        "11:00 AM - 12:00 PM", "12:00 PM - 01:00 PM", "01:00 PM - 02:00 PM",
                        "02:00 PM - 03:00 PM", "03:00 PM - 04:00 PM", "04:00 PM - 05:00 PM",
                        "05:00 PM - 06:00 PM", "06:00 PM - 07:00 PM", "07:00 PM - 08:00 PM"
                    ]
                    
                    with st.form("hourly_planner_form"):
                        slot_selection = st.selectbox("Select Time Slot Block", hours_slots)
                        act_type = st.radio("Activity Designation", ["Core Database Topic", "Break / Custom Task", "QA & KPI Parameters Training"])
                        
                        db_topics = db.get_topics()
                        topic_options = {top['name']: top['id'] for top in db_topics}
                        selected_topic_name = st.selectbox("Linked Core Database Topic (If applicable)", list(topic_options.keys()) if db_topics else ["No Topics Found"])
                        
                        custom_text = st.text_input("Custom Activity / Break Details Description")
                        
                        if st.form_submit_button("Commit Activity to Roster Grid"):
                            sched_id = f"{target_date}_{slot_selection.replace(' ', '')}"
                            payload = {
                                "id": sched_id,
                                "date": target_date,
                                "time_slot": slot_selection,
                                "activity_type": act_type,
                                "topic_id": topic_options[selected_topic_name] if (act_type == "Core Database Topic" and db_topics) else None,
                                "manual_activity": custom_text if act_type != "Core Database Topic" else selected_topic_name
                            }
                            db.upsert_induction_schedule(payload)
                            st.success("Hourly slot mapped.")
                            st.rerun()
                
                with c_sched2:
                    st.markdown("#### Active Daily Schedule Grid Overview")
                    day_schedule = db.get_induction_schedule_by_date(target_date)
                    if day_schedule:
                        sched_df = pd.DataFrame(day_schedule)[["time_slot", "activity_type", "manual_activity"]]
                        st.table(sched_df.sort_values(by="time_slot"))
                    else:
                        st.caption("No hourly timelines assigned yet for this active target calendar block.")
                
                st.divider()
                st.markdown("#### Dynamic Evaluation Engine & Manual Grading Portal")
                all_trainees = db.get_trainees()
                
                if not all_trainees:
                    st.info("Onboard trainees in L1 to authorize functional scoring profiles.")
                else:
                    with st.form("grading_engine_form"):
                        g_trainee = st.selectbox("Select Trainee Evaluation Target Profile", [f"{t['name']} ({t['empid']})" for t in all_trainees])
                        target_empid = g_trainee.split("(")[-1].replace(")", "").strip()
                        
                        col_scr1, col_scr2 = st.columns(2)
                        quiz_score = col_scr1.number_input("Automated Daily Quiz Performance Metric Score", min_value=0, max_value=100, value=0)
                        assignment_score = col_scr2.number_input("Manual Evaluation Assignment Grading Matrix Score", min_value=0, max_value=100, value=0)
                        eval_notes = st.text_area("Trainer Observation Assessment Remarks & Notes Log")
                        
                        if st.form_submit_button("Securely Record Grade Matrices"):
                            eval_id = f"{target_empid}_{target_date}"
                            db.upsert_trainee_evaluation({
                                "id": eval_id, "empid": target_empid, "date": target_date,
                                "quiz_score": int(quiz_score), "assignment_score": int(assignment_score),
                                "notes": eval_notes.strip()
                            })
                            st.success(f"Grades successfully calculated and securely logged down for {g_trainee}.")
                            st.rerun()

        # ---------------------------------------------------------
        # LAYER 4: Training Outcome (Detailed Report Breakdown)
        # ---------------------------------------------------------
        with ind_l4:
            st.subheader("Layer 4: Final Training Performance Report Dashboard Summary")
            
            raw_evals = db.get_all_evaluations()
            if not raw_evals:
                st.info("Insufficient system evaluation scoring records found to build final analysis modules yet.")
            else:
                eval_df = pd.DataFrame(raw_evals)
                
                # Dynamic calculations metrics mapping out scorecard profiles
                eval_df['Total Score'] = (eval_df['quiz_score'] + eval_df['assignment_score']) / 2
                summary_agg = eval_df.groupby(['empid', 'trainee_name', 'channel'])['Total Score'].mean().reset_index()
                
                col_c1, col_c2 = st.columns(2)
                top_scorer = summary_agg.loc[summary_agg['Total Score'].idxmax()]
                low_scorer = summary_agg.loc[summary_agg['Total Score'].idxmin()]
                
                col_c1.metric("🥇 Batch Top Performer Scorecard Profile", f"{top_scorer['trainee_name']}", f"{top_scorer['Total Score']:.1f}% Avg")
                col_c2.metric("⚠️ Focus Required Profile Assistance Target", f"{low_scorer['trainee_name']}", f"{low_scorer['Total Score']:.1f}% Avg", delta_color="inverse")
                
                st.markdown("#### Comprehensive Analytical Scorecard Breakdown Table View")
                st.dataframe(summary_agg, use_container_width=True, hide_index=True)
                
                # Excel Export Functionality Engine Structure
                import io
                buf = io.BytesIO()
                with pd.ExcelWriter(buf, engine="openpyxl") as writer:
                    summary_agg.to_excel(writer, index=False, sheet_name="Induction Final Performance")
                st.download_button(
                    "📊 Export Final Onboarding Report to Excel Format",
                    data=buf.getvalue(),
                    file_name=f"induction_performance_report_{date.today().isoformat()}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )

    # ==========================================
    # 3. REFRESHER TRAINING (PLACEHOLDER)
    # ==========================================
    # ==========================================
    # 3. REFRESHER TRAINING (ADMIN VIEW)
    # ==========================================
    with admin_tab3:
        st.header("Refresher Training Management")
        
        ref_admin_tab1, ref_admin_tab2 = st.tabs([
            "📥 Incoming Requests Board", 
            "🧙 Scheduling Wizard & Active Sessions"
        ])
        
        # ---------------------------------------------------------
        # TAB 1: Incoming Request Board
        # ---------------------------------------------------------
        with ref_admin_tab1:
            st.subheader("Agent Submitted Refresher Requests")
            incoming_requests = db.get_refresher_requests()
            
            # Filter only pending requests
            pending_reqs = [r for r in incoming_requests if r["status"] == "Pending"]
            
            if not pending_reqs:
                st.info("No pending refresher requests at the moment.")
            else:
                req_df = pd.DataFrame(pending_reqs)[["name", "empid", "channel", "topic_name", "preferred_slot"]]
                req_df.columns = ["Agent Name", "Emp ID", "Channel", "Requested Topic", "Preferred Slot"]
                st.dataframe(req_df, use_container_width=True, hide_index=True)
                
                # Bulk Action / Select to Schedule
                st.markdown("#### Action Board")
                with st.form("bulk_schedule_form"):
                    st.write("Group requests by topic to schedule a batch session:")
                    
                    # Group by unique pending topics
                    pending_topics = list(set([r["topic_name"] for r in pending_reqs]))
                    selected_group_topic = st.selectbox("Select Topic to Batch-Schedule", pending_topics)
                    
                    # Find agents requesting this topic
                    target_agents = [r for r in pending_reqs if r["topic_name"] == selected_group_topic]
                    agent_names = [f"{a['name']} ({a['empid']})" for a in target_agents]
                    
                    st.multiselect("Selected Agents for this Session", agent_names, default=agent_names)
                    
                    # Schedule Time Picker
                    col_dt1, col_dt2 = st.columns(2)
                    sched_date = col_dt1.date_input("Scheduled Date", value=date.today())
                    sched_time = col_dt2.time_input("Scheduled Time")
                    
                    submit_schedule = st.form_submit_button("📅 Confirm & Schedule Batch Session")
                    
                    if submit_schedule:
                        session_id = str(uuid.uuid4())
                        topic_id = target_agents[0]["topic_id"]
                        combined_time = f"{sched_date.isoformat()} {sched_time.strftime('%I:%M %p')}"
                        agent_ids_list = [a['empid'] for a in target_agents]
                        
                        # Save active schedule
                        db.insert_refresher_schedule({
                            "id": session_id,
                            "topic_id": topic_id,
                            "scheduled_time": combined_time,
                            "agent_ids": json.dumps(agent_ids_list),
                            "status": "Active"
                        })
                        
                        # Update individual request status to 'Scheduled'
                        for a in target_agents:
                            db.update_refresher_request_status(a["id"], "Scheduled")
                            
                        st.success(f"Successfully scheduled batch refresher session for '{selected_group_topic}' at {combined_time}!")
                        st.rerun()

        # ---------------------------------------------------------
        # TAB 2: Scheduling Wizard & Active Sessions
        # ---------------------------------------------------------
        with ref_admin_tab2:
            st.subheader("Currently Scheduled Active Sessions")
            active_sessions = db.get_active_refresher_schedules()
            
            if not active_sessions:
                st.info("No active scheduled sessions found.")
            else:
                for session in active_sessions:
                    with st.container(border=True):
                        c_s1, c_s2 = st.columns([3, 1])
                        
                        # Parse agent IDs from JSON
                        session_agents = json.loads(session["agent_ids"])
                        
                        c_s1.markdown(f"### 📚 Topic: {session['topic_name']}")
                        c_s1.markdown(f"**⏰ Scheduled Time:** {session['scheduled_time']}")
                        c_s1.write(f"**👥 Confirmed Agents (EMP IDs):** {', '.join(session_agents)}")
                        
                        # Trigger session completion
                        with c_s2:
                            if st.button("✅ Mark as Completed", key=f"complete_session_{session['id']}"):
                                db.update_refresher_schedule_status(session["id"], "Completed")
                                st.success("Session completed and closed.")
                                st.rerun()

else:
    # ==========================================
    # AGENT WORKSPACE PORTAL (COMPLETE VIEW)
    # ==========================================
    st.header("Agent Self-Service & Training Hub")
    
    agent_tab1, agent_tab2 = st.tabs([
        "📖 Self-Paced Learning & Quizzes", 
        "🔁 Request Refresher Session"
    ])
    
    # ---------------------------------------------------------
    # TAB 1: Self-Paced Learning (Self-Training)
    # ---------------------------------------------------------
    with agent_tab1:
        st.subheader("Interactive Knowledge Hub")
        
        # User Authentication Form
        if "agent_authenticated" not in st.session_state:
            st.session_state.agent_authenticated = False
            
        if not st.session_state.agent_authenticated:
            with st.form("agent_login_form"):
                st.markdown("#### Enter Your Details to Access Portal")
                ag_name = st.text_input("Full Name *")
                ag_id = st.text_input("Employee ID *")
                ag_chan = st.selectbox("Your Operating Channel", ["Voice", "Chat", "Email"])
                
                if st.form_submit_button("Access Training Modules"):
                    if not ag_name or not ag_id:
                        st.error("Name and Employee ID are required to proceed.")
                    else:
                        st.session_state.agent_name = ag_name.strip()
                        st.session_state.agent_empid = ag_id.strip()
                        st.session_state.agent_channel = ag_chan
                        st.session_state.agent_authenticated = True
                        st.rerun()
        else:
            st.success(f"Active Session: **{st.session_state.agent_name}** ({st.session_state.agent_empid}) — Channel: {st.session_state.agent_channel}")
            if st.button("Log Out / Change Profile"):
                st.session_state.agent_authenticated = False
                st.rerun()
                
            st.divider()
            
            # Fetch All Central Topics
            all_topics = db.get_topics()
            if not all_topics:
                st.info("No training modules found in the database. Please check back later.")
            else:
                topic_options = {t["name"]: t for t in all_topics}
                selected_topic_name = st.selectbox("Select Study Topic *", list(topic_options.keys()))
                selected_topic = topic_options[selected_topic_name]
                
                # Dynamic Tabs for Learning Content
                st.markdown(f"### Study Material: **{selected_topic['name']}**")
                st.caption(f"⏱️ Estimated Study Time: {selected_topic['duration']}")
                
                study_tabs = st.tabs([
                    "📖 Core Knowledge", 
                    "🛠️ Tools & Systems", 
                    "🔀 Step-by-Step Process", 
                    "💬 Response Templates"
                ])
                
                with study_tabs[0]:
                    st.markdown("#### Service Knowledge Guidelines")
                    st.write(selected_topic["service_knowledge"] or "No guidelines uploaded for this section.")
                with study_tabs[1]:
                    st.markdown("#### Required Systems & Checkpoints")
                    st.write(selected_topic["tools_introduction"] or "No tools detailed for this section.")
                    if selected_topic["tools_checkpoint"]:
                        st.markdown("**Action Checkpoints:**")
                        for point in selected_topic["tools_checkpoint"].split("\n"):
                            st.checkbox(point, key=f"cp_{selected_topic['id']}_{point[:15]}")
                with study_tabs[2]:
                    st.markdown("#### Workflow Resolution Path")
                    st.info(selected_topic["process_flow"] or "No process workflows mapped.")
                with study_tabs[3]:
                    st.markdown("#### Communication Scripts & Templates")
                    st.write(selected_topic["communication_scripts"] or "No communication scripts provided.")
                
                st.divider()
                
                # Dynamic Quiz Creator Engine
                st.markdown("### 📝 Dynamic Evaluation Check")
                try:
                    quiz_data = json.loads(selected_topic["quiz_questions"])
                except Exception:
                    quiz_data = []
                    
                if not quiz_data or len(quiz_data) == 0:
                    st.warning("No assessment quiz is linked to this topic yet.")
                else:
                    st.write("Complete the assessment below to earn your 'Completed' badge:")
                    
                    user_answers = {}
                    for idx, question in enumerate(quiz_data):
                        st.markdown(f"**Q{idx+1}. {question['question']}**")
                        user_answers[idx] = st.radio(
                            "Select Answer:", 
                            question["options"], 
                            key=f"q_{selected_topic['id']}_{idx}"
                        )
                        st.write("")
                    
                    if st.button("Submit Assessment & Finish Topic"):
                        # Calculate Score
                        correct_count = 0
                        for idx, question in enumerate(quiz_data):
                            if user_answers[idx] == question["answer"]:
                                correct_count += 1
                                
                        score_percentage = int((correct_count / len(quiz_data)) * 100)
                        passing_score = selected_topic["quiz_passing_mark"]
                        
                        if score_percentage >= passing_score:
                            st.balloons()
                            st.success(f"🎉 Passed! Your Score: {score_percentage}% (Required: {passing_score}%)")
                            db.insert_self_training_score(
                                empid=st.session_state.agent_empid,
                                name=st.session_state.agent_name,
                                topic_id=selected_topic["id"],
                                topic_name=selected_topic["name"],
                                score=score_percentage,
                                status="Passed"
                            )
                        else:
                            st.error(f"❌ Failed. Your Score: {score_percentage}% (Required: {passing_score}%). Please try again.")

    # ---------------------------------------------------------
    # TAB 2: Refresher Training Request
    # ---------------------------------------------------------
    with agent_tab2:
        st.subheader("Request for Refresher Assistance")
        st.write("Can't resolve specific customer issues? Request a classroom refresher with a trainer.")
        
        if "agent_authenticated" not in st.session_state or not st.session_state.agent_authenticated:
            st.warning("Please sign-in inside the 'Self-Paced Learning' tab to request training.")
        else:
            with st.form("refresher_request_form", clear_on_submit=True):
                st.markdown("#### Refresher Details")
                st.text_input("Your Name", value=st.session_state.agent_name, disabled=True)
                st.text_input("Your Employee ID", value=st.session_state.agent_empid, disabled=True)
                
                # Fetch available topics from database
                all_topics = db.get_topics()
                topic_options = {t["name"]: t["id"] for t in all_topics} if all_topics else {}
                
                selected_topic_name = st.selectbox("Select Topic You Need Help With *", list(topic_options.keys()) if topic_options else ["No Topics Available"])
                
                # Available Time Slots (Date & Time input helper)
                req_date = st.date_input("Preferred Date", value=date.today())
                req_time = st.selectbox("Preferred Hour Slot", [
                    "11:00 AM - 01:00 PM",
                    "02:00 PM - 04:00 PM",
                    "04:00 PM - 06:00 PM",
                    "06:00 PM - 08:00 PM"
                ])
                
                submit_req = st.form_submit_button("Submit Request to Training Queue")
                
                if submit_req:
                    if not topic_options:
                        st.error("Cannot submit. No topics exist in the Database.")
                    else:
                        req_payload = {
                            "id": str(uuid.uuid4()),
                            "empid": st.session_state.agent_empid,
                            "name": st.session_state.agent_name,
                            "channel": st.session_state.agent_channel,
                            "topic_id": topic_options[selected_topic_name],
                            "preferred_slot": f"{req_date.isoformat()} ({req_time})",
                            "status": "Pending"
                        }
                        db.insert_refresher_request(req_payload)
                        st.success("Your request has been successfully queued. Trainers will review and schedule a session soon.")

import streamlit as st
import pandas as pd
import json
import uuid
import base64
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
/* Topic Card Custom CSS */
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
.embed-container {
    position: relative;
    padding-bottom: 56.25%;
    height: 0;
    overflow: hidden;
    max-width: 100%;
    border-radius: 10px;
    border: 1px solid #2A3A34;
}
.embed-container iframe {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
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
        "🔁 Refresher Training"
    ])
    
    # ==========================================
    # 1. CENTRAL TOPIC & LINK MANAGER (UPDATED)
    # ==========================================
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
                            "site_url": site_url.strip() # Saved netlify link
                        }
                        db.upsert_topic(topic_payload)
                        st.success(f"Topic '{t_name}' saved with Netlify link!")
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

    # ==========================================
    # 2. INDUCTION TRAINING
    # ==========================================
    with admin_tab2:
        st.header("Induction Training Dashboard")
        
        ind_l1, ind_l2, ind_l3, ind_l4 = st.tabs([
            "👥 Trainee Onboarding", 
            "📅 Timeline Setup", 
            "⚡ Schedule & Grading", 
            "📊 Performance Report"
        ])
        
        with ind_l1:
            st.subheader("Onboard New Joiners")
            col_b1, col_b2 = st.columns([1, 1])
            with col_b1:
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
                            st.success(f"Trainee {t_name} onboarded.")
                            st.rerun()
            
            with col_b2:
                uploaded_csv = st.file_uploader("Bulk Import via CSV", type=["csv"])
                if uploaded_csv:
                    try:
                        csv_df = pd.read_csv(uploaded_csv)
                        required_cols = ["empid", "name", "email", "phone", "joining_date", "channel"]
                        if all(col in csv_df.columns for col in required_cols):
                            trainee_list = csv_df[required_cols].to_dict(orient="records")
                            db.insert_trainees(trainee_list)
                            st.success(f"Processed {len(trainee_list)} trainees.")
                            st.rerun()
                        else:
                            st.error(f"CSV requires headers: {required_cols}")
                    except Exception as e:
                        st.error(f"Error: {str(e)}")
            
            st.divider()
            current_trainees = db.get_trainees()
            if current_trainees:
                st.dataframe(pd.DataFrame(current_trainees), use_container_width=True, hide_index=True)

        with ind_l2:
            st.subheader("Timeline Setup")
            col_time1, col_time2 = st.columns([1, 2])
            with col_time1:
                start_range = st.date_input("Batch Start Date", key="ind_start")
                end_range = st.date_input("Batch End Date", key="ind_end")
            
            with col_time2:
                if start_range <= end_range:
                    delta_days = (end_range - start_range).days + 1
                    st.info(f"**{delta_days} Days** configured.")
                    grid_cols = st.columns(min(7, delta_days))
                    for day_idx in range(delta_days):
                        current_day = start_range + pd.Timedelta(days=day_idx)
                        day_str = current_day.isoformat()
                        col_pos = day_idx % 7
                        with grid_cols[col_pos]:
                            if st.button(f"📅 Day {day_idx+1}\n{current_day.strftime('%b %d')}", key=f"timeline_{day_str}", use_container_width=True):
                                st.session_state.active_induction_date = day_str
                                st.success(f"Selected: {day_str}")

        with ind_l3:
            target_date = st.session_state.get("active_induction_date", None)
            if not target_date:
                st.warning("⚠️ Pick a target day from Timeline Setup first.")
            else:
                st.subheader(f"Operations for Day [{target_date}]")
                c_sched1, c_sched2 = st.columns([2, 3])
                with c_sched1:
                    hours_slots = [
                        "11:00 AM - 12:00 PM", "12:00 PM - 01:00 PM", "01:00 PM - 02:00 PM",
                        "02:00 PM - 03:00 PM", "03:00 PM - 04:00 PM", "04:00 PM - 05:00 PM",
                        "05:00 PM - 06:00 PM", "06:00 PM - 07:00 PM", "07:00 PM - 08:00 PM"
                    ]
                    with st.form("hourly_planner_form"):
                        slot_selection = st.selectbox("Select Time Slot", hours_slots)
                        act_type = st.radio("Activity Type", ["Core Database Topic", "Break / Custom Task"])
                        db_topics = db.get_topics()
                        topic_options = {top['name']: top['id'] for top in db_topics}
                        selected_topic_name = st.selectbox("Topic", list(topic_options.keys()) if db_topics else ["None"])
                        custom_text = st.text_input("Custom Activity Details")
                        
                        if st.form_submit_button("Save Slot"):
                            sched_id = f"{target_date}_{slot_selection.replace(' ', '')}"
                            db.upsert_induction_schedule({
                                "id": sched_id, "date": target_date, "time_slot": slot_selection,
                                "activity_type": act_type,
                                "topic_id": topic_options[selected_topic_name] if (act_type == "Core Database Topic" and db_topics) else None,
                                "manual_activity": custom_text if act_type != "Core Database Topic" else selected_topic_name
                            })
                            st.success("Slot saved.")
                            st.rerun()
                
                with c_sched2:
                    day_schedule = db.get_induction_schedule_by_date(target_date)
                    if day_schedule:
                        st.table(pd.DataFrame(day_schedule)[["time_slot", "activity_type", "manual_activity"]].sort_values(by="time_slot"))
                
                st.divider()
                st.markdown("#### Grading Portal")
                all_trainees = db.get_trainees()
                if all_trainees:
                    with st.form("grading_engine_form"):
                        g_trainee = st.selectbox("Trainee Profile", [f"{t['name']} ({t['empid']})" for t in all_trainees])
                        target_empid = g_trainee.split("(")[-1].replace(")", "").strip()
                        c_s1, c_s2 = st.columns(2)
                        quiz_score = c_s1.number_input("Quiz Score", 0, 100, 0)
                        assignment_score = c_s2.number_input("Assignment Score", 0, 100, 0)
                        eval_notes = st.text_area("Trainer Remarks")
                        
                        if st.form_submit_button("Record Grade"):
                            db.upsert_trainee_evaluation({
                                "id": f"{target_empid}_{target_date}", "empid": target_empid, "date": target_date,
                                "quiz_score": int(quiz_score), "assignment_score": int(assignment_score), "notes": eval_notes.strip()
                            })
                            st.success("Grades logged.")
                            st.rerun()

        with ind_l4:
            st.subheader("Performance Report Dashboard")
            raw_evals = db.get_all_evaluations()
            if raw_evals:
                eval_df = pd.DataFrame(raw_evals)
                eval_df['Total Score'] = (eval_df['quiz_score'] + eval_df['assignment_score']) / 2
                summary_agg = eval_df.groupby(['empid', 'trainee_name', 'channel'])['Total Score'].mean().reset_index()
                st.dataframe(summary_agg, use_container_width=True, hide_index=True)

    # ==========================================
    # 3. REFRESHER TRAINING
    # ==========================================
    with admin_tab3:
        st.header("Refresher Requests & Schedules")
        incoming_requests = db.get_refresher_requests()
        pending_reqs = [r for r in incoming_requests if r["status"] == "Pending"]
        
        if pending_reqs:
            req_df = pd.DataFrame(pending_reqs)[["name", "empid", "channel", "topic_name", "preferred_slot"]]
            st.dataframe(req_df, use_container_width=True, hide_index=True)

else:
    # ==========================================
    # AGENT WORKSPACE PORTAL (CARD VIEW UPDATED)
    # ==========================================
    st.header("Agent Self-Service Hub")
    
    agent_tab1, agent_tab2 = st.tabs([
        "📖 Study Topics & Take Quiz", 
        "🔁 Request Refresher Session"
    ])
    
    with agent_tab1:
        if "agent_authenticated" not in st.session_state:
            st.session_state.agent_authenticated = False
            
        if not st.session_state.agent_authenticated:
            with st.form("agent_login_form"):
                st.markdown("#### Agent Sign In")
                ag_name = st.text_input("Full Name *")
                ag_id = st.text_input("Employee ID *")
                ag_chan = st.selectbox("Channel", [" ", "Inbound", "Live Chat & Social Media", "Report Issue & Email", "Complaint Management", "Campaign Management"])
                ag_topic = st.selectbox("Topic", [" ", "Rider Joining Process", "Joining Bonus & Referral Program", "Star Program", "Fare Information", "Due & Payment", "Flagged Trips", "Payment Flow", "SOPs & Internal Tools", "Parcel Service"])
                
                
                if st.form_submit_button("Access Portal"):
    # ৪টি ফিল্ডের কোনো একটি খালি থাকলেই এরর দেখাবে
    if not ag_name.strip() or not ag_id.strip() or not ag_chan or not ag_topic:
        st.error("⚠️ All fields (Name, Employee ID, Channel, and Topic) are required!")
    else:
        st.session_state.agent_name = ag_name.strip()
        st.session_state.agent_empid = ag_id.strip()
        st.session_state.agent_channel = ag_chan
        st.session_state.agent_topic = ag_topic  # session_state-এ topic সেভ করা হলো
        st.session_state.agent_authenticated = True
        st.rerun()
        else:
            st.success(f"Active Session: **{st.session_state.agent_name}** ({st.session_state.agent_empid})")
            if st.button("Log Out"):
                st.session_state.agent_authenticated = False
                st.session_state.pop("selected_topic_id", None)
                st.rerun()
                
            st.divider()
            
            all_topics = db.get_topics()
            if not all_topics:
                st.info("No training topics available in the portal right now.")
            else:
                # ----------------------------------------------------
                # TOPIC CARDS GRID SYSTEM
                # ----------------------------------------------------
                if "selected_topic_id" not in st.session_state:
                    st.markdown("### 🎯 Select a Training Topic Card")
                    
                    # Creating a 3-Column Grid for Cards
                    cols = st.columns(3)
                    for idx, topic in enumerate(all_topics):
                        col = cols[idx % 3]
                        with col:
                            st.markdown(f"""
                            <div class="topic-card-box">
                                <h3>📚 {topic['name']}</h3>
                                <p style="color: #a0a0a0; margin-bottom: 5px;">⏱️ Duration: <b>{topic['duration']}</b></p>
                                <p style="color: #a0a0a0;">👤 Trainer: <b>{topic.get('trainer_name', 'N/A')}</b></p>
                            </div>
                            """, unsafe_allow_html=True)
                            
                            if st.button(f"Open Module ➔", key=f"btn_card_{topic['id']}"):
                                st.session_state.selected_topic_id = topic['id']
                                st.rerun()
                            st.write("")
                
                # ----------------------------------------------------
                # SELECTED TOPIC VIEW (WEBVIEW EMBED + QUIZ)
                # ----------------------------------------------------
                else:
                    selected_topic = next((t for t in all_topics if t["id"] == st.session_state.selected_topic_id), None)
                    
                    if selected_topic:
                        if st.button("⬅️ Back to All Topics Card Grid"):
                            st.session_state.pop("selected_topic_id", None)
                            st.rerun()
                        
                        st.markdown(f"## 📖 Module: **{selected_topic['name']}**")
                        st.caption(f"⏱️ Duration: {selected_topic['duration']} | Assigned Trainer: {selected_topic.get('trainer_name', 'N/A')}")
                        
                        # Netlify Website Embed View
                        site_url = selected_topic.get("site_url", "")
                        if site_url:
                            st.markdown(f"#### 🌐 Embedded Training Material")
                            st.components.v1.iframe(site_url, height=650, scrolling=True)
                            st.markdown(f"🔗 *Having trouble viewing? [Click here to open in new tab]({site_url})*")
                        else:
                            st.warning("No Netlify URL attached to this topic.")
                        
                        st.divider()
                        
                        # 5-QUESTION QUIZ ENGINE
                        st.markdown("### 📝 Topic Quiz Assessment")
                        try:
                            quiz_data = json.loads(selected_topic.get("quiz_questions", "[]"))
                        except Exception:
                            quiz_data = []
                            
                        if not quiz_data:
                            st.info("No quiz has been created for this topic yet.")
                        else:
                            st.write(f"Answer the questions below to complete this topic (Passing mark: {selected_topic.get('quiz_passing_mark', 80)}%):")
                            
                            user_answers = {}
                            for idx, question in enumerate(quiz_data):
                                st.markdown(f"**Q{idx+1}. {question['question']}**")
                                user_answers[idx] = st.radio(
                                    "Select Your Option:", 
                                    [opt for opt in question["options"] if opt.strip() != ""], 
                                    key=f"q_{selected_topic['id']}_{idx}"
                                )
                                st.write("")
                            
                            if st.button("Submit Quiz Answers"):
                                correct_count = 0
                                for idx, question in enumerate(quiz_data):
                                    if user_answers.get(idx) == question["answer"]:
                                        correct_count += 1
                                        
                                score_percentage = int((correct_count / len(quiz_data)) * 100)
                                passing_score = selected_topic.get("quiz_passing_mark", 80)
                                
                                if score_percentage >= passing_score:
                                    st.balloons()
                                    st.success(f"🎉 Passed! Your Score: {score_percentage}% (Correct: {correct_count}/{len(quiz_data)})")
                                    db.insert_self_training_score(
                                        empid=st.session_state.agent_empid,
                                        name=st.session_state.agent_name,
                                        topic_id=selected_topic["id"],
                                        topic_name=selected_topic["name"],
                                        score=score_percentage,
                                        status="Passed"
                                    )
                                else:
                                    st.error(f"❌ Failed. Your Score: {score_percentage}%. Please review the topic material and try again.")

    with agent_tab2:
        st.subheader("Request Refresher Session")
        if "agent_authenticated" in st.session_state and st.session_state.agent_authenticated:
            with st.form("refresher_request_form", clear_on_submit=True):
                all_topics = db.get_topics()
                topic_options = {t["name"]: t["id"] for t in all_topics} if all_topics else {}
                selected_topic_name = st.selectbox("Select Topic *", list(topic_options.keys()) if topic_options else ["None"])
                req_date = st.date_input("Preferred Date", value=date.today())
                req_time = st.selectbox("Preferred Slot", ["11:00 AM - 01:00 PM", "02:00 PM - 04:00 PM", "04:00 PM - 06:00 PM"])
                
                if st.form_submit_button("Submit Request"):
                    if topic_options:
                        db.insert_refresher_request({
                            "id": str(uuid.uuid4()),
                            "empid": st.session_state.agent_empid,
                            "name": st.session_state.agent_name,
                            "channel": st.session_state.agent_channel,
                            "topic_id": topic_options[selected_topic_name],
                            "preferred_slot": f"{req_date.isoformat()} ({req_time})",
                            "status": "Pending"
                        })
                        st.success("Request submitted to trainers queue.")

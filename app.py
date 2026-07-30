import streamlit as st
import pandas as pd
import uuid
import json
import requests
from datetime import date, timedelta

import db

st.set_page_config(page_title="Pathao CX Training Portal", page_icon="🎓", layout="wide")
db.init_db()

# Custom CSS Styling
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
</style>
""", unsafe_allow_html=True)

# Helper functions
def format_embed_url(url):
    if not url: return ""
    if "/edit" in url: return url.split("/edit")[0] + "/embed"
    elif "/pub" in url: return url.split("/pub")[0] + "/embed"
    elif not url.endswith("/embed") and "docs.google.com/presentation" in url:
        return url.rstrip('/') + "/embed"
    return url

def format_form_url(url):
    if not url: return ""
    if "docs.google.com/forms" in url and not url.endswith("embedded=true"):
        if "?" in url: return url + "&embedded=true"
        return url + "?embedded=true"
    return url

# Auth State
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
    admin_tab1, admin_tab2, admin_tab3, admin_tab4, admin_tab5 = st.tabs([
        "👥 Agent Information", 
        "📊 Topics & Quiz Editor", 
        "📅 Induction Calendar Planner", 
        "📝 Agent Evaluation", 
        "🔁 Refresher Requests"
    ])
    
    # 1. AGENT INFORMATION DIRECTORY
    with admin_tab1:
        st.header("👥 Induction Agent Information Directory")
        st.caption("Add and manage agent info: Name, EMP ID, Email, and Phone Number.")
        
        with st.expander("➕ Add / Edit Agent Record", expanded=False):
            with st.form("agent_info_form"):
                col1, col2 = st.columns(2)
                ag_id = col1.text_input("EMP ID *")
                ag_name = col2.text_input("Agent Name *")
                col3, col4 = st.columns(2)
                ag_email = col3.text_input("Email Address *")
                ag_phone = col4.text_input("Phone Number *")
                
                if st.form_submit_button("💾 Save Agent"):
                    if not ag_id or not ag_name or not ag_email:
                        st.error("EMP ID, Name, and Email are mandatory!")
                    else:
                        db.upsert_agent(ag_id.strip(), ag_name.strip(), ag_email.strip(), ag_phone.strip())
                        st.success("Agent Info saved successfully!")
                        st.rerun()

        st.subheader("Registered Agents List")
        agents = db.get_agents()
        if not agents:
            st.info("No Agents registered yet.")
        else:
            df_ag = pd.DataFrame(agents)
            st.dataframe(df_ag, use_container_width=True)
            for ag in agents:
                if st.button(f"🗑️ Delete Agent {ag['name']} ({ag['empid']})", key=f"del_ag_{ag['empid']}"):
                    db.delete_agent(ag['empid'])
                    st.rerun()

    # 2. TOPICS & QUIZ FORM EDITOR
    with admin_tab2:
        st.header("📊 Topics, Time & Quiz Form Link Manager")
        st.caption("Update Topic Duration (Time) or Google Form Links for existing modules.")
        
        topics_list = db.get_topics()
        for top in topics_list:
            with st.expander(f"⚙️ Edit Module: **{top['name']}**", expanded=False):
                with st.form(f"edit_top_form_{top['id']}"):
                    c1, c2 = st.columns(2)
                    new_time = c1.text_input("Duration / Time *", value=top.get('duration', ''), key=f"time_{top['id']}")
                    new_trainer = c2.text_input("Trainer Name *", value=top.get('trainer_name', 'Md Asikul islam Azman'), key=f"tr_{top['id']}")
                    
                    new_slide = st.text_input("Google Slide Link", value=top.get('slide_url', ''), key=f"slide_{top['id']}")
                    new_form = st.text_input("Quiz Form Link (Google Form / Typeform)", value=top.get('form_url', ''), key=f"form_{top['id']}")
                    
                    if st.form_submit_button("💾 Update Topic Details"):
                        db.upsert_topic({
                            "id": top['id'],
                            "name": top['name'],
                            "duration": new_time.strip(),
                            "trainer_name": new_trainer.strip(),
                            "slide_url": format_embed_url(new_slide.strip()),
                            "form_url": format_form_url(new_form.strip())
                        })
                        st.success(f"Topic '{top['name']}' updated!")
                        st.rerun()

    # 3. INDUCTION CALENDAR PLANNER (MULTI-SLOT SUPPORTED)
    with admin_tab3:
        st.header("📅 Induction Training Period Calendar Planner")
        st.caption("Select Date Range, add multiple time slots/topics per day, or mark Day Off.")
        
        # Step 1: Period Selection Form
        with st.form("period_select_form"):
            b_col1, b_col2, b_col3 = st.columns([2, 1.5, 1.5])
            batch_title = b_col1.text_input("Batch / Training Name", value="Induction Batch - Rides")
            date_from = b_col2.date_input("Date From", value=date.today())
            date_to = b_col3.date_input("Date To", value=date.today() + timedelta(days=6))
            
            p_submit = st.form_submit_button("📅 Generate Day-wise Planner")

        if "current_planner" not in st.session_state or p_submit:
            if date_from > date_to:
                st.error("'Date From' cannot be later than 'Date To'!")
            else:
                num_days = (date_to - date_from).days + 1
                dates_list = [(date_from + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(num_days)]
                
                day_slots = {}
                for d in dates_list:
                    day_slots[d] = [
                        {"type": "Topic Session", "topic": "", "custom": "", "time": "10:00 AM - 01:00 PM", "trainer": "Md Asikul islam Azman", "off": False}
                    ]
                
                st.session_state.current_planner = {
                    "batch": batch_title,
                    "from": date_from.strftime("%Y-%m-%d"),
                    "to": date_to.strftime("%Y-%m-%d"),
                    "dates": dates_list,
                    "day_slots": day_slots
                }

        planner_data = st.session_state.get("current_planner", None)
        
        # Safe Fallback to avoid KeyError from old session states
        if planner_data and "day_slots" not in planner_data:
            planner_data["day_slots"] = {}
            for d in planner_data.get("dates", []):
                planner_data["day_slots"][d] = [
                    {"type": "Topic Session", "topic": "", "custom": "", "time": "10:00 AM - 01:00 PM", "trainer": "Md Asikul islam Azman", "off": False}
                ]

        if planner_data:
            st.divider()
            st.subheader(f"📌 Planning for: **{planner_data['batch']}** ({planner_data['from']} to {planner_data['to']})")
            
            topics_db = db.get_topics()
            topic_names = ["-- Select Topic --"] + [t['name'] for t in topics_db]
            
            webhook_url = st.text_input("🔗 Google Sheet Webhook URL (Apps Script / Webhook)", 
                                        placeholder="https://script.google.com/macros/s/.../exec")

            full_schedule_output = []

            # Loop through days
            for idx, d_str in enumerate(planner_data.get("dates", [])):
                dt_obj = date.fromisoformat(d_str)
                day_name = dt_obj.strftime("%A")
                
                st.markdown(f"### 🗓️ Day {idx+1}: `{d_str}` ({day_name})")
                
                # Check Day Off toggle
                is_day_off = st.checkbox(f"🔴 Mark Entire Day as DAY OFF", key=f"off_day_{d_str}")
                
                if is_day_off:
                    st.info("This day is marked as Day Off.")
                    full_schedule_output.append({
                        "Date": d_str,
                        "Day": day_name,
                        "Activity / Topic": "DAY OFF",
                        "Time Slot": "N/A",
                        "Trainer": "N/A",
                        "Status": "Day Off"
                    })
                else:
                    slots = planner_data.get("day_slots", {}).get(d_str, [])
                    
                    for s_idx, slot in enumerate(slots):
                        st.markdown(f"**Slot #{s_idx+1}**")
                        c1, c2, c3, c4 = st.columns([1.5, 2, 2, 0.5])
                        
                        st_type = c1.selectbox("Activity Type", ["Topic Session", "Other Task / Exam / Mock Call"], key=f"type_{d_str}_{s_idx}")
                        
                        if st_type == "Topic Session":
                            st_topic = c2.selectbox("Select Topic", topic_names, key=f"top_{d_str}_{s_idx}")
                            act_title = st_topic if st_topic != "-- Select Topic --" else "Topic Session"
                        else:
                            act_title = c2.text_input("Task / Exam Title", value="Mock Call & Feedback", key=f"cust_{d_str}_{s_idx}")
                            
                        st_time = c3.text_input("Time Slot", value=slot.get("time", "10:00 AM - 01:00 PM"), key=f"time_{d_str}_{s_idx}")
                        st_trainer = c3.text_input("Trainer Name", value=slot.get("trainer", "Md Asikul islam Azman"), key=f"tr_{d_str}_{s_idx}")
                        
                        if c4.button("🗑️", key=f"del_slot_{d_str}_{s_idx}"):
                            planner_data["day_slots"][d_str].pop(s_idx)
                            st.rerun()

                        full_schedule_output.append({
                            "Date": d_str,
                            "Day": day_name,
                            "Activity / Topic": act_title,
                            "Time Slot": st_time,
                            "Trainer": st_trainer,
                            "Status": "Scheduled"
                        })

                    # Button to Add Extra Slot in the same day
                    if st.button(f"➕ Add Another Slot for {d_str}", key=f"add_slot_{d_str}"):
                        if d_str not in planner_data["day_slots"]:
                            planner_data["day_slots"][d_str] = []
                        planner_data["day_slots"][d_str].append({
                            "type": "Topic Session", "topic": "", "custom": "", "time": "02:00 PM - 05:00 PM", "trainer": "Md Asikul islam Azman", "off": False
                        })
                        st.rerun()

                st.divider()

            # Publish Calendar Button
            if st.button("🚀 Publish Training Calendar to Google Sheet", type="primary"):
                sched_id = str(uuid.uuid4())
                json_str = json.dumps(full_schedule_output)
                db.save_batch_schedule(sched_id, planner_data['batch'], planner_data['from'], planner_data['to'], json_str, "Published")
                
                st.success("✅ Multi-slot Training Calendar saved successfully!")
                
                if webhook_url:
                    try:
                        resp = requests.post(webhook_url, json={
                            "batch": planner_data['batch'],
                            "schedule": full_schedule_output
                        }, timeout=10)
                        if resp.status_code in [200, 201]:
                            st.success("📊 Exported to Google Sheet successfully!")
                    except Exception as e:
                        st.error(f"Error posting to Webhook: {e}")

                df_export = pd.DataFrame(full_schedule_output)
                st.dataframe(df_export, use_container_width=True)
                csv = df_export.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="📥 Download CSV for Google Sheets",
                    data=csv,
                    file_name=f"{planner_data['batch']}_calendar.csv",
                    mime="text/csv"
                )

        st.subheader("📁 Saved / Published Calendars")
        batches = db.get_batch_schedules()
        if not batches:
            st.info("No Published Calendars found.")
        else:
            for b in batches:
                with st.expander(f"📆 **{b['batch_name']}** ({b['start_date']} to {b['end_date']})"):
                    data_list = json.loads(b['schedule_json'])
                    st.dataframe(pd.DataFrame(data_list), use_container_width=True)
                    if st.button("🗑️ Delete Schedule", key=f"del_b_{b['id']}"):
                        db.delete_batch_schedule(b['id'])
                        st.rerun()

    # 4. AGENT EVALUATION SYSTEM
    with admin_tab4:
        st.header("📝 Induction Agent Evaluation System")
        evals = db.get_evaluations()
        if not evals:
            st.warning("No Agents found in directory. Please add agents in the 'Agent Information' tab first.")
        else:
            st.subheader("Agent Score Card Sheet")
            for ev in evals:
                with st.expander(f"👤 Agent: **{ev['agent_name']}** (EMP ID: `{ev['empid']}`)", expanded=True):
                    with st.form(f"eval_form_{ev['empid']}"):
                        c1, c2, c3, c4 = st.columns(4)
                        q1 = c1.number_input("Quiz 1 Score", min_value=0.0, max_value=100.0, value=float(ev['quiz1']), key=f"q1_{ev['empid']}")
                        q2 = c2.number_input("Quiz 2 Score", min_value=0.0, max_value=100.0, value=float(ev['quiz2']), key=f"q2_{ev['empid']}")
                        q3 = c3.number_input("Quiz 3 Score", min_value=0.0, max_value=100.0, value=float(ev['quiz3']), key=f"q3_{ev['empid']}")
                        ass = c4.number_input("Assignment", min_value=0.0, max_value=100.0, value=float(ev['assignment']), key=f"ass_{ev['empid']}")
                        
                        c5, c6, c7 = st.columns(3)
                        mock = c5.number_input("Mock Call Score", min_value=0.0, max_value=100.0, value=float(ev['mock_call']), key=f"mock_{ev['empid']}")
                        live = c6.number_input("Live Communication", min_value=0.0, max_value=100.0, value=float(ev['live_comm']), key=f"live_{ev['empid']}")
                        
                        suggested_avg = round((q1 + q2 + q3 + ass + mock + live) / 6, 2)
                        final_sc = c7.number_input("Final Score", min_value=0.0, max_value=100.0, value=float(ev['final_score'] or suggested_avg), key=f"fin_{ev['empid']}")
                        
                        if st.form_submit_button("💾 Save Score Evaluation"):
                            db.update_evaluation(ev['empid'], q1, q2, q3, ass, mock, live, final_sc)
                            st.success(f"Scores saved for {ev['agent_name']}!")
                            st.rerun()

    # 5. REFRESHER REQUESTS
    with admin_tab5:
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
    # AGENT WORKSPACE PORTAL
    st.header("Agent Self-Service Hub")
    agent_tab1, agent_tab2, agent_tab3 = st.tabs(["📖 Study Topics & Take Quiz", "📅 View Training Calendar", "🔁 Request Refresher Session"])
    
    with agent_tab1:
        all_topics = db.get_topics()
        if not all_topics:
            st.info("No training topics available right now.")
        else:
            if "selected_topic_id" not in st.session_state:
                st.markdown("### 🎯 Select a Training Topic Card")
                cols = st.columns(3)
                for idx, topic in enumerate(all_topics):
                    col = cols[idx % 3]
                    with col:
                        st.markdown(f"""
                        <div class="topic-card-box">
                            <h3>📊 {topic['name']}</h3>
                            <p style="color: #a0a0a0; margin-bottom: 5px;">⏱️ Duration: <b>{topic['duration']}</b></p>
                            <p style="color: #a0a0a0;">👤 Trainer: <b>{topic.get('trainer_name', 'Md Asikul islam Azman')}</b></p>
                        </div>
                        """, unsafe_allow_html=True)
                        if st.button(f"Open Module ➔", key=f"btn_card_{topic['id']}"):
                            st.session_state.selected_topic_id = topic['id']
                            st.rerun()
                        st.write("")
            else:
                selected_topic = next((t for t in all_topics if t["id"] == st.session_state.selected_topic_id), None)
                if selected_topic:
                    if st.button("⬅️ Back to All Topic Cards"):
                        st.session_state.pop("selected_topic_id", None)
                        st.rerun()
                    
                    st.markdown(f"## 📊 Topic: **{selected_topic['name']}**")
                    st.caption(f"⏱️ Duration: {selected_topic['duration']} | Assigned Trainer: {selected_topic.get('trainer_name', 'Md Asikul islam Azman')}")
                    
                    content_tab1, content_tab2 = st.tabs(["📺 Study Presentation", "📝 Take Quiz Form"])
                    
                    with content_tab1:
                        embed_slide = format_embed_url(selected_topic.get("slide_url", ""))
                        if embed_slide:
                            st.components.v1.iframe(embed_slide, height=560, scrolling=False)
                        else:
                            st.warning("No Slide Presentation available.")
                            
                    with content_tab2:
                        embed_form = format_form_url(selected_topic.get("form_url", ""))
                        if embed_form:
                            st.components.v1.iframe(embed_form, height=700, scrolling=True)
                        else:
                            st.info("No Quiz Form link added for this topic yet. Admin can attach a Google Form link from Admin View.")

    with agent_tab2:
        st.subheader("📅 Published Training Schedules")
        published_batches = db.get_batch_schedules()
        if not published_batches:
            st.info("No active training schedule published yet.")
        else:
            for b in published_batches:
                st.markdown(f"### 📆 **{b['batch_name']}** (`{b['start_date']}` to `{b['end_date']}`)")
                data_list = json.loads(b['schedule_json'])
                st.dataframe(pd.DataFrame(data_list), use_container_width=True)

    with agent_tab3:
        st.subheader("🔁 Request Refresher Session")
        topics = db.get_topics()
        t_opts = [t["name"] for t in topics] if topics else []
        
        with st.form("agent_ref_form"):
            c1, c2 = st.columns(2)
            a_name = c1.text_input("Agent Name *")
            a_id = c2.text_input("EMP ID *")
            
            c3, c4 = st.columns(2)
            a_chan = c3.selectbox("Channel *", ["", "Inbound Voice", "Live Chat & Social Media", "Report Issue & Email", "Complaint Management", "Campaign Management"])
            a_topic = c4.selectbox("Topic Name *", [""] + t_opts) if t_opts else c4.text_input("Topic Name *")
            
            col1, col2 = st.columns(2)
            r_date = col1.date_input("Date *", value=date.today())
            r_time = col2.selectbox("Slot *", ["", "10:00 AM - 01:00 PM", "02:00 PM - 05:00 PM", "05:00 PM - 08:00 PM"])
            
            if st.form_submit_button("Submit Refresher Request"):
                if not a_name or not a_id or not a_chan or not a_topic or not r_time:
                    st.error("All fields marked with (*) are mandatory!")
                else:
                    db.insert_refresher_request({
                        "id": str(uuid.uuid4()), 
                        "empid": a_id, 
                        "name": a_name,
                        "channel": a_chan, 
                        "topic_name": a_topic,
                        "preferred_slot": f"{r_date.strftime('%d %b %Y')} ({r_time})"
                    })
                    st.success("Refresher Session Request submitted successfully to Admin!")

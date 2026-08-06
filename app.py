import streamlit as st
import pandas as pd
import uuid
import json
from datetime import date, datetime, timedelta
from io import BytesIO

from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

import db
try:
    import certificate as cert_generator
except ImportError:
    import cert_generator

st.set_page_config(page_title="Pathao CX Training Portal", page_icon="🔴", layout="wide")
db.init_db()

st.markdown("""
<style>
    .stMetric {
        background-color: #f8f9fa;
        border: 1px solid #e9ecef;
        border-radius: 10px;
        padding: 15px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    .card-box {
        background-color: #ffffff;
        border-left: 5px solid #E21B24;
        border-radius: 8px;
        padding: 18px;
        margin-bottom: 15px;
        box-shadow: 0 2px 6px rgba(0,0,0,0.06);
    }
    .card-box-info {
        background-color: #f1f3f5;
        border-left: 5px solid #1c7ed6;
        border-radius: 8px;
        padding: 18px;
        margin-bottom: 15px;
    }
</style>
""", unsafe_allow_html=True)

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

def generate_pdf_report(batch_info, covered_topics, df_evals):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
    story = []
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('TitleStyle', parent=styles['Heading1'], fontSize=18, textColor=colors.HexColor('#E21B24'), spaceAfter=10)
    sub_style = ParagraphStyle('SubStyle', parent=styles['Normal'], fontSize=11, textColor=colors.HexColor('#333333'), spaceAfter=15)
    heading_style = ParagraphStyle('HeadStyle', parent=styles['Heading2'], fontSize=13, textColor=colors.HexColor('#111111'), spaceAfter=8)

    story.append(Paragraph("Pathao Rides — Induction Performance Summary Report", title_style))
    if batch_info:
        info_text = f"<b>Batch Name:</b> {batch_info['batch_name']}<br/><b>Training Period:</b> {batch_info['start_date']} to {batch_info['end_date']}<br/><b>Status:</b> {batch_info['status']}"
    else:
        info_text = "<b>Batch Name:</b> N/A"
    story.append(Paragraph(info_text, sub_style))
    story.append(Spacer(1, 10))

    story.append(Paragraph("<b>Covered Topics in Training:</b>", heading_style))
    topics_str = ", ".join(covered_topics) if covered_topics else "No topics marked as completed yet."
    story.append(Paragraph(topics_str, sub_style))
    story.append(Spacer(1, 15))

    story.append(Paragraph("<b>Induction Employee Scorecard:</b>", heading_style))
    if not df_evals.empty:
        table_data = [["EMP ID", "Employee Name", "Quiz 1", "Quiz 2", "Quiz 3", "Assign.", "Mock", "Live", "Final Score"]]
        for _, row in df_evals.iterrows():
            table_data.append([
                str(row.get('empid', '')),
                str(row.get('agent_name', '')),
                str(row.get('quiz1', 0)),
                str(row.get('quiz2', 0)),
                str(row.get('quiz3', 0)),
                str(row.get('assignment', 0)),
                str(row.get('mock_call', 0)),
                str(row.get('live_comm', 0)),
                f"{row.get('final_score', 0):.2f}%"
            ])
        
        t = Table(table_data, colWidths=[55, 110, 45, 45, 45, 45, 45, 45, 65])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#E21B24')),
            ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTSIZE', (0,0), (-1,0), 9),
            ('BOTTOMPADDING', (0,0), (-1,0), 6),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#cccccc')),
            ('FONTNAME', (0,1), (-1,-1), 'Helvetica'),
            ('FONTSIZE', (0,1), (-1,-1), 8),
        ]))
        story.append(t)
    else:
        story.append(Paragraph("No Induction employee evaluation data recorded.", sub_style))

    doc.build(story)
    buffer.seek(0)
    return buffer

if "is_admin" not in st.session_state:
    st.session_state.is_admin = False

with st.sidebar:
    st.title("🔴 Pathao")
    st.caption("Rides CX Portal")
    st.divider()
    role = st.radio("Access Level:", ["Agent View", "Admin View"])
    
    if role == "Admin View" and not st.session_state.is_admin:
        pw = st.text_input("Enter Admin Password", type="password")
        if st.button("Authorize"):
            admin_pwd = st.secrets.get("admin_password", "changeme123")
            if pw == admin_pwd:
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

CHANNEL_OPTIONS = ["Inbound Voice", "Live Chat & Social Media", "Report Issue & Email", "Complaint Management", "Campaign Management"]

if is_admin_view:
    admin_tab0, admin_tab_logs, admin_tab1, admin_tab2, admin_tab_view, admin_tab3, admin_tab4, admin_tab5 = st.tabs([
        "📈 Dashboard",
        "📖 Training Logs",
        "👥 Employee Data", # Updated Tab Name
        "📊 Topics & Quiz Editor", 
        "🖥️ Training Viewer", 
        "📅 Calendar Planner", 
        "📝 Evaluation System", 
        "🔁 Refresher Requests"
    ])
    
    # 0. PERFORMANCE DASHBOARD
    with admin_tab0:
        dash_sub1, dash_sub2 = st.tabs(["🔴 Induction Training Dashboard", "📘 Self Training Dashboard"])
        
        with dash_sub1:
            st.header("🔴 Induction Training Performance Dashboard")
            st.caption("This dashboard strictly connects with Employees whose Employment Status is set to 'Induction'.")
            
            batches = db.get_batch_schedules()
            evals = db.get_induction_evaluations()
            df_evals = pd.DataFrame(evals) if evals else pd.DataFrame()

            active_batch = batches[0] if batches else None

            c_met1, c_met2, c_met3, c_met4 = st.columns(4)
            with c_met1:
                st.metric("Active Batch", active_batch['batch_name'] if active_batch else "N/A")
            with c_met2:
                st.metric("Batch Status", active_batch['status'] if active_batch else "N/A")
            with c_met3:
                st.metric("Induction Employees", len(df_evals) if not df_evals.empty else 0)
            with c_met4:
                avg_score = df_evals['final_score'].mean() if not df_evals.empty and 'final_score' in df_evals else 0
                st.metric("Induction Avg Score", f"{avg_score:.1f}%")

            st.divider()

            covered_topics = []
            if active_batch:
                st.markdown(f"### 🗓️ Training Period: **{active_batch['start_date']}** to **{active_batch['end_date']}**")
                sched_items = json.loads(active_batch['schedule_json'])
                for item in sched_items:
                    if item.get("Status") == "Completed" and item.get("Activity / Topic") not in ["DAY OFF", "Topic Session"]:
                        if item.get("Activity / Topic") not in covered_topics:
                            covered_topics.append(item.get("Activity / Topic"))
            
            col_t1, col_t2 = st.columns([1, 2])
            with col_t1:
                st.markdown("<div class='card-box'>", unsafe_allow_html=True)
                st.markdown("### 📚 Topics Covered So Far")
                if covered_topics:
                    for top in covered_topics:
                        st.success(f"✓ {top}")
                else:
                    st.info("No slots marked as 'Completed' yet.")
                st.markdown("</div>", unsafe_allow_html=True)

            with col_t2:
                st.markdown("<div class='card-box'>", unsafe_allow_html=True)
                st.markdown("### 👤 Induction Employee Scoreboard")
                if not df_evals.empty:
                    st.dataframe(df_evals[['empid', 'agent_name', 'quiz1', 'quiz2', 'quiz3', 'assignment', 'mock_call', 'live_comm', 'final_score']], use_container_width=True)
                else:
                    st.info("No Induction Employee evaluation records found in database.")
                st.markdown("</div>", unsafe_allow_html=True)

            st.divider()
            pdf_bytes = generate_pdf_report(active_batch, covered_topics, df_evals)
            st.download_button("📄 Download Live Induction Performance Summary (PDF)", pdf_bytes, "Induction_Summary.pdf", "application/pdf")

        with dash_sub2:
            st.header("📘 Self Training Performance Dashboard")
            st.caption("This dashboard analyzes self-learning engagement and self-quiz scores from logs.")
            
            logs = db.get_self_training_logs()
            df_logs = pd.DataFrame(logs) if logs else pd.DataFrame()

            if df_logs.empty:
                st.info("No Self-Training log data available to build dashboard.")
            else:
                s_col1, s_col2, s_col3, s_col4 = st.columns(4)
                s_col1.metric("Total Self-Training Sessions", len(df_logs))
                s_col2.metric("Unique Participating Employees", df_logs['empid'].nunique())
                
                avg_q_score = df_logs['quiz_score'].mean() if 'quiz_score' in df_logs else 0.0
                s_col3.metric("Avg Self-Quiz Score", f"{avg_q_score:.1f}%")
                s_col4.metric("Top Topic", df_logs['topic_name'].mode()[0] if not df_logs['topic_name'].empty else "N/A")

                st.divider()
                
                sc_left, sc_right = st.columns(2)
                with sc_left:
                    st.markdown("<div class='card-box-info'>", unsafe_allow_html=True)
                    st.markdown("### 📊 Module Popularity (Sessions per Topic)")
                    topic_counts = df_logs['topic_name'].value_counts()
                    st.bar_chart(topic_counts)
                    st.markdown("</div>", unsafe_allow_html=True)

                with sc_right:
                    st.markdown("<div class='card-box-info'>", unsafe_allow_html=True)
                    st.markdown("### 📌 Engagement by Channel")
                    chan_counts = df_logs['channel'].value_counts()
                    st.bar_chart(chan_counts)
                    st.markdown("</div>", unsafe_allow_html=True)

                st.markdown("<div class='card-box'>", unsafe_allow_html=True)
                st.markdown("### 📋 Employee-wise Self Training Summary")
                agent_summary = df_logs.groupby(['empid', 'name']).agg(
                    Total_Sessions=('id', 'count'),
                    Avg_Quiz_Score=('quiz_score', 'mean'),
                    Last_Active=('access_time', 'max')
                ).reset_index()
                st.dataframe(agent_summary, use_container_width=True)
                st.markdown("</div>", unsafe_allow_html=True)

    # 1. SELF TRAINING LOGS
    with admin_tab_logs:
        st.header("📖 Self Training Activity Logs & Quiz Scores")
        logs = db.get_self_training_logs()
        if not logs:
            st.info("No self-training activities logged yet.")
        else:
            df_logs = pd.DataFrame(logs)
            
            st.markdown("<div class='card-box'>", unsafe_allow_html=True)
            st.subheader("📋 Logs Overview")
            st.dataframe(df_logs[['id', 'empid', 'name', 'channel', 'topic_name', 'quiz_score', 'access_time']], use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)

            with st.expander("📝 Update Employee Self-Quiz Score", expanded=False):
                with st.form("update_quiz_score_form"):
                    selected_log_id = st.selectbox("Select Log Entry ID", [l['id'] for l in logs])
                    new_quiz_score = st.number_input("Enter Quiz Score (%)", min_value=0.0, max_value=100.0, step=1.0)
                    if st.form_submit_button("💾 Save Score"):
                        db.update_self_training_score(selected_log_id, new_quiz_score)
                        st.success("Quiz score updated in log successfully!")
                        st.rerun()

            st.download_button("📥 Export Logs (CSV)", df_logs.to_csv(index=False).encode('utf-8'), "Self_Training_Logs.csv", "text/csv")

    # 2. EMPLOYEE DATA (NEW FILE UPLOAD & UPDATED ENTRY FORM)
    with admin_tab1:
        st.header("👥 Employee Data & Employment Status")
        
        # BULK UPLOAD SECTION
        st.markdown("<div class='card-box-info'>", unsafe_allow_html=True)
        st.subheader("📁 Bulk Upload Employee Data (CSV / Excel)")
        st.caption("Upload a file containing: **Name**, **EMP ID**, **Channel**, **Email Address**, **Phone Number** (Optional), **Employee Status**")
        
        up_file = st.file_uploader("Choose CSV or XLSX File", type=["csv", "xlsx"])
        if up_file is not None:
            try:
                if up_file.name.endswith(".csv"):
                    df_emp = pd.read_csv(up_file)
                else:
                    df_emp = pd.read_excel(up_file)
                
                st.write("📊 **Uploaded Data Preview:**")
                st.dataframe(df_emp.head(10), use_container_width=True)
                
                if st.button("🚀 Process & Import Employees"):
                    import_count = 0
                    for _, r in df_emp.iterrows():
                        e_id = str(r.get("EMP ID", r.get("empid", ""))).strip()
                        e_name = str(r.get("Name", r.get("name", ""))).strip()
                        e_email = str(r.get("Email Address", r.get("email", ""))).strip()
                        e_phone = str(r.get("Phone Number", r.get("phone", ""))).strip()
                        e_chan = str(r.get("Channel", r.get("channel", "Inbound Voice"))).strip()
                        e_stat = str(r.get("Employee Status", r.get("employment_status", "Induction"))).strip()
                        
                        if e_id and e_name and e_email:
                            db.upsert_agent(e_id, e_name, e_email, e_phone, e_chan, e_stat)
                            import_count += 1
                            
                    st.success(f"Successfully imported {import_count} employee records!")
                    st.rerun()
            except Exception as ex:
                st.error(f"Error processing file: {ex}")
        st.markdown("</div>", unsafe_allow_html=True)

        # MANUAL ENTRY FORM
        st.markdown("<div class='card-box'>", unsafe_allow_html=True)
        with st.expander("➕ Add / Edit Single Employee Record", expanded=False):
            with st.form("agent_info_form"):
                col1, col2 = st.columns(2)
                ag_id = col1.text_input("EMP ID *")
                ag_name = col2.text_input("Employee Name *")
                
                col3, col4 = st.columns(2)
                ag_email = col3.text_input("Email Address *")
                ag_phone = col4.text_input("Phone Number")
                
                col5, col6 = st.columns(2)
                ag_chan = col5.selectbox("Channel *", CHANNEL_OPTIONS)
                ag_status = col6.selectbox("Employee Status *", ["Induction", "Regular", "Probation"])
                
                if st.form_submit_button("💾 Save Employee"):
                    if not ag_id or not ag_name or not ag_email:
                        st.error("EMP ID, Name, and Email are required!")
                    else:
                        db.upsert_agent(ag_id.strip(), ag_name.strip(), ag_email.strip(), ag_phone.strip(), ag_chan, ag_status)
                        st.success("Employee Record saved successfully!")
                        st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

        # DIRECTORY DISPLAY
        agents = db.get_agents()
        if agents:
            st.subheader("📋 Registered Employee Directory")
            st.dataframe(pd.DataFrame(agents), use_container_width=True)
            for ag in agents:
                c1, c2 = st.columns([4, 1])
                c1.write(f"👤 **{ag['name']}** (`{ag['empid']}`) | Channel: `{ag.get('channel', 'N/A')}` | Status: `{ag.get('employment_status', 'Induction')}`")
                if c2.button(f"🗑️ Delete", key=f"del_ag_{ag['empid']}"):
                    db.delete_agent(ag['empid'])
                    st.rerun()

    # 3. TOPICS & QUIZ EDITOR
    with admin_tab2:
        st.header("📊 Topics, Time & Quiz Form Manager")
        topics_list = db.get_topics()
        for top in topics_list:
            st.markdown("<div class='card-box'>", unsafe_allow_html=True)
            with st.expander(f"⚙️ Edit Module: **{top['name']}**", expanded=False):
                with st.form(f"edit_top_form_{top['id']}"):
                    c1, c2 = st.columns(2)
                    new_time = c1.text_input("Duration *", value=top.get('duration', ''), key=f"time_{top['id']}")
                    new_trainer = c2.text_input("Trainer Name *", value=top.get('trainer_name', 'Md Asikul islam Azman'), key=f"tr_{top['id']}")
                    new_slide = st.text_input("Google Slide Link", value=top.get('slide_url', ''), key=f"slide_{top['id']}")
                    new_form = st.text_input("Quiz Form Link", value=top.get('form_url', ''), key=f"form_{top['id']}")
                    
                    if st.form_submit_button("💾 Update Details"):
                        db.upsert_topic({
                            "id": top['id'], "name": top['name'],
                            "duration": new_time.strip(), "trainer_name": new_trainer.strip(),
                            "slide_url": format_embed_url(new_slide.strip()),
                            "form_url": format_form_url(new_form.strip())
                        })
                        st.success(f"Module '{top['name']}' updated successfully!")
                        st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

    # 4. TRAINING VIEWER
    with admin_tab_view:
        st.header("🖥️ Admin Training Presentation Viewer")
        all_topics_admin = db.get_topics()
        if all_topics_admin:
            topic_names_admin = [t["name"] for t in all_topics_admin]
            selected_topic_name = st.selectbox("🎯 Select Topic to Present:", ["-- Select Topic --"] + topic_names_admin, key="admin_topic_select")
            
            if selected_topic_name != "-- Select Topic --":
                selected_topic_obj = next((t for t in all_topics_admin if t["name"] == selected_topic_name), None)
                if selected_topic_obj:
                    st.divider()
                    st.markdown(f"## 📊 Module: **{selected_topic_obj['name']}**")
                    adm_c1, adm_c2 = st.tabs(["📺 Presentation Slides", "📝 Auto Loaded Quiz"])
                    
                    with adm_c1:
                        embed_slide = format_embed_url(selected_topic_obj.get("slide_url", ""))
                        if embed_slide:
                            st.components.v1.iframe(embed_slide, height=580, scrolling=False)
                        else:
                            st.warning("No Presentation Available.")
                            
                    with adm_c2:
                        embed_form = format_form_url(selected_topic_obj.get("form_url", ""))
                        if embed_form:
                            st.components.v1.iframe(embed_form, height=700, scrolling=True)
                        else:
                            st.info("No Quiz Link Available.")

    # 5. INDUCTION CALENDAR PLANNER
    with admin_tab3:
        st.header("📅 Induction Training Calendar Planner & Editor")
        
        st.markdown("<div class='card-box'>", unsafe_allow_html=True)
        st.subheader("➕ Create New Batch Schedule")
        with st.form("period_select_form"):
            b_col1, b_col2, b_col3 = st.columns([2, 1.5, 1.5])
            batch_title = b_col1.text_input("Batch Name", value="Induction Batch - Rides")
            date_from = b_col2.date_input("Date From", value=date.today())
            date_to = b_col3.date_input("Date To", value=date.today() + timedelta(days=6))
            p_submit = st.form_submit_button("📅 Generate Day-wise Planner")
        st.markdown("</div>", unsafe_allow_html=True)

        if "current_planner" not in st.session_state or p_submit:
            if date_from <= date_to:
                num_days = (date_to - date_from).days + 1
                dates_list = [(date_from + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(num_days)]
                day_slots = {d: [{"type": "Topic Session", "topic": "", "custom": "", "time": "10:00 AM - 01:00 PM", "trainer": "Md Asikul islam Azman", "off": False}] for d in dates_list}
                st.session_state.current_planner = {"batch": batch_title, "from": date_from.strftime("%Y-%m-%d"), "to": date_to.strftime("%Y-%m-%d"), "dates": dates_list, "day_slots": day_slots}

        planner_data = st.session_state.get("current_planner", None)
        if planner_data:
            st.divider()
            topics_db = db.get_topics()
            topic_names = ["-- Select Topic --"] + [t['name'] for t in topics_db]
            full_schedule_output = []

            for idx, d_str in enumerate(planner_data.get("dates", [])):
                dt_obj = date.fromisoformat(d_str)
                day_name = dt_obj.strftime("%A")
                st.markdown(f"### 🗓️ Day {idx+1}: `{d_str}` ({day_name})")
                is_day_off = st.checkbox(f"🔴 Mark Entire Day as DAY OFF", key=f"off_day_{d_str}")
                
                if is_day_off:
                    full_schedule_output.append({"Date": d_str, "Day": day_name, "Activity / Topic": "DAY OFF", "Time Slot": "N/A", "Trainer": "N/A", "Status": "Day Off"})
                else:
                    slots = planner_data.get("day_slots", {}).get(d_str, [])
                    for s_idx, slot in enumerate(slots):
                        c1, c2, c3, c4 = st.columns([1.5, 2, 2, 0.5])
                        st_type = c1.selectbox("Activity Type", ["Topic Session", "Other Task / Exam / Mock Call"], key=f"type_{d_str}_{s_idx}")
                        act_title = c2.selectbox("Select Topic", topic_names, key=f"top_{d_str}_{s_idx}") if st_type == "Topic Session" else c2.text_input("Task Title", value="Mock Call", key=f"cust_{d_str}_{s_idx}")
                        st_time = c3.text_input("Time Slot", value=slot.get("time", "10:00 AM - 01:00 PM"), key=f"time_{d_str}_{s_idx}")
                        st_trainer = c3.text_input("Trainer Name", value=slot.get("trainer", "Md Asikul islam Azman"), key=f"tr_{d_str}_{s_idx}")
                        
                        if c4.button("🗑️", key=f"del_slot_{d_str}_{s_idx}"):
                            planner_data["day_slots"][d_str].pop(s_idx)
                            st.rerun()

                        full_schedule_output.append({"Date": d_str, "Day": day_name, "Activity / Topic": act_title, "Time Slot": st_time, "Trainer": st_trainer, "Status": "In Progress"})

                    if st.button(f"➕ Add Slot for {d_str}", key=f"add_slot_{d_str}"):
                        planner_data["day_slots"][d_str].append({"type": "Topic Session", "topic": "", "custom": "", "time": "02:00 PM - 05:00 PM", "trainer": "Md Asikul islam Azman", "off": False})
                        st.rerun()

            if st.button("🚀 Save & Publish Calendar", type="primary"):
                sched_id = str(uuid.uuid4())
                db.save_batch_schedule(sched_id, planner_data['batch'], planner_data['from'], planner_data['to'], json.dumps(full_schedule_output), "In Progress", full_schedule_output=full_schedule_output)
                st.success("Calendar published and synced successfully!")
                st.rerun()

        st.subheader("📁 Published Calendars & Live Modifier / Editor")
        batches = db.get_batch_schedules()
        for b in batches:
            st.markdown("<div class='card-box'>", unsafe_allow_html=True)
            with st.expander(f"📆 **{b['batch_name']}** ({b['start_date']} to {b['end_date']}) — `Status: {b['status']}`", expanded=True):
                data_list = json.loads(b['schedule_json'])
                edit_history = json.loads(b.get('edit_history_json') or '[]')
                
                has_changed = False
                for i, item in enumerate(data_list):
                    if item.get("Activity / Topic") != "DAY OFF":
                        col1, col2, col3 = st.columns([2, 2, 1.5])
                        col1.write(f"🗓️ `{item['Date']}` ({item['Day']})")
                        col2.write(f"📌 **{item['Activity / Topic']}** ({item['Time Slot']})")
                        curr_status = item.get("Status", "In Progress")
                        new_status = col3.selectbox("Status", ["In Progress", "Completed"], index=1 if curr_status == "Completed" else 0, key=f"status_upd_{b['id']}_{i}")
                        if new_status != curr_status:
                            data_list[i]["Status"] = new_status
                            has_changed = True

                if has_changed:
                    db.update_schedule_json_and_status(b['id'], json.dumps(data_list))
                    st.rerun()

                df_sched = pd.DataFrame(data_list)
                st.dataframe(df_sched, use_container_width=True)

                st.markdown("---")
                st.markdown("#### ✏️ Edit Saved Calendar & Log Changes")
                with st.expander("📝 Modify Calendar Slots & Reason", expanded=False):
                    edited_df = st.data_editor(df_sched, num_rows="dynamic", key=f"editor_{b['id']}")
                    edit_reason = st.text_area("Why are you editing this calendar? *", key=f"reason_{b['id']}")
                    edit_changes = st.text_area("What specific changes were made? *", key=f"changes_{b['id']}")
                    
                    if st.button("💾 Save Edited Calendar", key=f"save_edit_{b['id']}"):
                        if not edit_reason.strip() or not edit_changes.strip():
                            st.error("Please fill out both Reason and Changes description!")
                        else:
                            new_history_entry = {
                                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                "reason": edit_reason.strip(),
                                "changes": edit_changes.strip()
                            }
                            edit_history.append(new_history_entry)
                            updated_json = edited_df.to_json(orient="records")
                            
                            db.update_batch_schedule_full(b['id'], updated_json, json.dumps(edit_history))
                            st.success("Calendar updated and Change Log stored successfully!")
                            st.rerun()

                if edit_history:
                    st.markdown("📜 **Calendar Modification History / Change Logs:**")
                    for h in reversed(edit_history):
                        st.info(f"⏰ **{h['timestamp']}**\n- **Reason:** {h['reason']}\n- **Changes:** {h['changes']}")

                c_d1, c_d2, c_d3 = st.columns(3)
                c_d1.download_button("📥 Download Calendar CSV", df_sched.to_csv(index=False).encode('utf-8'), f"{b['batch_name']}_Calendar.csv", "text/csv", key=f"dl_cal_{b['id']}")
                if b['status'] != "Training Complete":
                    if c_d2.button("🎓 Mark Training Complete", key=f"complete_batch_{b['id']}"):
                        db.update_schedule_json_and_status(b['id'], json.dumps(data_list), status="Training Complete")
                        st.rerun()
                else:
                    c_d2.success("🎉 Batch Completed!")

                if c_d3.button("🗑️ Delete Schedule", key=f"del_b_{b['id']}"):
                    db.delete_batch_schedule(b['id'])
                    st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

    # 6. EMPLOYEE EVALUATION SYSTEM
    with admin_tab4:
        st.header("📝 Employee Evaluation System")
        st.caption("Only Employees with Employment Status = 'Induction' appear in this evaluation list.")
        
        induction_evals = db.get_induction_evaluations()
        if not induction_evals:
            st.info("No Employees currently marked as 'Induction' in Employee Data.")
        else:
            for ev in induction_evals:
                st.markdown("<div class='card-box'>", unsafe_allow_html=True)
                with st.expander(f"👤 Induction Employee: **{ev['agent_name']}** (`{ev['empid']}`)", expanded=True):
                    with st.form(f"eval_form_{ev['empid']}"):
                        c1, c2, c3, c4 = st.columns(4)
                        q1 = c1.number_input("Quiz 1 Score", min_value=0.0, max_value=100.0, value=float(ev['quiz1']), key=f"q1_{ev['empid']}")
                        q2 = c2.number_input("Quiz 2 Score", min_value=0.0, max_value=100.0, value=float(ev['quiz2']), key=f"q2_{ev['empid']}")
                        q3 = c3.number_input("Quiz 3 Score", min_value=0.0, max_value=100.0, value=float(ev['quiz3']), key=f"q3_{ev['empid']}")
                        ass = c4.number_input("Assignment", min_value=0.0, max_value=100.0, value=float(ev['assignment']), key=f"ass_{ev['empid']}")
                        
                        c5, c6, c7 = st.columns(3)
                        mock = c5.number_input("Mock Call Score", min_value=0.0, max_value=100.0, value=float(ev['mock_call']), key=f"mock_{ev['empid']}")
                        live = c6.number_input("Live Communication", min_value=0.0, max_value=100.0, value=float(ev['live_comm']), key=f"live_{ev['empid']}")
                        
                        auto_final = round((q1 + q2 + q3 + ass + mock + live) / 6.0, 2)
                        c7.markdown(f"**Auto Final Score:**\n### `{auto_final}%`")
                        
                        if st.form_submit_button("💾 Save Score"):
                            db.update_evaluation(ev['empid'], q1, q2, q3, ass, mock, live, auto_final)
                            st.success("Score Saved permanently and synced!")
                            st.rerun()
                st.markdown("</div>", unsafe_allow_html=True)

    # 7. REFRESHER REQUESTS MANAGEMENT
    with admin_tab5:
        st.header("🔁 Refresher Training Requests Management")
        all_requests = db.get_refresher_requests()
        if not all_requests:
            st.info("No Refresher Requests found.")
        else:
            for req in all_requests:
                st.markdown("<div class='card-box'>", unsafe_allow_html=True)
                c_info, c_action = st.columns([3, 2])
                with c_info:
                    st.markdown(f"### 👤 Employee: **{req['name']}** (`{req['empid']}`)")
                    st.markdown(f"**Channel:** {req['channel']} | **Topic:** `{req['topic_name']}`")
                    st.markdown(f"🗓️ **Slot:** {req['preferred_slot']}")
                    st.write(f"**Status:** `{req['status']}` | **Training Status:** `{req.get('training_status', 'Pending')}`")

                with c_action:
                    action = st.selectbox("Action", ["Select Action", "Accept Request", "Reject Request"], key=f"act_{req['id']}")
                    
                    if action == "Accept Request":
                        t_stat = st.selectbox("Training Status", ["Pending", "In Progress", "Completed"], key=f"ts_{req['id']}")
                        if st.button("Confirm Accept", key=f"acc_{req['id']}"):
                            db.update_refresher_status(req['id'], "Accepted", "", t_stat)
                            st.rerun()

                    elif action == "Reject Request":
                        reason = st.text_area("Rejection Reason *", key=f"rej_{req['id']}")
                        if st.button("Confirm Reject", key=f"rej_btn_{req['id']}"):
                            if not reason.strip():
                                st.error("Provide a reason for rejection!")
                            else:
                                db.update_refresher_status(req['id'], "Rejected", reason.strip(), "Cancelled")
                                st.rerun()
                st.markdown("</div>", unsafe_allow_html=True)

else:
    # AGENT WORKSPACE PORTAL
    st.header("Agent Self-Service Hub")
    agent_tab1, agent_tab2, agent_tab3 = st.tabs(["📖 Self Training", "🎓 My Certificate", "🔁 Request Refresher Session"])
    
    # 1. SELF TRAINING TAB
    with agent_tab1:
        all_topics = db.get_topics()
        topic_names = [t["name"] for t in all_topics] if all_topics else []

        if "active_self_topic" not in st.session_state:
            st.subheader("📚 Start Self Training Module")
            st.caption("Enter your details and select a topic to open training materials.")
            
            with st.form("self_training_start_form"):
                c1, c2 = st.columns(2)
                s_name = c1.text_input("Employee Name *")
                s_empid = c2.text_input("EMP ID *")
                
                c3, c4 = st.columns(2)
                s_channel = c3.selectbox("Channel *", ["-- Select Channel --"] + CHANNEL_OPTIONS)
                s_topic = c4.selectbox("Select Training Topic *", ["-- Select Topic --"] + topic_names)
                
                if st.form_submit_button("🚀 Start Training"):
                    if not s_name or not s_empid or s_channel == "-- Select Channel --" or s_topic == "-- Select Topic --":
                        st.error("All fields marked with (*) are required!")
                    else:
                        selected_obj = next((t for t in all_topics if t["name"] == s_topic), None)
                        if selected_obj:
                            log_id = str(uuid.uuid4())
                            db.insert_self_training_log(log_id, s_empid.strip(), s_name.strip(), s_channel, s_topic, 0.0)
                            
                            st.session_state.active_self_topic = selected_obj
                            st.session_state.current_agent_empid = s_empid.strip()
                            st.session_state.current_agent_name = s_name.strip()
                            st.rerun()
        else:
            selected_topic = st.session_state.active_self_topic
            
            if st.button("⬅️ Back to Topic Selection"):
                st.session_state.pop("active_self_topic", None)
                st.rerun()

            st.markdown(f"## 📊 Module: **{selected_topic['name']}**")
            st.caption(f"⏱️ Duration: {selected_topic['duration']} | Assigned Trainer: {selected_topic.get('trainer_name', 'Md Asikul islam Azman')}")

            content_tab1, content_tab2 = st.tabs(["📺 Study Presentation", "📝 Auto Loaded Quiz"])
            
            with content_tab1:
                embed_slide = format_embed_url(selected_topic.get("slide_url", ""))
                if embed_slide:
                    st.components.v1.iframe(embed_slide, height=560, scrolling=False)
                else:
                    st.warning("No Slide Presentation available.")
                    
            with content_tab2:
                embed_form = format_form_url(selected_topic.get("form_url", ""))
                if embed_form:
                    st.subheader("📝 Module Assessment Quiz")
                    st.components.v1.iframe(embed_form, height=700, scrolling=True)
                else:
                    st.info("No Quiz Form link added for this topic yet.")

    # 2. MY CERTIFICATE TAB
    with agent_tab2:
        st.subheader("🎓 Download Official Completion Certificate")
        st.caption("Check your final evaluation score and download your Pathao CX Training Certificate.")
        
        cert_empid = st.text_input("Enter your EMP ID", value=st.session_state.get("current_agent_empid", ""))
        
        if st.button("🔍 Verify & Download Certificate"):
            if cert_empid.strip():
                eval_record = db.get_evaluation_by_id(cert_empid.strip())
                if eval_record:
                    score = float(eval_record.get('final_score', 0.0))
                    ag_name = eval_record.get('agent_name', 'Pathao Employee')
                    
                    st.info(f"Employee Name: **{ag_name}** | Final Score: **{score:.2f}%**")
                    
                    if score >= 60.0:
                        st.success("🎉 Congratulations! You have successfully passed the Pathao CX Induction Training.")
                        
                        cert_bytes = cert_generator.generate_certificate(
                            agent_name=ag_name,
                            topic_name="Pathao CX Induction Training Module",
                            score=score,
                            date_str=date.today().strftime("%d %B, %Y")
                        )
                        
                        st.download_button(
                            label="📄 Download Official PDF Certificate",
                            data=cert_bytes,
                            file_name=f"Pathao_Certificate_{cert_empid.strip()}.pdf",
                            mime="application/pdf"
                        )
                    else:
                        st.warning("⚠️ Passing score required for Certificate is 60.0%. Please contact your trainer.")
                else:
                    st.error("No Evaluation record found for this EMP ID in database.")
            else:
                st.error("Please enter a valid EMP ID.")

    # 3. REQUEST REFRESHER SESSION TAB
    with agent_tab3:
        st.subheader("🔁 Request Refresher Training Session")
        st.caption("Request a specialized training session with a trainer.")
        
        topics = db.get_topics()
        t_opts = [t["name"] for t in topics] if topics else []
        
        with st.form("agent_ref_form"):
            c1, c2 = st.columns(2)
            a_name = c1.text_input("Employee Name *")
            a_id = c2.text_input("EMP ID *")
            
            c3, c4 = st.columns(2)
            a_chan = c3.selectbox("Channel *", ["-- Select Channel --"] + CHANNEL_OPTIONS)
            a_topic = c4.selectbox("Topic Name *", ["-- Select Topic --"] + t_opts)
            
            col1, col2 = st.columns(2)
            r_date = col1.date_input("Available Date *", value=date.today())
            r_time = col2.selectbox("Available Time Slot *", ["-- Select Slot --", "10:00 AM - 01:00 PM", "02:00 PM - 05:00 PM", "05:00 PM - 08:00 PM"])
            
            if st.form_submit_button("📩 Submit Request"):
                if not a_name or not a_id or a_chan == "-- Select Channel --" or a_topic == "-- Select Topic --" or r_time == "-- Select Slot --":
                    st.error("All fields marked with (*) are required!")
                else:
                    db.insert_refresher_request({
                        "id": str(uuid.uuid4()), 
                        "empid": a_id.strip(), 
                        "name": a_name.strip(),
                        "channel": a_chan, 
                        "topic_name": a_topic,
                        "preferred_slot": f"{r_date.strftime('%d %b %Y')} ({r_time})"
                    })
                    st.success("Training Request submitted successfully and synced to GSheet!")

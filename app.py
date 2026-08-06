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

st.set_page_config(page_title="Pathao CX Training Portal", page_icon="🔴", layout="wide")

# Custom UI Styling for Modern Dashboard Cards & Visual Update Badges
st.markdown("""
<style>
    .admin-card {
        background-color: #1e212b;
        border: 1px solid #2e3440;
        border-radius: 10px;
        padding: 18px;
        margin-bottom: 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }
    .update-badge {
        background-color: #064e3b;
        color: #34d399;
        border: 1px solid #059669;
        padding: 6px 12px;
        border-radius: 6px;
        font-weight: bold;
        font-size: 0.9rem;
        display: inline-block;
        margin-bottom: 10px;
    }
    .reason-box {
        background-color: #1f2937;
        border-left: 4px solid #3b82f6;
        padding: 10px 14px;
        border-radius: 4px;
        margin-top: 8px;
        margin-bottom: 12px;
    }
</style>
""", unsafe_allow_html=True)

try:
    db.init_db()
except Exception as e:
    st.error(f"Database Initialization Error: {e}")

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
    title_style = ParagraphStyle('TitleStyle', parent=styles['Heading1'], fontSize=18, textColor=colors.HexColor('#D32F2F'), spaceAfter=10)
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

    story.append(Paragraph("<b>Induction Agent Scorecard:</b>", heading_style))
    if not df_evals.empty:
        table_data = [["EMP ID", "Agent Name", "Quiz 1", "Quiz 2", "Quiz 3", "Assign.", "Mock", "Live", "Final Score"]]
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
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#D32F2F')),
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
        story.append(Paragraph("No evaluation data recorded for Induction agents.", sub_style))

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

    st.sidebar.divider()
    if st.sidebar.button("🧪 Test Google Sheet Connection"):
        try:
            db.sync_to_gsheet("Self Training Log", ["TEST_ID", "12345", "Test Agent", "Inbound Voice", "Fare", "2026-08-06", "In Progress", 0.0])
            st.sidebar.success("Test Data Sent Successfully!")
        except Exception as e:
            st.sidebar.error(f"Test Failed: {e}")

is_admin_view = (role == "Admin View" and st.session_state.is_admin)

st.title("Pathao Rides — CX Training Portal")

CHANNEL_OPTIONS = ["Inbound Voice", "Live Chat & Social Media", "Report Issue & Email", "Complaint Management", "Campaign Management"]

if is_admin_view:
    admin_group = st.radio(
        "🗂️ Navigation Groups:",
        ["📈 Dashboards", "⚙️ Operations & Planning", "👥 Employee Management & Logs"],
        horizontal=True
    )
    st.divider()

    # GROUP 1: DASHBOARDS
    if admin_group == "📈 Dashboards":
        dash_type = st.radio("Select Dashboard View:", ["🎓 Induction Performance Dashboard", "📖 Self-Training Performance Dashboard"], horizontal=True)
        
        if dash_type == "🎓 Induction Performance Dashboard":
            st.header("🎓 Induction Training Performance Dashboard")
            st.caption("Connected directly to Induction Batch Evaluations.")
            
            batches = db.get_batch_schedules()
            ind_evals = db.get_induction_evaluations()
            df_ind_evals = pd.DataFrame(ind_evals) if ind_evals else pd.DataFrame()

            active_batch = batches[0] if batches else None

            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Active Batch", active_batch['batch_name'] if active_batch else "N/A")
            c2.metric("Batch Status", active_batch['status'] if active_batch else "N/A")
            c3.metric("Induction Agents", len(df_ind_evals) if not df_ind_evals.empty else 0)
            
            avg_score = df_ind_evals['final_score'].mean() if not df_ind_evals.empty and 'final_score' in df_ind_evals else 0
            c4.metric("Avg Final Score", f"{avg_score:.1f}%")

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
                st.markdown("### 📚 Topics Covered")
                if covered_topics:
                    for top in covered_topics: st.success(f"✓ {top}")
                else: st.info("No slots marked as Completed.")

            with col_t2:
                st.markdown("### 👤 Induction Scoreboard")
                if not df_ind_evals.empty:
                    st.dataframe(df_ind_evals[['empid', 'agent_name', 'channel', 'quiz1', 'quiz2', 'quiz3', 'assignment', 'mock_call', 'live_comm', 'final_score']], width="stretch")
                else:
                    st.info("No agents with Employment Status = 'Induction' found.")

            st.divider()
            pdf_bytes = generate_pdf_report(active_batch, covered_topics, df_ind_evals)
            st.download_button("📄 Download Induction Summary PDF", pdf_bytes, "Induction_Performance_Summary.pdf", "application/pdf")

        elif dash_type == "📖 Self-Training Performance Dashboard":
            st.header("📖 Self-Training Performance Dashboard")
            st.caption("Analytics derived from agent self-learning modules & quizzes.")
            
            logs = db.get_self_training_logs()
            df_logs = pd.DataFrame(logs) if logs else pd.DataFrame()

            if df_logs.empty:
                st.info("No self-training logs available yet.")
            else:
                total_trainings = len(df_logs)
                completed_trainings = len(df_logs[df_logs['status'] == 'Completed'])
                in_progress = len(df_logs[df_logs['status'] == 'In Progress'])
                avg_quiz = df_logs[df_logs['status'] == 'Completed']['quiz_score'].mean() if completed_trainings > 0 else 0.0

                m1, m2, m3, m4 = st.columns(4)
                m1.metric("Total Enrolled", total_trainings)
                m2.metric("Completed Modules", completed_trainings)
                m3.metric("In-Progress Lock", in_progress)
                m4.metric("Avg Quiz Score", f"{avg_quiz:.1f}%")

                st.divider()
                c_chart1, c_chart2 = st.columns(2)
                
                with c_chart1:
                    st.markdown("### 📊 Module Participation")
                    topic_counts = df_logs['topic_name'].value_counts()
                    st.bar_chart(topic_counts)

                with c_chart2:
                    st.markdown("### 🏆 Average Quiz Score by Topic")
                    if completed_trainings > 0:
                        score_by_topic = df_logs[df_logs['status'] == 'Completed'].groupby('topic_name')['quiz_score'].mean()
                        st.line_chart(score_by_topic)
                    else:
                        st.info("No completed quiz score data available for chart.")

    # GROUP 2: OPERATIONS & PLANNING
    elif admin_group == "⚙️ Operations & Planning":
        op_tab1, op_tab2, op_tab3, op_tab4, op_tab5 = st.tabs([
            "📅 Induction Calendar Planner", 
            "📝 Induction Agent Evaluation", 
            "📊 Topics Editor", 
            "🖥️ Training Presentation Viewer", 
            "🎯 Admin Refresher Assignment"
        ])

        with op_tab1:
            st.header("📅 Induction Training Planner & Editor")
            
            # Message check after update rerun
            if st.session_state.get("show_update_success", False):
                st.success("✅ Calendar successfully updated and saved to database!")
                st.session_state.show_update_success = False

            # Check if we are currently editing an existing calendar schedule
            editing_sched_id = st.session_state.get("editing_sched_id", None)
            
            if editing_sched_id:
                st.warning(f"✏️ **Editing Calendar Schedule ID:** `{editing_sched_id}`")
                if st.button("❌ Cancel Edit Mode"):
                    st.session_state.editing_sched_id = None
                    st.session_state.current_planner = None
                    st.rerun()

            if not editing_sched_id:
                with st.form("period_select_form"):
                    b_col1, b_col2, b_col3 = st.columns([2, 1.5, 1.5])
                    batch_title = b_col1.text_input("Batch Name", value="Induction Batch - Rides")
                    date_from = b_col2.date_input("Date From", value=date.today())
                    date_to = b_col3.date_input("Date To", value=date.today() + timedelta(days=6))
                    p_submit = st.form_submit_button("📅 Generate Day Planner")

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

                st.divider()
                
                # Reason Box for Audit Trail
                edit_reason_input = st.text_area("📝 What changed? / Reason for Update *", placeholder="Specify what was edited in this calendar (e.g. Shifted Friday session to Saturday, updated trainer name)", key="edit_reason_field")

                if editing_sched_id:
                    if st.button("💾 Update & Re-Publish Calendar", type="primary"):
                        if not edit_reason_input.strip():
                            st.error("⚠️ Reason for editing is required before updating!")
                        else:
                            db.update_batch_schedule(editing_sched_id, json.dumps(full_schedule_output), "Updated", edit_reason_input.strip(), full_schedule_output)
                            st.toast("✅ Calendar updated successfully!", icon="🎉")
                            st.session_state.show_update_success = True
                            st.session_state.editing_sched_id = None
                            st.session_state.current_planner = None
                            st.rerun()
                else:
                    if st.button("🚀 Save & Publish Calendar", type="primary"):
                        sched_id = str(uuid.uuid4())
                        reason = edit_reason_input.strip() if edit_reason_input.strip() else "Initial Calendar Creation"
                        db.save_batch_schedule(sched_id, planner_data['batch'], planner_data['from'], planner_data['to'], json.dumps(full_schedule_output), "In Progress", edit_reason=reason, full_schedule_output=full_schedule_output)
                        st.toast("✅ New Calendar published successfully!", icon="🚀")
                        st.session_state.current_planner = None
                        st.rerun()

            st.divider()
            st.subheader("📁 Saved Calendars Tracker & Change Logs")
            batches = db.get_batch_schedules()
            
            if not batches:
                st.info("No published calendars found.")
            else:
                for b in batches:
                    is_recently_updated = (b.get('status') == 'Updated')
                    
                    with st.expander(f"📆 **{b['batch_name']}** ({b['start_date']} to {b['end_date']}) — Status: `{b['status']}`"):
                        
                        # Visible Badge Showing Updated Status
                        if is_recently_updated:
                            st.markdown(f"""
                            <div class="update-badge">
                                ✨ UPDATED CALENDAR | Last Modified: {b.get('last_updated', 'N/A')}
                            </div>
                            <div class="reason-box">
                                💬 <b>Change Log / Reason:</b> {b.get('edit_reason', 'No details provided')}
                            </div>
                            """, unsafe_allow_html=True)
                        else:
                            st.caption(f"🕒 Created On: {b.get('last_updated', 'N/A')}")
                            st.caption(f"📝 Initial Note: {b.get('edit_reason', 'N/A')}")
                        
                        data_list = json.loads(b['schedule_json'])
                        df_sched = pd.DataFrame(data_list)
                        st.dataframe(df_sched, width="stretch")

                        col_ed, col_rm = st.columns([1.5, 4])
                        if col_ed.button("✏️ Edit Calendar", key=f"edit_btn_{b['id']}"):
                            st.session_state.editing_sched_id = b['id']
                            
                            dates_in_batch = sorted(list(set([item['Date'] for item in data_list if 'Date' in item])))
                            day_slots = {}
                            for d in dates_in_batch:
                                day_slots[d] = []
                                for item in data_list:
                                    if item.get('Date') == d and item.get('Activity / Topic') != 'DAY OFF':
                                        day_slots[d].append({
                                            "type": "Topic Session",
                                            "topic": item.get('Activity / Topic'),
                                            "custom": item.get('Activity / Topic'),
                                            "time": item.get('Time Slot'),
                                            "trainer": item.get('Trainer'),
                                            "off": False
                                        })
                            
                            st.session_state.current_planner = {
                                "batch": b['batch_name'],
                                "from": b['start_date'],
                                "to": b['end_date'],
                                "dates": dates_in_batch,
                                "day_slots": day_slots
                            }
                            st.rerun()

                        if col_rm.button("🗑️ Delete Schedule", key=f"del_sch_{b['id']}"):
                            db.delete_batch_schedule(b['id'])
                            st.rerun()

        # EVALUATION SYSTEM (Filtered ONLY for Employment Status = Induction)
        with op_tab2:
            st.header("📝 Induction Agent Evaluation System")
            st.caption("Only showing Agents with Employment Status = 'Induction'")
            
            induction_evals = db.get_induction_evaluations()
            
            if not induction_evals:
                st.warning("No agents currently set to 'Induction' status in Agent Directory.")
            else:
                for ev in induction_evals:
                    st.markdown(f"""
                    <div class="admin-card">
                        <h4>👤 Agent: <b>{ev['agent_name']}</b> (<code>{ev['empid']}</code>)</h4>
                        <p>Channel: {ev.get('channel', 'N/A')} | Status: <b>Induction</b></p>
                    </div>
                    """, unsafe_allow_html=True)
                    
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
                            st.success("Score saved successfully!")
                            st.rerun()

        with op_tab3:
            st.header("📊 Module & Topics Manager")
            topics_list = db.get_topics()
            for top in topics_list:
                with st.expander(f"⚙️ Edit Module: **{top['name']}**"):
                    with st.form(f"edit_top_form_{top['id']}"):
                        c1, c2 = st.columns(2)
                        new_time = c1.text_input("Duration *", value=top.get('duration', ''), key=f"edit_dur_{top['id']}")
                        new_trainer = c2.text_input("Trainer Name *", value=top.get('trainer_name', 'Md Asikul islam Azman'), key=f"edit_tr_{top['id']}")
                        new_slide = st.text_input("Google Slide Link", value=top.get('slide_url', ''), key=f"slide_{top['id']}")
                        new_form = st.text_input("Quiz Form Link", value=top.get('form_url', ''), key=f"form_{top['id']}")
                        
                        if st.form_submit_button("💾 Update Details"):
                            db.upsert_topic({
                                "id": top['id'], "name": top['name'],
                                "duration": new_time.strip(), "trainer_name": new_trainer.strip(),
                                "slide_url": format_embed_url(new_slide.strip()),
                                "form_url": format_form_url(new_form.strip())
                            })
                            st.success(f"Topic '{top['name']}' updated!")
                            st.rerun()

        with op_tab4:
            st.header("🖥️ Live Presentation Viewer")
            all_topics_admin = db.get_topics()
            topic_names_admin = [t["name"] for t in all_topics_admin]
            selected_topic_name = st.selectbox("🎯 Select Topic:", ["-- Select Topic --"] + topic_names_admin)
            
            if selected_topic_name != "-- Select Topic --":
                selected_topic_obj = next((t for t in all_topics_admin if t["name"] == selected_topic_name), None)
                if selected_topic_obj:
                    st.markdown(f"## 📊 Module: **{selected_topic_obj['name']}**")
                    embed_slide = format_embed_url(selected_topic_obj.get("slide_url", ""))
                    if embed_slide: st.iframe(embed_slide, height=550)

        with op_tab5:
            st.header("🎯 Assign Refresher Training")
            agents_list = db.get_agents()
            topics_list = db.get_topics()
            agent_names = [f"{ag['name']} ({ag['empid']})" for ag in agents_list]
            topic_names = [t["name"] for t in topics_list]

            with st.form("admin_assign_refresher_form"):
                c1, c2 = st.columns(2)
                selected_agent_str = c1.selectbox("Select Agent *", ["-- Select Agent --"] + agent_names)
                manual_emp_id = c2.text_input("OR Enter EMP ID Manually")
                
                c3, c4 = st.columns(2)
                agent_channel = c3.selectbox("Channel *", ["-- Select Channel --"] + CHANNEL_OPTIONS)
                refresher_topic = c4.selectbox("Select Refresher Topic *", ["-- Select Topic --"] + topic_names)
                
                c5, c6 = st.columns(2)
                assign_date = c5.date_input("Scheduled Date *", value=date.today())
                assign_time = c6.selectbox("Time Slot *", ["-- Select Slot --", "10:00 AM - 01:00 PM", "02:00 PM - 05:00 PM", "05:00 PM - 08:00 PM"])

                if st.form_submit_button("🚀 Assign Refresher"):
                    final_name = selected_agent_str.split(" (")[0] if selected_agent_str != "-- Select Agent --" else "Existing Employee"
                    final_empid = selected_agent_str.split("(")[1].replace(")", "") if selected_agent_str != "-- Select Agent --" else manual_emp_id.strip()

                    if not final_empid or agent_channel == "-- Select Channel --" or refresher_topic == "-- Select Topic --":
                        st.error("Fill required fields!")
                    else:
                        slot_info = f"{assign_date.strftime('%d %b %Y')} ({assign_time})"
                        db.assign_refresher_by_admin(final_empid, final_name, agent_channel, refresher_topic, slot_info)
                        st.success("Refresher Assigned!")
                        st.rerun()

    # GROUP 3: EMPLOYEE & LOGS
    elif admin_group == "👥 Employee Management & Logs":
        emp_tab1, emp_tab2, emp_tab3 = st.tabs(["👥 Agent Directory", "📖 Self Training Logs", "🔁 Refresher Requests"])

        with emp_tab1:
            st.header("👥 Agent Directory & Status Control")
            c_u1, c_u2 = st.columns([1.5, 1])
            with c_u1:
                st.subheader("📤 Bulk Upload Employee Sheet")
                uploaded_file = st.file_uploader("Upload CSV/Excel", type=["csv", "xlsx"])
                if uploaded_file is not None:
                    df_upload = pd.read_csv(uploaded_file) if uploaded_file.name.endswith(".csv") else pd.read_excel(uploaded_file)
                    df_upload.columns = df_upload.columns.str.strip()
                    if st.button("🚀 Import Data"):
                        db.bulk_upsert_agents(df_upload)
                        st.success("Imported successfully!")
                        st.rerun()

            with c_u2:
                st.subheader("➕ Add Single Agent")
                with st.form("add_ag_form"):
                    m_empid = st.text_input("EMP ID *")
                    m_name = st.text_input("Name *")
                    m_email = st.text_input("Email *")
                    m_channel = st.selectbox("Channel *", CHANNEL_OPTIONS)
                    m_status = st.selectbox("Employment Status *", ["Existing", "Induction", "Resigned"])
                    if st.form_submit_button("💾 Save Agent"):
                        db.upsert_agent(m_empid.strip(), m_name.strip(), m_email.strip(), channel=m_channel, employment_status=m_status)
                        st.success("Saved!")
                        st.rerun()

            st.divider()
            agents = db.get_agents()
            for ag in agents:
                st.markdown(f"""
                <div class="admin-card">
                    <b>{ag['empid']}</b> | <b>{ag['name']}</b> ({ag['email']}) | Channel: <code>{ag.get('channel','N/A')}</code> | Current Status: <b>{ag.get('employment_status','Induction')}</b>
                </div>
                """, unsafe_allow_html=True)
                
                c_st, c_del = st.columns([3, 1])
                new_st = c_st.selectbox("Change Status", ["Existing", "Induction", "Resigned"], index=["Existing", "Induction", "Resigned"].index(ag.get('employment_status','Induction')), key=f"st_sel_{ag['empid']}")
                if new_st != ag.get('employment_status'):
                    db.update_agent_status(ag['empid'], new_st)
                    st.rerun()
                if c_del.button("🗑️ Delete Agent", key=f"del_ag_{ag['empid']}"):
                    db.delete_agent(ag['empid'])
                    st.rerun()

        with emp_tab2:
            st.header("📖 Self Training Activity Logs & Quiz Scores")
            logs = db.get_self_training_logs()
            if logs:
                df_logs = pd.DataFrame(logs)
                st.dataframe(df_logs[['empid', 'name', 'channel', 'topic_name', 'access_time', 'status', 'quiz_score']], width="stretch")
            else:
                st.info("No logs available.")

        with emp_tab3:
            st.header("🔁 Refresher Training Requests")
            reqs = db.get_refresher_requests()
            if reqs:
                st.dataframe(pd.DataFrame(reqs), width="stretch")
            else:
                st.info("No Refresher Requests found.")

else:
    # AGENT SERVICE HUB
    st.header("Agent Self-Service Hub")
    agent_tab1, agent_tab2 = st.tabs(["📖 Self Training", "🔁 Request Refresher Session"])
    
    with agent_tab1:
        st.subheader("📖 Self Training Hub")
        all_topics = db.get_topics()
        topic_names = [t["name"] for t in all_topics] if all_topics else []

        if "agent_verified_id" not in st.session_state:
            with st.form("verify_agent_form"):
                st.caption("Enter your Employee details to access self-training modules.")
                v_empid = st.text_input("EMP ID *").strip()
                v_name = st.text_input("Employee Name *").strip()
                v_channel = st.selectbox("Channel *", ["-- Select Channel --"] + CHANNEL_OPTIONS)
                
                if st.form_submit_button("Verify & Access Training"):
                    if not v_empid or not v_name or v_channel == "-- Select Channel --":
                        st.error("Please fill in all required (*) fields!")
                    else:
                        st.session_state.agent_verified_id = v_empid
                        st.session_state.agent_name = v_name
                        st.session_state.agent_channel = v_channel
                        st.rerun()
        else:
            emp_id = st.session_state.agent_verified_id
            emp_name = st.session_state.agent_name
            emp_channel = st.session_state.agent_channel

            c_usr, c_out = st.columns([4, 1])
            c_usr.info(f"👤 Logged in as: **{emp_name}** (`{emp_id}`) | Channel: **{emp_channel}**")
            
            if c_out.button("🚪 Logout"):
                st.session_state.pop("agent_verified_id", None)
                st.session_state.pop("agent_name", None)
                st.session_state.pop("agent_channel", None)
                st.rerun()

            st.divider()

            active_session = db.get_active_agent_training(emp_id)

            if active_session:
                st.warning(f"⚠️ **In-Progress Training Lock:** You have an unfinished training session on **{active_session['topic_name']}**.")
                st.caption("You cannot start a new topic until you complete this training slide and submit the quiz.")

                selected_topic = next((t for t in all_topics if t["name"] == active_session['topic_name']), None)

                if selected_topic:
                    st.markdown(f"## 📊 Module: **{selected_topic['name']}**")
                    
                    step_key = f"step_{active_session['id']}"
                    if step_key not in st.session_state:
                        st.session_state[step_key] = "slides"

                    if st.session_state[step_key] == "slides":
                        st.subheader("Step 1 of 2: Overview All Presentation Slides")
                        embed_slide = format_embed_url(selected_topic.get("slide_url", ""))
                        if embed_slide: st.iframe(embed_slide, height=550)

                        st.markdown("---")
                        if st.button("➡️ I have reviewed all slides, Proceed to Quiz", type="primary"):
                            st.session_state[step_key] = "quiz"
                            st.rerun()

                    elif st.session_state[step_key] == "quiz":
                        st.subheader("Step 2 of 2: Submit Evaluation Quiz & Score")
                        embed_form = format_form_url(selected_topic.get("form_url", ""))
                        if embed_form: st.iframe(embed_form, height=600)

                        st.markdown("---")
                        with st.form("quiz_score_submit_form"):
                            st.caption("Enter your obtained Quiz score (%) to mark completion:")
                            q_score = st.number_input("Quiz Score (%) *", min_value=0.0, max_value=100.0, value=80.0)
                            
                            if st.form_submit_button("✅ Submit Quiz & Complete Training"):
                                db.mark_self_training_complete(active_session['id'], score=q_score)
                                st.success("🎉 Congratulations! Training marked as Completed.")
                                st.session_state.pop(step_key, None)
                                st.rerun()

            else:
                st.subheader("📚 Start New Training Module")
                with st.form("start_new_training_form"):
                    selected_topic_name = st.selectbox("Select Training Topic *", ["-- Select Topic --"] + topic_names)
                    
                    if st.form_submit_button("🚀 Start Training"):
                        if selected_topic_name == "-- Select Topic --":
                            st.error("Please select a topic!")
                        else:
                            log_id = str(uuid.uuid4())
                            db.insert_self_training_log(log_id, emp_id, emp_name, emp_channel, selected_topic_name)
                            st.toast(f"Training started for '{selected_topic_name}'!")
                            st.rerun()

    with agent_tab2:
        st.subheader("🔁 Request Training Session")
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
            
            if st.form_submit_button("📩 Request Training Session"):
                if not a_name or not a_id or a_chan == "-- Select Channel --" or a_topic == "-- Select Topic --":
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
                    st.success("Training Request submitted successfully!")

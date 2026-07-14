import streamlit as st
import pandas as pd
import calendar as cal
import io
import uuid
from datetime import datetime, date

import db

st.set_page_config(page_title="Pathao CX Training Portal", page_icon="🎓", layout="wide")
db.init_db()

# ---------------------------------------------------------------------------
# Small styling touch — keep it light, Streamlit's own theme does most of the
# work. Configure the exact colors in .streamlit/config.toml (included).
# ---------------------------------------------------------------------------
st.markdown("""
<style>
.stamp-badge{
    display:inline-block;border:2px solid #2E7D32;color:#2E7D32;border-radius:50%;
    width:74px;height:74px;text-align:center;line-height:1.1;padding-top:20px;
    font-weight:700;font-size:11px;letter-spacing:.5px;transform:rotate(-6deg);
}
</style>
""", unsafe_allow_html=True)

DOW = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

# ---------------------------------------------------------------------------
# Authentication
#   - Admin: single password gate. Set the real password in Streamlit Cloud
#     under Settings -> Secrets as:  admin_password = "your-password-here"
#     Locally, put the same line in .streamlit/secrets.toml (gitignored).
#   - Agent: identifies with work email + Employee ID (not a password login,
#     since agents don't need accounts — this just tags their record).
# ---------------------------------------------------------------------------
def check_admin_password(pw: str) -> bool:
    real = st.secrets.get("admin_password", "changeme123")
    return pw == real


if "is_admin" not in st.session_state:
    st.session_state.is_admin = False

with st.sidebar:
    st.markdown("### 🎓 CX Training Portal")
    st.caption("Pathao Rides · CMT")
    st.divider()
    role = st.radio("I am a...", ["Agent", "Admin"], index=0)

    if role == "Admin" and not st.session_state.is_admin:
        pw = st.text_input("Admin password", type="password")
        if st.button("Log in"):
            if check_admin_password(pw):
                st.session_state.is_admin = True
                st.rerun()
            else:
                st.error("Incorrect password.")
    elif role == "Admin" and st.session_state.is_admin:
        st.success("Logged in as Admin")
        if st.button("Log out"):
            st.session_state.is_admin = False
            st.rerun()

is_admin_view = (role == "Admin") and st.session_state.is_admin

st.title("Pathao Rides — CX Training Portal")

tab1, tab2 = st.tabs(["📅 Induction Training", "🔁 Refresher Training"])

# ===========================================================================
# TAB 1 — INDUCTION TRAINING
# ===========================================================================
with tab1:
    if "cal_year" not in st.session_state:
        today = date.today()
        st.session_state.cal_year = today.year
        st.session_state.cal_month = today.month

    colA, colB, colC = st.columns([1, 2, 1])
    with colA:
        if st.button("← Previous month"):
            m, y = st.session_state.cal_month - 1, st.session_state.cal_year
            if m == 0:
                m, y = 12, y - 1
            st.session_state.cal_month, st.session_state.cal_year = m, y
    with colC:
        if st.button("Next month →"):
            m, y = st.session_state.cal_month + 1, st.session_state.cal_year
            if m == 13:
                m, y = 1, y + 1
            st.session_state.cal_month, st.session_state.cal_year = m, y
    with colB:
        st.markdown(
            f"<h3 style='text-align:center'>{cal.month_name[st.session_state.cal_month]} {st.session_state.cal_year}</h3>",
            unsafe_allow_html=True,
        )

    year, month = st.session_state.cal_year, st.session_state.cal_month
    entries = db.get_induction_entries()
    entries_by_date = {}
    for e in entries:
        entries_by_date.setdefault(e["date"], []).append(e)

    month_matrix = cal.monthcalendar(year, month)
    header_cols = st.columns(7)
    for i, d in enumerate(DOW):
        header_cols[i].markdown(f"**{d}**")

    if "selected_date" not in st.session_state:
        st.session_state.selected_date = None

    for week in month_matrix:
        row_cols = st.columns(7)
        for i, day_num in enumerate(week):
            with row_cols[i]:
                if day_num == 0:
                    st.write("")
                else:
                    d_str = f"{year}-{month:02d}-{day_num:02d}"
                    has_entry = d_str in entries_by_date
                    label = f"{day_num} 🟢" if has_entry else f"{day_num}"
                    if st.button(label, key=f"day_{d_str}", use_container_width=True):
                        st.session_state.selected_date = d_str

    st.divider()

    if st.session_state.selected_date:
        d_str = st.session_state.selected_date
        day_entries = entries_by_date.get(d_str, [])

        if is_admin_view:
            st.subheader(f"Manage entry — {d_str}")
            existing = day_entries[0] if day_entries else None

            with st.form("induction_form"):
                topic = st.text_input("Topic", value=existing["topic"] if existing else "")
                assignment = st.text_area("Assignment", value=existing["assignment"] if existing else "")
                task = st.text_area("Task", value=existing["task"] if existing else "")
                c1, c2 = st.columns(2)
                trainee_name = c1.text_input("Trainee name", value=existing["trainee_name"] if existing else "")
                trainee_empid = c2.text_input("Trainee EMP ID", value=existing["trainee_empid"] if existing else "")
                score = st.text_input("Score (out of 100)", value=existing["score"] if existing else "")
                notes = st.text_area("Notes", value=existing["notes"] if existing else "")
                uploaded = st.file_uploader("Assignment file (optional — PDF, DOCX, XLSX, image)",
                                             type=["pdf", "docx", "doc", "xlsx", "xls", "png", "jpg", "jpeg"])
                if existing and existing.get("file_name"):
                    st.caption(f"Current file on record: {existing['file_name']}")

                save_col, del_col = st.columns(2)
                submitted = save_col.form_submit_button("💾 Save entry", use_container_width=True)
                deleted = del_col.form_submit_button("🗑️ Delete entry", use_container_width=True) if existing else False

            if submitted:
                if not topic.strip():
                    st.error("Topic is required.")
                else:
                    entry = {
                        "id": existing["id"] if existing else str(uuid.uuid4()),
                        "date": d_str,
                        "topic": topic.strip(),
                        "assignment": assignment.strip(),
                        "task": task.strip(),
                        "trainee_name": trainee_name.strip(),
                        "trainee_empid": trainee_empid.strip(),
                        "score": score.strip(),
                        "notes": notes.strip(),
                        "file_name": uploaded.name if uploaded else None,
                        "file_data": uploaded.getvalue() if uploaded else None,
                    }
                    db.upsert_induction_entry(entry)
                    st.success("Entry saved.")
                    st.rerun()

            if deleted:
                db.delete_induction_entry(existing["id"])
                st.success("Entry deleted.")
                st.session_state.selected_date = None
                st.rerun()

        else:
            st.subheader(f"Training for {d_str}")
            if not day_entries:
                st.info("No training scheduled for this day yet.")
            for e in day_entries:
                st.markdown(f"**{e['topic']}**")
                if e["assignment"]:
                    st.write(f"**Assignment:** {e['assignment']}")
                if e["task"]:
                    st.write(f"**Task:** {e['task']}")
                if e.get("file_name") and e.get("file_data"):
                    st.download_button(
                        f"⬇️ Download {e['file_name']}",
                        data=e["file_data"],
                        file_name=e["file_name"],
                        key=f"dl_{e['id']}",
                    )

    st.divider()
    st.subheader("All induction entries")
    if entries:
        df = pd.DataFrame(entries)[["date", "topic", "trainee_name", "trainee_empid", "score", "notes"]]
        df.columns = ["Date", "Topic", "Trainee", "EMP ID", "Score", "Notes"]
        st.dataframe(df, use_container_width=True, hide_index=True)

        if is_admin_view:
            buf = io.BytesIO()
            with pd.ExcelWriter(buf, engine="openpyxl") as writer:
                df.to_excel(writer, index=False, sheet_name="Induction Training")
            st.download_button(
                "📊 Export to Excel",
                data=buf.getvalue(),
                file_name=f"induction_training_{date.today().isoformat()}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
    else:
        st.caption("No entries added yet.")

# ===========================================================================
# TAB 2 — REFRESHER TRAINING
# ===========================================================================
with tab2:
    if is_admin_view:
        st.subheader("Manage refresher topics")
        with st.form("topic_form", clear_on_submit=True):
            c1, c2 = st.columns([2, 1])
            name = c1.text_input("Topic name")
            minutes = c2.number_input("Est. minutes", min_value=1, value=15)
            description = st.text_area("Description")
            add_topic = st.form_submit_button("+ Add topic")
        if add_topic:
            if not name.strip():
                st.error("Topic name is required.")
            else:
                db.upsert_topic({
                    "id": str(uuid.uuid4()), "name": name.strip(),
                    "description": description.strip(), "minutes": int(minutes),
                })
                st.success("Topic added.")
                st.rerun()

        topics = db.get_topics()
        if topics:
            for t in topics:
                c1, c2, c3 = st.columns([3, 1, 1])
                c1.write(f"**{t['name']}** — {t['description']}")
                c2.write(f"{t['minutes']} min")
                if c3.button("Remove", key=f"del_topic_{t['id']}"):
                    db.delete_topic(t["id"])
                    st.rerun()
        else:
            st.caption("No topics yet — add the first one above.")

        st.divider()
        st.subheader("Completion records")
        records = db.get_records()
        if records:
            rdf = pd.DataFrame(records)[["email", "empid", "topic_name", "completed_at", "duration_min"]]
            rdf.columns = ["Email", "EMP ID", "Topic", "Completed at", "Duration (min)"]
            st.dataframe(rdf, use_container_width=True, hide_index=True)

            buf = io.BytesIO()
            with pd.ExcelWriter(buf, engine="openpyxl") as writer:
                rdf.to_excel(writer, index=False, sheet_name="Refresher Records")
            st.download_button(
                "📊 Export to Excel",
                data=buf.getvalue(),
                file_name=f"refresher_records_{date.today().isoformat()}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        else:
            st.caption("No completions recorded yet.")

    else:
        # ---- Agent self-service flow ----
        if "r_step" not in st.session_state:
            st.session_state.r_step = "form"

        if st.session_state.r_step == "form":
            st.subheader("Start a refresher topic")
            email = st.text_input("Email address", key="r_email")
            empid = st.text_input("Employee ID", key="r_empid")
            st.text_input("Training type", value="Refresher Training", disabled=True)
            if st.button("Continue"):
                if not email.strip() or not empid.strip():
                    st.error("Email and Employee ID are required.")
                else:
                    st.session_state.r_user_email = email.strip()
                    st.session_state.r_user_empid = empid.strip()
                    st.session_state.r_step = "select"
                    st.rerun()

        elif st.session_state.r_step == "select":
            st.caption(f"Signed in as {st.session_state.r_user_email} · {st.session_state.r_user_empid}")
            topics = db.get_topics()
            if not topics:
                st.info("No refresher topics available yet. Ask your admin to add one.")
            else:
                options = {f"{t['name']}  ({t['minutes']} min)": t for t in topics}
                choice = st.radio("Choose a topic", list(options.keys()))
                st.write(options[choice]["description"])
                c1, c2 = st.columns(2)
                if c1.button("← Back"):
                    st.session_state.r_step = "form"
                    st.rerun()
                if c2.button("Start topic ▶️"):
                    st.session_state.r_topic = options[choice]
                    st.session_state.r_started_at = datetime.now()
                    st.session_state.r_step = "active"
                    st.rerun()

        elif st.session_state.r_step == "active":
            t = st.session_state.r_topic
            st.subheader(f"In progress: {t['name']}")
            st.write(t["description"])
            st.caption(f"Started at {st.session_state.r_started_at.strftime('%H:%M:%S')}")
            if st.button("✅ Mark topic as complete"):
                completed_at = datetime.now()
                duration = max(1, int((completed_at - st.session_state.r_started_at).total_seconds() / 60))
                db.insert_record({
                    "id": str(uuid.uuid4()),
                    "email": st.session_state.r_user_email,
                    "empid": st.session_state.r_user_empid,
                    "topic_id": t["id"],
                    "topic_name": t["name"],
                    "started_at": st.session_state.r_started_at.isoformat(),
                    "completed_at": completed_at.isoformat(),
                    "duration_min": duration,
                })
                st.session_state.r_step = "done"
                st.rerun()

        elif st.session_state.r_step == "done":
            st.markdown('<div class="stamp-badge">COMPLETE</div>', unsafe_allow_html=True)
            st.subheader(f"{st.session_state.r_topic['name']} — recorded ✅")
            st.caption(f"Saved for {st.session_state.r_user_email} ({st.session_state.r_user_empid})")
            if st.button("Start another topic"):
                st.session_state.r_step = "select"
                st.rerun()

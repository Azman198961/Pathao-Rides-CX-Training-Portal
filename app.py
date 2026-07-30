import streamlit as st
import pandas as pd
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

# Helper function to convert Google Slide URL to embed URL
def format_embed_url(url):
    if not url:
        return ""
    if "/edit" in url:
        return url.split("/edit")[0] + "/embed"
    elif "/pub" in url:
        return url.split("/pub")[0] + "/embed"
    elif not url.endswith("/embed") and "docs.google.com/presentation" in url:
        return url.rstrip('/') + "/embed"
    return url

# Helper function for Google Form URLs
def format_form_url(url):
    if not url:
        return ""
    if "docs.google.com/forms" in url and not url.endswith("embedded=true"):
        if "?" in url:
            return url + "&embedded=true"
        return url + "?embedded=true"
    return url

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
        "📊 Topic, Slide & Form Manager", 
        "📅 Induction Performance Dashboard", 
        "🔁 Refresher Training"
    ])
    
    # 1. TOPIC & FORM MANAGER
    with admin_tab1:
        st.header("Topic, Google Slides & Quiz Form Manager")
        st.caption("Default 8 topics are already configured. You can update or add quiz form links to them.")
        
        with st.expander("➕ Add / Edit Training Topic & Forms", expanded=False):
            with st.form("new_topic_form"):
                c1, c2, c3 = st.columns([2, 1, 1])
                t_name = c1.text_input("Topic Name *")
                t_duration = c2.text_input("Duration *")
                t_trainer = c3.text_input("Assigned Trainer Name")
                
                slide_url = st.text_input("Google Slides Link *", placeholder="https://docs.google.com/presentation/d/.../edit")
                form_url = st.text_input("Quiz Form Link (Google Form / Typeform)", placeholder="https://docs.google.com/forms/d/e/.../viewform")
                
                if st.form_submit_button("💾 Save Topic"):
                    if not t_name or not slide_url:
                        st.error("Topic Name and Slide URL are required!")
                    else:
                        db.upsert_topic({
                            "id": str(uuid.uuid4()), 
                            "name": t_name.strip(), 
                            "duration": t_duration.strip(),
                            "trainer_name": t_trainer.strip(), 
                            "slide_url": format_embed_url(slide_url.strip()),
                            "form_url": format_form_url(form_url.strip())
                        })
                        st.success("Topic & Form Link Saved Successfully!")
                        st.rerun()

        st.subheader("Current Topics in Database")
        topics_list = db.get_topics()
        for top in topics_list:
            with st.container(border=True):
                col_t1, col_t2 = st.columns([4, 1])
                col_t1.markdown(f"### 📊 {top.get('name')}")
                col_t1.caption(f"⏱️ Duration: {top.get('duration')} | 👤 Trainer: {top.get('trainer_name')}")
                col_t1.caption(f"📺 Slide: {top.get('slide_url')}")
                col_t1.caption(f"📝 Quiz Form: {top.get('form_url') or 'Not Added Yet'}")
                if col_t2.button("🗑️ Delete", key=f"del_{top['id']}"):
                    db.delete_topic(top['id'])
                    st.rerun()

    # 2. INDUCTION DASHBOARD
    with admin_tab2:
        st.header("📊 Induction Training Performance Dashboard")
        raw_data = db.get_induction_activities()
        if not raw_data:
            st.info("No Induction Activity Records Found yet.")
        else:
            df = pd.DataFrame(raw_data)
            st.dataframe(df, use_container_width=True)

    # 3. REFRESHER TRAINING
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
    # AGENT WORKSPACE PORTAL
    st.header("Agent Self-Service Hub")
    agent_tab1, agent_tab2 = st.tabs(["📖 Study Topics & Take Quiz", "🔁 Request Refresher Session"])
    
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
                            <p style="color: #a0a0a0;">👤 Trainer: <b>{topic.get('trainer_name', 'N/A')}</b></p>
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
                    st.caption(f"⏱️ Duration: {selected_topic['duration']} | Assigned Trainer: {selected_topic.get('trainer_name', 'N/A')}")
                    
                    # Nested Tabs for Slide Presentation and Form Embed
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

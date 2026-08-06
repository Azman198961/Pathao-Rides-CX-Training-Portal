# ==========================================
# Dynamic Quiz & Certificate Integration Code
# (Add this logic inside app.py under Self Training Hub)
# ==========================================

import streamlit as st
import datetime
from certificate import generate_certificate

def render_dynamic_quiz(agent_name, topic_name, topic_id):
    st.markdown("### 📝 Module Assessment Quiz")
    
    # Sample dynamic questions (These can also be loaded from db.py)
    questions = [
        {
            "id": 1,
            "question": "পাঠাও সিএক্স পলিসি অনুযায়ী কাস্টমার রিফান্ড রিকোয়েস্ট কত সময়ের মধ্যে প্রসেস করতে হয়?",
            "options": ["২৪ ঘণ্টা", "৪৮ ঘণ্টা", "৭২ ঘণ্টা", "তাৎক্ষণিক"],
            "answer": "২৪ ঘণ্টা"
        },
        {
            "id": 2,
            "question": "কল ট্রান্সফার করার সময় এজেন্টকে প্রথমে কি করতে হবে?",
            "options": ["সরাসরি ট্রান্সফার করা", "কাস্টমারকে হোল্ডে রেখে অনুমতি নেওয়া", "কল কেটে দেওয়া", "সুপারভাইজারকে মেসেজ দেওয়া"],
            "answer": "কাস্টমারকে হোল্ডে রেখে অনুমতি নেওয়া"
        }
    ]
    
    user_answers = {}
    with st.form("quiz_form"):
        for q in questions:
            user_answers[q["id"]] = st.radio(f"**Q{q['id']}. {q['question']}**", q["options"], key=f"q_{q['id']}")
            st.divider()
            
        submitted = st.form_submit_button("Submit Quiz")
        
        if submitted:
            correct_count = sum(1 for q in questions if user_answers[q["id"]] == q["answer"])
            total_questions = len(questions)
            score_percentage = (correct_count / total_questions) * 100
            
            st.write(f"### আপনার প্রাপ্ত স্কোর: **{score_percentage:.1f}%** ({correct_count}/{total_questions})")
            
            if score_percentage >= 80.0:
                st.success("🎉 অভিনন্দন! আপনি সফলভাবে এই মডিউলটি পাস করেছেন।")
                
                # Generate PDF Certificate
                today_str = datetime.date.today().strftime("%d %B, %Y")
                cert_pdf = generate_certificate(agent_name, topic_name, score_percentage, today_str)
                
                st.download_button(
                    label="📜 Download Your Official Certificate (PDF)",
                    data=cert_pdf,
                    file_name=f"Pathao_Certificate_{agent_name.replace(' ', '_')}.pdf",
                    mime="application/pdf"
                )
            else:
                st.error("❌ আপনি পাসিং মার্কস (80%) পাননি। স্লাইডগুলো পুনরায় দেখে আবার চেষ্টা করুন।")

import streamlit as st
import datetime
import pandas as pd
import numpy as np
from PIL import Image
import io
import time

from src.ui.base_layout import style_background_dashboard, style_base_layout
from src.components.header import header_dashboard
from src.components.subject_card import subject_card
from src.components.dialog_create_subject import create_subject_dialog
from src.components.dialog_share_subject import share_subject_dialog

from src.database.db import (
    check_teacher_exists,
    create_teacher,
    teacher_login,
    get_teacher_subject,
    get_subject_enrolled_students,
    record_attendance_session,
    get_subject_attendance_history,
    delete_attendance_session,
    delete_subject
)
from src.pipelines.face_pipeline import predict_attendance
from src.pipelines.voice_pipeline import process_bulk_audio, identify_speaker, get_voice_embedding


def teacher_screen():
    style_background_dashboard()
    style_base_layout()

    if "teacher_data" in st.session_state:
        teacher_dashboard()
    elif 'teacher_login_type' not in st.session_state or st.session_state.teacher_login_type == "login":
        teacher_screen_login()
    elif st.session_state.teacher_login_type == "register":
        teacher_screen_register()


def teacher_dashboard():
    teacher_data = st.session_state.teacher_data
    c1, c2 = st.columns(2, vertical_alignment='center', gap='large')
    with c1:
        header_dashboard()
    with c2:
        st.subheader(f"Welcome, Prof. {teacher_data['name']} 👨‍🏫")
        if st.button("LogOut", type='secondary', key='teacher_logout_btn'):
            st.session_state['is_logged_in'] = False
            if 'teacher_data' in st.session_state:
                del st.session_state.teacher_data
            if 'user_role' in st.session_state:
                del st.session_state.user_role
            st.rerun()

    st.write("")

    if "current_teacher_tab" not in st.session_state:
        st.session_state.current_teacher_tab = 'take_attendance'

    tab1, tab2, tab3 = st.columns(3)

    with tab1:
        type1 = "primary" if st.session_state.current_teacher_tab == 'take_attendance' else "tertiary"
        if st.button('Take Attendance', type=type1, width='stretch', icon=':material/ar_on_you:'):
            st.session_state.current_teacher_tab = 'take_attendance'
            st.rerun()

    with tab2:
        type2 = "primary" if st.session_state.current_teacher_tab == 'manage_subjects' else "tertiary"
        if st.button('Manage Subjects', type=type2, width='stretch', icon=':material/book_ribbon:'):
            st.session_state.current_teacher_tab = 'manage_subjects'
            st.rerun()

    with tab3:
        type3 = "primary" if st.session_state.current_teacher_tab == 'attendance_records' else "tertiary"
        if st.button('Attendance Records', type=type3, width='stretch', icon=":material/stacks:"):
            st.session_state.current_teacher_tab = 'attendance_records'
            st.rerun()

    st.divider()

    if st.session_state.current_teacher_tab == "take_attendance":
        teacher_tab_take_attendance()

    elif st.session_state.current_teacher_tab == "manage_subjects":
        teacher_tab_manage_subjects()

    elif st.session_state.current_teacher_tab == "attendance_records":
        teacher_tab_attendance_records()


def get_current_time_ist():
    try:
        from zoneinfo import ZoneInfo
        return datetime.datetime.now(ZoneInfo("Asia/Kolkata"))
    except Exception:
        tz_ist = datetime.timezone(datetime.timedelta(hours=5, minutes=30))
        return datetime.datetime.now(tz_ist)


# ==========================================
# TAB 1: TAKE AI ATTENDANCE
# ==========================================
def teacher_tab_take_attendance():
    teacher_id = st.session_state.teacher_data['teacher_id']
    subjects = get_teacher_subject(teacher_id)

    if not subjects:
        st.warning("You haven't created any subjects yet. Please create a subject in the 'Manage Subjects' tab first.")
        return

    st.header('📸 Take AI Attendance')
    st.caption("Capture class photo or voice recording to automatically detect students and record attendance.")

    # Select Subject
    subject_options = {f"{s['name']} ({s['subject_code']} - Sec {s['section']})": s for s in subjects}
    selected_label = st.selectbox("Select Subject", list(subject_options.keys()))
    selected_sub = subject_options[selected_label]
    subject_id = selected_sub['subject_id']

    # Fetch Enrolled Students for this subject
    enrolled_students = get_subject_enrolled_students(subject_id)
    enrolled_map = {s['student_id']: s for s in enrolled_students}

    c_info1, c_info2 = st.columns(2)
    with c_info1:
        st.info(f"👥 **Enrolled Students:** {len(enrolled_students)}")
    with c_info2:
        st.info(f"🏛️ **Subject Code:** `{selected_sub['subject_code']}` | Section: `{selected_sub['section']}`")

    if not enrolled_students:
        st.warning(f"No students enrolled in **{selected_sub['name']}** yet. Share the subject code with students to enroll.")
        return

    st.write("")
    
    # Mode selection
    mode = st.radio(
        "Select Attendance Method",
        ["📸 Face Recognition", "🎙️ Voice Recognition", "⚡ Hybrid (Face + Voice)", "📝 Manual Entry"],
        horizontal=True
    )

    detected_student_ids = set()
    ai_status_map = {}

    # Session Date and Time (Defaulted to Indian Standard Time)
    now_ist = get_current_time_ist()
    c_date, c_time = st.columns(2)
    with c_date:
        session_date = st.date_input("Class Date", value=now_ist.date())
    with c_time:
        session_time = st.time_input("Class Time", value=now_ist.time().replace(microsecond=0))

    session_timestamp = f"{session_date} {session_time.strftime('%H:%M:%S')}"

    st.divider()

    # --- Mode 1: Face Recognition ---
    if "Face Recognition" in mode or "Hybrid" in mode:
        st.subheader("📷 Face Detection")
        face_input_type = st.radio("Image Input Source", ["Webcam Capture", "Upload Image File"], horizontal=True, key="face_src_type")
        
        image_data = None
        if face_input_type == "Webcam Capture":
            camera_file = st.camera_input("Take Classroom Snapshot", key="teacher_class_camera")
            if camera_file:
                image_data = camera_file
        else:
            uploaded_img = st.file_uploader("Upload Classroom Image", type=["jpg", "jpeg", "png"], key="teacher_class_upload")
            if uploaded_img:
                image_data = uploaded_img

        if image_data:
            img = np.array(Image.open(image_data))
            with st.spinner("AI is analyzing faces in the photo..."):
                detected, all_ids, num_faces, annotated_img = predict_attendance(img, annotate=True)

            col_img1, col_img2 = st.columns([3, 2])
            with col_img1:
                st.image(annotated_img, caption=f"Analyzed Photo: {num_faces} face(s) found", use_container_width=True)
            with col_img2:
                st.markdown(f"### Detection Summary\n- **Faces Found:** {num_faces}\n- **Recognized Students:** {len(detected)}")
                for sid in detected.keys():
                    if sid in enrolled_map:
                        st.success(f"✅ {enrolled_map[sid]['name']} (Enrolled)")
                        detected_student_ids.add(sid)
                        ai_status_map[sid] = "📸 Face Detected"
                    else:
                        st.info(f"ℹ️ Student ID {sid} (Not enrolled in this subject)")

    # --- Mode 2: Voice Recognition ---
    if "Voice Recognition" in mode or "Hybrid" in mode:
        st.subheader("🎙️ Voice Detection")
        voice_input_type = st.radio("Voice Input Source", ["Live Audio Recording", "Upload Audio File"], horizontal=True, key="voice_src_type")
        
        audio_bytes = None
        if voice_input_type == "Live Audio Recording":
            try:
                rec_audio = st.audio_input("Record Classroom Roll-Call / Phrases", key="teacher_voice_rec")
                if rec_audio:
                    audio_bytes = rec_audio.read()
            except Exception:
                st.info("Audio recording input is ready.")
        else:
            up_audio = st.file_uploader("Upload Classroom Audio Recording", type=["wav", "mp3", "m4a", "ogg"], key="teacher_voice_upload")
            if up_audio:
                audio_bytes = up_audio.read()

        if audio_bytes:
            # Build candidates dictionary from enrolled students with voice embeddings
            candidates = {s['student_id']: s.get('voice_embedding') for s in enrolled_students if s.get('voice_embedding')}

            if not candidates:
                st.warning("None of the enrolled students have enrolled their voice embeddings yet.")
            else:
                with st.spinner("Analyzing voice signatures..."):
                    identified = process_bulk_audio(audio_bytes, candidates, threshold=0.60)
                    
                if identified:
                    st.markdown(f"### Voice Recognition Results ({len(identified)} detected)")
                    for sid, score in identified.items():
                        if sid in enrolled_map:
                            st.success(f"🎙️ **{enrolled_map[sid]['name']}** (Confidence: {int(score * 100)}%)")
                            detected_student_ids.add(sid)
                            ai_status_map[sid] = f"🎙️ Voice Detected ({int(score * 100)}%)" if sid not in ai_status_map else "⚡ Face + Voice"
                else:
                    st.info("No enrolled voice matches found in this audio clip.")

    st.divider()

    # --- Step 4: Interactive Student Checklist ---
    st.subheader("📋 Attendance Roster & Verification")
    st.caption("Review and edit the attendance list before saving.")

    # Initialize session state for subject checkboxes if not initialized or subject switched
    if "current_att_subject" not in st.session_state or st.session_state.current_att_subject != subject_id:
        st.session_state.current_att_subject = subject_id
        st.session_state.ai_status_map = {}
        for s in enrolled_students:
            st.session_state[f"att_check_{s['student_id']}_{subject_id}"] = False

    # If AI detected students in this run, automatically check their box in session state
    if detected_student_ids:
        if "ai_status_map" not in st.session_state:
            st.session_state.ai_status_map = {}
        st.session_state.ai_status_map.update(ai_status_map)
        for sid in detected_student_ids:
            st.session_state[f"att_check_{sid}_{subject_id}"] = True

    # Action buttons
    b1, b2, b3 = st.columns(3)
    with b1:
        if st.button("Mark All Present", type="primary", use_container_width=True):
            for s in enrolled_students:
                st.session_state[f"att_check_{s['student_id']}_{subject_id}"] = True
            st.rerun()
    with b2:
        if st.button("Mark All Absent", type="secondary", use_container_width=True):
            for s in enrolled_students:
                st.session_state[f"att_check_{s['student_id']}_{subject_id}"] = False
            st.rerun()
    with b3:
        if st.button("Invert Selection", type="tertiary", use_container_width=True):
            for s in enrolled_students:
                chk_key = f"att_check_{s['student_id']}_{subject_id}"
                st.session_state[chk_key] = not st.session_state.get(chk_key, False)
            st.rerun()

    # Display Students Roster
    st.write("")
    present_count = 0
    
    for s in enrolled_students:
        sid = s['student_id']
        name = s['name']
        chk_key = f"att_check_{sid}_{subject_id}"
        if chk_key not in st.session_state:
            st.session_state[chk_key] = False

        status_tag = st.session_state.get("ai_status_map", {}).get(sid, "Manual")
        
        c_chk, c_nm, c_st = st.columns([1, 4, 3], vertical_alignment='center')
        with c_chk:
            checked = st.checkbox(
                "Present",
                key=chk_key,
                label_visibility="collapsed"
            )
            if checked:
                present_count += 1
                
        with c_nm:
            st.markdown(f"**{name}** `(ID: {sid})`")
        with c_st:
            if status_tag != "Manual":
                st.badge(status_tag) if hasattr(st, 'badge') else st.markdown(f"`{status_tag}`")
            else:
                st.caption("Manual / Absent")

    st.write("")
    total_enrolled = len(enrolled_students)
    absent_count = total_enrolled - present_count
    st.metric(
        label="Session Summary",
        value=f"{present_count} Present / {total_enrolled} Total",
        delta=f"{absent_count} Absent",
        delta_color="inverse"
    )

    st.write("")
    if st.button("💾 Submit & Save Attendance Session", type="primary", use_container_width=True, icon=":material/check_circle:"):
        records_to_save = []
        for s in enrolled_students:
            sid = s['student_id']
            chk_key = f"att_check_{sid}_{subject_id}"
            is_pres = bool(st.session_state.get(chk_key, False))
            records_to_save.append({
                "student_id": sid,
                "subject_id": subject_id,
                "is_present": is_pres,
                "timestamp": session_timestamp
            })

        try:
            with st.spinner("Saving attendance to database..."):
                record_attendance_session(records_to_save)
            st.balloons()
            st.success(f"🎉 Attendance successfully saved for **{selected_sub['name']}** on {session_timestamp}! (Present: {present_count}, Absent: {absent_count})")
            time.sleep(1.5)
            # Switch to attendance records tab
            st.session_state.current_teacher_tab = "attendance_records"
            st.rerun()
        except Exception as e:
            st.error(f"Error saving attendance: {e}")


# ==========================================
# TAB 2: MANAGE SUBJECTS
# ==========================================
def teacher_tab_manage_subjects():
    teacher_id = st.session_state.teacher_data['teacher_id']
    col1, col2 = st.columns([3, 1], vertical_alignment='center')

    with col1:
        st.header('📚 Manage Subjects')
    with col2:
        if st.button('Create New Subject', type='primary', icon=':material/add:', width='stretch'):
            create_subject_dialog(teacher_id)

    st.divider()

    subjects = get_teacher_subject(teacher_id)
    if subjects:
        cols = st.columns(2)
        for i, sub in enumerate(subjects):
            stats = [
                ("👥", "Students", sub["total_students"]),
                ("🕰️", "Classes", sub["total_classes"])
            ]

            def make_footer(sub_data=sub):
                def footer():
                    c_sh, c_del = st.columns(2)
                    with c_sh:
                        if st.button(f"Share Code", key=f"share_{sub_data['subject_code']}", icon=":material/share:", use_container_width=True):
                            share_subject_dialog(sub_data["name"], sub_data["subject_code"])
                    with c_del:
                        if st.button(f"Delete", key=f"del_{sub_data['subject_code']}", type="secondary", icon=":material/delete:", use_container_width=True):
                            delete_subject(sub_data['subject_id'])
                            st.toast(f"Subject '{sub_data['name']}' deleted!")
                            time.sleep(1)
                            st.rerun()
                return footer

            with cols[i % 2]:
                subject_card(
                    name=sub["name"],
                    code=sub["subject_code"],
                    section=sub["section"],
                    stats=stats,
                    footer_callback=make_footer(sub)
                )
    else:
        st.info("No subjects found. Click **'Create New Subject'** above to get started!")


# ==========================================
# TAB 3: ATTENDANCE RECORDS & ANALYTICS
# ==========================================
def teacher_tab_attendance_records():
    teacher_id = st.session_state.teacher_data['teacher_id']
    subjects = get_teacher_subject(teacher_id)

    if not subjects:
        st.warning("No subjects found. Please create a subject first.")
        return

    st.header('📊 Attendance Records & Analytics')
    st.caption("View attendance statistics, session histories, student summaries, and export reports.")

    # Select Subject
    subject_options = {f"{s['name']} ({s['subject_code']} - Sec {s['section']})": s for s in subjects}
    selected_label = st.selectbox("Select Subject to View Records", list(subject_options.keys()), key="rec_sub_select")
    selected_sub = subject_options[selected_label]
    subject_id = selected_sub['subject_id']

    # Fetch History
    with st.spinner("Fetching attendance records..."):
        logs = get_subject_attendance_history(subject_id)
        enrolled_students = get_subject_enrolled_students(subject_id)

    if not logs:
        st.info(f"No attendance records logged for **{selected_sub['name']}** yet. Take attendance in the 'Take Attendance' tab!")
        return

    # Process logs into data structures
    all_timestamps = sorted(list(set(log['timestamp'] for log in logs if 'timestamp' in log)), reverse=True)
    total_classes = len(all_timestamps)
    total_enrolled = len(enrolled_students)

    # Student Summary Calculation
    student_stats = {}
    for s in enrolled_students:
        student_stats[s['student_id']] = {
            "name": s['name'],
            "attended": 0,
            "total": total_classes
        }

    for log in logs:
        sid = log.get('student_id')
        if sid in student_stats:
            is_pres = log.get('is_present') in (True, 1, 'true', 'True', 't')
            if is_pres:
                student_stats[sid]['attended'] += 1

    # Overall Attendance Rate
    total_presents = sum(1 for log in logs if log.get('is_present') in (True, 1, 'true', 'True', 't'))
    total_expected = len(logs)
    avg_rate = round((total_presents / total_expected * 100), 1) if total_expected > 0 else 0.0

    # Metric Cards
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.metric("Total Classes Held", f"{total_classes} 🗓️")
    with m2:
        st.metric("Enrolled Students", f"{total_enrolled} 👥")
    with m3:
        st.metric("Avg. Attendance Rate", f"{avg_rate}% 📈")
    with m4:
        perfect_count = sum(1 for st_info in student_stats.values() if total_classes > 0 and st_info['attended'] == total_classes)
        st.metric("100% Attendance", f"{perfect_count} 🌟")

    st.write("")

    rec_tab1, rec_tab2, rec_tab3 = st.tabs(["📊 Student Summary", "🗓️ Date-wise Sessions", "📋 Attendance Matrix"])

    # 1. Student Summary Tab
    with rec_tab1:
        st.subheader("Student-wise Attendance Summary")
        summary_rows = []
        for sid, sinfo in student_stats.items():
            pct = round((sinfo['attended'] / sinfo['total'] * 100), 1) if sinfo['total'] > 0 else 0.0
            status = "🟢 Good" if pct >= 75 else ("🟡 Warning" if pct >= 50 else "🔴 Critical")
            summary_rows.append({
                "Student ID": sid,
                "Student Name": sinfo['name'],
                "Classes Attended": sinfo['attended'],
                "Total Classes": sinfo['total'],
                "Attendance %": f"{pct}%",
                "Status": status
            })

        df_summary = pd.DataFrame(summary_rows)
        st.dataframe(df_summary, use_container_width=True, hide_index=True)

    # 2. Date-wise Sessions Tab
    with rec_tab2:
        st.subheader("Class Session Logs")
        
        # Group logs by timestamp
        logs_by_session = {}
        for log in logs:
            ts = log.get('timestamp')
            if ts not in logs_by_session:
                logs_by_session[ts] = []
            logs_by_session[ts].append(log)

        for ts in all_timestamps:
            session_logs = logs_by_session.get(ts, [])
            pres_students = [l['students']['name'] for l in session_logs if l.get('is_present') in (True, 1, 'true', 'True', 't') and l.get('students')]
            abs_students = [l['students']['name'] for l in session_logs if (not l.get('is_present') or l.get('is_present') in (False, 0, 'false', 'False', 'f')) and l.get('students')]
            
            with st.expander(f"🗓️ Session: **{ts}** — Present: {len(pres_students)} / Total: {len(session_logs)}"):
                col_p, col_a, col_d = st.columns([3, 3, 2])
                with col_p:
                    st.markdown("**✅ Present:**")
                    if pres_students:
                        for nm in pres_students:
                            st.write(f"- {nm}")
                    else:
                        st.caption("None")
                with col_a:
                    st.markdown("**❌ Absent:**")
                    if abs_students:
                        for nm in abs_students:
                            st.write(f"- {nm}")
                    else:
                        st.caption("None")
                with col_d:
                    st.write("")
                    if st.button(f"🗑️ Delete Session", key=f"del_sess_{ts}", type="secondary", use_container_width=True):
                        delete_attendance_session(subject_id, ts)
                        st.toast(f"Session on {ts} deleted successfully!")
                        time.sleep(1)
                        st.rerun()

    # 3. Attendance Matrix Tab
    with rec_tab3:
        st.subheader("Attendance Grid Matrix")
        
        matrix_data = []
        for s in enrolled_students:
            row = {"Student Name": s['name']}
            sid = s['student_id']
            
            for ts in all_timestamps:
                matching_log = next((l for l in logs if l.get('student_id') == sid and l.get('timestamp') == ts), None)
                if matching_log:
                    is_p = matching_log.get('is_present') in (True, 1, 'true', 'True', 't')
                    row[ts] = "✅" if is_p else "❌"
                else:
                    row[ts] = "—"
            matrix_data.append(row)

        df_matrix = pd.DataFrame(matrix_data)
        st.dataframe(df_matrix, use_container_width=True, hide_index=True)

    # Export to CSV
    st.divider()
    st.subheader("📥 Export Attendance Report")
    
    if not df_summary.empty:
        csv_buffer = io.StringIO()
        df_summary.to_csv(csv_buffer, index=False)
        csv_bytes = csv_buffer.getvalue().encode('utf-8')
        
        today_ist = get_current_time_ist().date()
        st.download_button(
            label="Download Attendance Summary CSV",
            data=csv_bytes,
            file_name=f"attendance_{selected_sub['subject_code']}_{today_ist}.csv",
            mime="text/csv",
            type="primary",
            icon=":material/download:"
        )


# ==========================================
# AUTHENTICATION: LOGIN & REGISTER
# ==========================================
def login_teacher(username, password):
    if not username or not password:
        return False

    teacher = teacher_login(username, password)
    if teacher:
        st.session_state.user_role = 'teacher'
        st.session_state.teacher_data = teacher
        st.session_state.is_logged_in = True
        return True

    return False


def teacher_screen_login():
    style_background_dashboard()
    style_base_layout()

    c1, c2 = st.columns(2, vertical_alignment='center', gap='large')
    with c1:
        header_dashboard()
    with c2:
        if st.button("Go back to Home", type='secondary', key='loginbackbtn'):
            st.session_state['login_type'] = None
            st.rerun()

    st.header('Teacher Portal — Login')
    st.write("")
    
    teacher_username = st.text_input("Enter Username", placeholder="e.g. ananyaroy")
    teacher_pass = st.text_input("Enter Password", type='password', placeholder="Enter your password")

    st.divider()

    btncl1, btncl2 = st.columns(2)
    with btncl1:
        if st.button('Login', icon=':material/login:', width='stretch', type='primary'):
            if login_teacher(teacher_username, teacher_pass):
                st.toast("Welcome back!", icon="👋")
                time.sleep(1)
                st.rerun()
            else:
                st.error("Invalid username or password combination.")

    with btncl2:
        if st.button('Register New Account', type='secondary', icon=':material/person_add:', width='stretch'):
            st.session_state.teacher_login_type = 'register'
            st.rerun()


def register_teacher(teacher_username, teacher_name, teacher_pass, teacher_pass_confirm):
    if (not teacher_username.strip() or not teacher_name.strip() or not teacher_pass.strip() or not teacher_pass_confirm.strip()):
        return False, "All fields are required!"
    if check_teacher_exists(teacher_username.strip()):
        return False, "Username already taken. Please choose another."
    if teacher_pass != teacher_pass_confirm:
        return False, "Passwords do not match."

    try:
        create_teacher(teacher_username.strip(), teacher_pass, teacher_name.strip())
        return True, "Account successfully created! You can now log in."
    except Exception as e:
        return False, str(e)


def teacher_screen_register():
    style_background_dashboard()
    style_base_layout()

    c1, c2 = st.columns(2, vertical_alignment='center', gap='large')
    with c1:
        header_dashboard()
    with c2:
        if st.button("Go back to Home", type='secondary', key='regbackbtn'):
            st.session_state['login_type'] = None
            st.rerun()

    st.header('Teacher Portal — Register')
    st.write("")

    teacher_username = st.text_input("Choose Username", placeholder="e.g. ananyaroy")
    teacher_name = st.text_input("Full Name", placeholder="e.g. Prof. Ananya Roy")
    teacher_pass = st.text_input("Create Password", type='password', placeholder="Enter password")
    teacher_pass_confirm = st.text_input("Confirm Password", type='password', placeholder="Re-enter password")

    st.divider()

    btncl1, btncl2 = st.columns(2)
    with btncl1:
        if st.button('Register Now', icon=':material/how_to_reg:', width='stretch', type='primary'):
            success, message = register_teacher(teacher_username, teacher_name, teacher_pass, teacher_pass_confirm)
            if success:
                st.success(message)
                time.sleep(1.5)
                st.session_state.teacher_login_type = "login"
                st.rerun()
            else:
                st.error(message)

    with btncl2:
        if st.button('Login Instead', type='secondary', icon=':material/login:', width='stretch'):
            st.session_state.teacher_login_type = 'login'
            st.rerun()

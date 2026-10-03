import streamlit as st
from src.ui.base_layout import style_background_dashboard, style_base_layout
from src.components.header import header_dashboard
from PIL import Image
import numpy as np
from src.pipelines.face_pipeline import predict_attendance, get_face_embeddings, train_classifier
from src.pipelines.voice_pipeline import get_voice_embedding
from src.database.db import get_all_students, create_student, get_student_subjects, get_student_attendance, unenroll_student_to_subject

import time

from src.components.dialog_enroll import enroll_dialog
from src.components.subject_card import subject_card

def student_dashboard():
    student_data = st.session_state.student_data
    student_id = student_data['student_id']
    
    c1, c2 = st.columns(2, vertical_alignment='center', gap='large')
    with c1:
        header_dashboard()
    with c2:
        st.subheader(f"Welcome, {student_data['name']} 👋")
        if st.button("LogOut", type='secondary', key='student_logout_btn'):
            st.session_state['is_logged_in'] = False
            if 'student_data' in st.session_state:
                del st.session_state.student_data
            if 'user_role' in st.session_state:
                del st.session_state.user_role
            st.rerun()

    st.write("")
    
    # Header actions row
    c1, c2 = st.columns([3, 1], vertical_alignment='center')
    with c1:
        st.header('📚 Your Enrolled Subjects')
    with c2:
        if st.button('Enroll in Subject', type='primary', icon=':material/add:', width='stretch'):
            enroll_dialog()

    st.divider()

    with st.spinner('Loading your enrolled subjects..'):
        subjects = get_student_subjects(student_id)
        logs = get_student_attendance(student_id)

    stats_map = {}
    if logs:
        for log in logs:
            sid = log.get('subject_id')
            if not sid:
                continue
            if sid not in stats_map:
                stats_map[sid] = {"total": 0, "attended": 0}
            stats_map[sid]["total"] += 1
            is_p = log.get('is_present') in (True, 1, 'true', 'True', 't')
            if is_p:
                stats_map[sid]["attended"] += 1

    if subjects:
        cols = st.columns(2)
        for i, sub_node in enumerate(subjects):
            sub = sub_node['subjects']
            sid = sub['subject_id']

            stats = stats_map.get(sid, {"total": 0, "attended": 0})
            pct = round((stats['attended'] / stats['total'] * 100), 1) if stats['total'] > 0 else 0.0

            def make_unenroll_btn(subject_id_val=sid, subject_name=sub['name']):
                def unenroll_button():
                    if st.button(f"Unenroll from {subject_name}", key=f"unenroll_{subject_id_val}", type='tertiary', width='stretch'):
                        unenroll_student_to_subject(student_id, subject_id_val)
                        st.toast(f"Unenrolled from {subject_name} successfully!")
                        time.sleep(1)
                        st.rerun()
                return unenroll_button

            with cols[i % 2]:
                subject_card(
                    name=sub['name'],
                    code=sub['subject_code'],
                    section=sub['section'],
                    stats=[
                        ('🗓️', 'Total Classes', stats['total']),
                        ('✅', 'Attended', stats['attended']),
                        ('📊', 'Rate', f"{pct}%")
                    ],
                    footer_callback=make_unenroll_btn(sid, sub['name'])
                )
    else:
        st.info("You are not enrolled in any subjects yet. Click **'Enroll in Subject'** above to enter your teacher's subject code.")

def student_screen():
    style_background_dashboard()
    style_base_layout()

    if "student_data" in st.session_state:
        student_dashboard()
        return
    
    c1, c2 = st.columns(2, vertical_alignment='center', gap='large')
    with c1:
        header_dashboard()
    with c2:
        if st.button("Go back to Home", type='secondary', key='student_home_btn'):
            st.session_state['login_type'] = None
            st.rerun()

    st.header('Login using FaceID')
    st.caption('Position your face clearly in the camera frame to authenticate.')
    st.write("")

    show_registration = False

    photo_source = st.camera_input("Face Authentication Camera")

    if photo_source:
        img = np.array(Image.open(photo_source))

        with st.spinner('AI is scanning facial features..'):
            detected, all_ids, num_faces = predict_attendance(img)

            if num_faces == 0:
                st.warning('No face detected! Please position your face clearly in the frame.')
            elif num_faces > 1:
                st.warning(f'Multiple faces detected ({num_faces}). Please ensure only one person is in frame for login.')
            else:
                if detected:
                    student_id = list(detected.keys())[0]
                    all_students = get_all_students()
                    student = next((s for s in all_students if s['student_id'] == student_id), None)

                    if student:
                        st.session_state.is_logged_in = True
                        st.session_state.user_role = 'student'
                        st.session_state.student_data = student
                        st.toast(f"Welcome back, {student['name']}! 👋")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.warning('Face recognized but student record could not be loaded.')
                else:
                    st.info('Face not recognized! You can register below with this photo.')
                    show_registration = True

    if show_registration and photo_source:
        with st.container(border=True):
            st.header('📝 Register New Student Profile')
            new_name = st.text_input("Enter your Full Name", placeholder='E.g. Akash Sharma')

            st.subheader('🎙️ Optional: Voice Enrollment')
            st.caption("Enroll your voice sample for audio attendance verification.")

            audio_data = None
            try:
                audio_data = st.audio_input('Record a short phrase (e.g., "Present teacher, my name is ...")')
            except Exception:
                st.info('Audio recording is optional.')

            if st.button('Create Account & Sign In', type='primary', icon=':material/how_to_reg:'):
                if new_name.strip():
                    with st.spinner('Analyzing features and creating profile...'):
                        img = np.array(Image.open(photo_source))
                        encodings = get_face_embeddings(img)
                        if encodings:
                            face_emb = encodings[0].tolist()
                            voice_emb = None

                            if audio_data:
                                audio_bytes = audio_data.read()
                                voice_emb = get_voice_embedding(audio_bytes)

                            response_data = create_student(new_name.strip(), face_embedding=face_emb, voice_embedding=voice_emb)

                            if response_data:
                                train_classifier()
                                st.session_state.is_logged_in = True
                                st.session_state.user_role = 'student'
                                st.session_state.student_data = response_data[0]
                                st.toast(f'Profile created! Welcome, {new_name}!')
                                time.sleep(1)
                                st.rerun()
                            else:
                                st.error('Failed to create student record in database. Please try again.')
                        else:
                            st.error('Could not extract facial features from the image. Please try another photo.')
                else:
                    st.warning('Please enter your full name!')

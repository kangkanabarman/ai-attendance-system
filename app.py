import streamlit as st

st.set_page_config(
    page_title="SnapClass - AI Attendance System",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="collapsed"
)

from src.screens.home_screen import home_screen
from src.screens.student_screen import student_screen
from src.screens.teacher_screen import teacher_screen

def main():
    # Handle join_code query param
    
    if "join_code" in st.query_params and 'login_type' not in st.session_state:
        st.session_state['login_type'] = 'student'

    if 'login_type' not in st.session_state:
        st.session_state['login_type'] = None
    
    match st.session_state['login_type']:
        case 'teacher':
            teacher_screen()

        case 'student':
            student_screen()

        case None:
            home_screen()

if __name__ == "__main__":
    main()
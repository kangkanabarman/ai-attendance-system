import streamlit as st

def style_background_home():
    st.markdown("""
        <style>
            .stApp{
                background: #5865F2 !important;
            }

            .stApp div[data-testid="stColumn"]{
                background-color:#E0E3FF !important;
                padding:2.5rem !important;
                border-radius:5rem !important;
            }
        </style>
    """, unsafe_allow_html=True)
    
def style_background_dashboard():
    st.markdown("""
        <style>
            .stApp{
                background: #E0E3FF !important;
            }
        </style>
    """, unsafe_allow_html=True)
    
def style_base_layout():
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Climate+Crisis:YEAR@1979&display=swap');
        @import url('https://fonts.googleapis.com/css2?family=Climate+Crisis:YEAR@1979&family=Outfit:wght@100..900&display=swap');
            
            .block-container{
                padding-top:1.5rem !important;
            }

            h1{
                font-family: 'Climate Crisis', sans-serif !important;
                font-size: 3.5rem !important;
                line-height: 1.1 !important;
                margin-bottom:0rem !important;
            }
            h2{
                font-family: 'Climate Crisis', sans-serif !important;
                font-size: 2rem !important;
                line-height: 0.9 !important;
                margin-bottom:0rem !important;
            }

            h3,h4,p,span{
                font-family: 'Outfit', sans-serif;
            }

            /* ===========================
               ALL BUTTONS
               =========================== */

            .stButton > button {
                border-radius: 1.5rem !important;
                padding: 10px 20px !important;
                border: none !important;
                color: white !important;
                transition: all 0.25s ease !important;
            }

            /* Primary Button (Blue) */
            .stButton > button[data-testid="stBaseButton-primary"] {
                background-color: #5865F2 !important;
                color: white !important;
            }

            /* Secondary Button (Pink) */
            .stButton > button[data-testid="stBaseButton-secondary"] {
                background-color: #EB459E !important;
                color: white !important;
            }

            /* Tertiary Button (Black) */
            .stButton > button[data-testid="stBaseButton-tertiary"] {
                background-color: #000000 !important;
                color: white !important;
            }

            /* Hover */
            .stButton > button:hover {
                transform: scale(1.05);
            }
        </style>
    """, unsafe_allow_html=True)
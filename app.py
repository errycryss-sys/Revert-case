import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import time
from datetime import datetime, timedelta, timezone

# Page Configuration
st.set_page_config(page_title="Agent Case Tracker", page_icon="⏱️", layout="centered")

# Custom CSS for aesthetic & vibrant UI
st.markdown("""
    <style>
    .main { padding: 2rem; }
    .stButton button { 
        width: 100%; 
        border-radius: 10px; 
        font-weight: bold; 
        height: 3em;
    }
    div[data-testid="stForm"] {
        border: 2px solid #f0f2f6;
        border-radius: 15px;
        padding: 20px;
        background-color: #fafafa;
    }
    </style>
""", unsafe_allow_html=True)

# Google Sheets Connection
@st.cache_resource
def init_gspread():
    creds_dict = st.secrets["gcp_service_account"]
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    credentials = Credentials.from_service_account_info(
        creds_dict,
        scopes=scopes
    )
    client = gspread.authorize(credentials)
    return client

try:
    client = init_gspread()
    sheet = client.open("Revert case").sheet1
except Exception as e:
    st.error(f"Failed to connect to Google Sheets: {e}")

# Session State Initialization
if 'tracking' not in st.session_state:
    st.session_state.tracking = False
if 'paused' not in st.session_state:
    st.session_state.paused = False
if 'start_time' not in st.session_state:
    st.session_state.start_time = None
if 'pause_start_time' not in st.session_state:
    st.session_state.pause_start_time = None
if 'total_paused_sec' not in st.session_state:
    st.session_state.total_paused_sec = 0
if 'start_str' not in st.session_state:
    st.session_state.start_str = ""
if 'end_str' not in st.session_state:
    st.session_state.end_str = ""
if 'duration_sec' not in st.session_state:
    st.session_state.duration_sec = 0
if 'completed' not in st.session_state:
    st.session_state.completed = False

st.title("⏱️ Agent Case Tracker")
st.markdown("---")

# Agent Input Form
col1, col2 = st.columns(2)
with col1:
    agent_list = [
        "- Select Your Name -",
        "Adam", "Aina", "Farhana", "Faris", "Hani", 
        "Hidayah", "Kieshan", "Maisarah", "Milah", 
        "Mivan", "Noor", "Venosha"
    ]
    selected_agent = st.selectbox(
        "Agent Name",
        agent_list,
        disabled=st.session_state.tracking or st.session_state.completed
    )
    agent_name = selected_agent if selected_agent != "- Select Your Name -" else ""

with col2:
    case_id = st.text_input("Case ID", placeholder="e.g. 2000", disabled=st.session_state.tracking or st.session_state.completed)

st.markdown("### Controls")

# Buttons Row
col_btn1, col_btn2, col_btn3 = st.columns(3)

with col_btn1:
    if st.button("▶️ START CASE", type="primary", disabled=st.session_state.tracking or st.session_state.completed):
        if not agent_name or not case_id:
            st.warning("⚠️ Please enter Agent Name and Case ID first!")
        else:
            st.session_state.tracking = True
            st.session_state.paused = False
            st.session_state.start_time = time.time()
            st.session_state.total_paused_sec = 0
            my_tz = timezone(timedelta(hours=8))
            st.session_state.start_str = datetime.now(my_tz).strftime("%d/%m/%Y %I:%M %p")
            st.rerun()

with col_btn2:
    if not st.session_state.paused:
        if st.button("⏸️ PAUSE", disabled=not st.session_state.tracking or st.session_state.completed):
            st.session_state.paused = True
            st.session_state.pause_start_time = time.time()
            st.rerun()
    else:
        if st.button("▶️ RESUME", type="primary", disabled=not st.session_state.tracking or st.session_state.completed):
            st.session_state.paused = False
            st.session_state.total_paused_sec += int(time.time() - st.session_state.pause_start_time)
            st.rerun()

with col_btn3:
    if st.button("⏹️ COMPLETE CASE", type="secondary", disabled=not st.session_state.tracking):
        end_time = time.time()
        if st.session_state.paused:
            st.session_state.total_paused_sec += int(end_time - st.session_state.pause_start_time)
            st.session_state.paused = False

        my_tz = timezone(timedelta(hours=8))
        st.session_state.end_str = datetime.now(my_tz).strftime("%d/%m/%Y %I:%M %p")
        
        total_elapsed = int(end_time - st.session_state.start_time)
        st.session_state.duration_sec = max(0, total_elapsed - st.session_state.total_paused_sec)
        
        st.session_state.tracking = False
        st.session_state.completed = True
        st.rerun()

# Status Display
if st.session_state.tracking:
    if st.session_state.paused:
        st.warning(f"⏸️ **Case Paused...** (Started at: {st.session_state.start_str})")
    else:
        st.info(f"⏳ **Tracking Case ID: {case_id}** (Started at: {st.session_state.start_str})")

# Completion Form
if st.session_state.completed:
    st.success("🎉 Case Completed! Please fill in the details below:")
    
    with st.form("submit_form"):
        remark = st.text_area("Remark", placeholder="No Remarks / Standard Handling")
        submit_btn = st.form_submit_button("📤 Submit to Google Sheet", type="primary")
        
        if submit_btn:
            try:
                # Format duration (JAM:MINIT SAHAJA - Tanpa Saat)
                m, _ = divmod(st.session_state.duration_sec, 60)
                h, m = divmod(m, 60)
                formatted_duration = f"{h:02d}:{m:02d}"

                pm, _ = divmod(st.session_state.total_paused_sec, 60)
                ph, pm = divmod(pm, 60)
                formatted_pause = f"{ph:02d}:{pm:02d}"

                row_data = [
                    case_id,
                    agent_name,
                    st.session_state.start_str,
                    st.session_state.end_str,
                    formatted_pause,
                    st.session_state.duration_sec,
                    formatted_duration,
                    "Completed",
                    remark if remark else "No Remarks"
                ]
                
                sheet.append_row(row_data)
                
                # Pop balloons & tunjuk success message
                st.balloons()
                st.success("✅ Saved to Google Sheet successfully!")
                
                # Reset Session State
                st.session_state.tracking = False
                st.session_state.paused = False
                st.session_state.completed = False
                st.session_state.total_paused_sec = 0
                
                # Delay 2 saat supaya belon sempat terbang fully!
                time.sleep(2)
                st.rerun()
                
            except Exception as e:
                st.error(f"Error saving to Google Sheet: {e}")

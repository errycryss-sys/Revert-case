import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import time
from datetime import datetime, timedelta, timezone
import pandas as pd

# Page Configuration
st.set_page_config(page_title="CASE LOG", page_icon="⏱️", layout="centered")

# Custom CSS for EXACT Original Layout, Banner & FULL RED BUTTON
st.markdown("""
    <style>
    /* Header Container - Dark Blue Card */
    .header-box {
        background-color: #2b549a;
        padding: 25px;
        border-radius: 12px;
        text-align: center;
        color: white;
        margin-bottom: 20px;
    }
    .header-box h1 {
        color: white !important;
        font-weight: 800;
        letter-spacing: 1px;
        margin-bottom: 5px;
        font-size: 2rem;
    }
    .header-box p {
        color: #e0e6ed;
        font-size: 14px;
        margin: 0;
    }
    
    /* Global Button Base */
    .stButton button { 
        width: 100% !important; 
        border-radius: 8px !important; 
        font-weight: bold !important; 
        height: 3em !important;
    }

    /* Force RED Submit Button Everywhere */
    div[data-testid="stFormSubmitButton"] > button,
    div.stButton > button[kind="secondary"] {
        background-color: #ff4d4d !important;
        color: white !important;
        border: none !important;
        font-size: 16px !important;
    }
    
    div[data-testid="stFormSubmitButton"] > button:hover,
    div.stButton > button[kind="secondary"]:hover {
        background-color: #ff3333 !important;
        color: white !important;
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
    # GUNAKAN ID SPREADSHEET DAN NAMA TAB YANG TEPAT
    sheet = client.open_by_key("19uOA-ylddWlcgvV92O3OyUEY9ekqHyoGXoF5-rslyIM").worksheet("Case Logs")
    connected = True
except Exception as e:
    connected = False
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

# Original Blue Header Card
st.markdown("""
    <div class="header-box">
        <h1>📁 CASE LOG</h1>
        <p>Start case ➔ Pause (if needed) ➔ Complete case ➔ Log Summary</p>
    </div>
""", unsafe_allow_html=True)

if connected:
    st.success("✅ Connected to Google Sheet!")

# Agent Input Form
col1, col2 = st.columns(2)
with col1:
    agent_list = [
        "- Select Your Name -",
        "Adam", "Aina", "Azwar", "Farhana", "Faris",
        "Hani", "Hidayah", "Jaleel", "Kieshan", "Maisarah",
        "Milah", "Mivan", "Noor", "Syahmi", "Syazana",
        "Venosha"
    ]
    selected_agent = st.selectbox(
        "Agent Name",
        agent_list,
        disabled=st.session_state.tracking or st.session_state.completed
    )
    agent_name = selected_agent if selected_agent != "- Select Your Name -" else ""

with col2:
    case_id = st.text_input("Case ID", placeholder="e.g. 2000", disabled=st.session_state.tracking or st.session_state.completed)

st.markdown("---")

# Controls Section (Start, Pause, Complete)
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
    if st.button("⏹️ COMPLETE CASE", disabled=not st.session_state.tracking):
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

# Completion Details Form (Remarks Only)
if st.session_state.completed:
    # Format Duration tanpa saat (Jam:Minit)
    m, _ = divmod(st.session_state.duration_sec, 60)
    h, m = divmod(m, 60)
    formatted_duration = f"{h:02d}:{m:02d}"

    st.success(f"⏹️ **Case Finished! Total Handling Time: {formatted_duration}**")
    
    remark = st.text_area(
        "Remarks", 
        placeholder="Summarize any delays or issues faced (e.g., Hard to validate evidence / Unclear SOP / Complex case / Waiting for seller response / System lag)..."
    )
    
    # Red Submit Button
    if st.button("🚀 SUBMIT TO SHEET", type="secondary", use_container_width=True):
        try:
            pm, ps = divmod(st.session_state.total_paused_sec, 60)
            ph, pm = divmod(pm, 60)
            formatted_pause = f"{ph:02d}:{pm:02d}:{ps:02d}"

            # Data row ringkas (7 Column)
            row_data = [
                case_id,
                agent_name,
                st.session_state.start_str,
                st.session_state.end_str,
                formatted_pause,
                "Completed",
                remark if remark else "No Remarks"
            ]
            
            sheet.append_row(row_data)
            
            # Show Balloons Animation!
            st.balloons()
            st.success("✅ Saved to Google Sheet successfully!")
            
            # Reset Session State
            st.session_state.tracking = False
            st.session_state.paused = False
            st.session_state.completed = False
            st.session_state.total_paused_sec = 0
            
            # Delay 2.5s for balloons to float before refresh
            time.sleep(2.5)
            st.rerun()
            
        except Exception as e:
            st.error(f"Error saving to Google Sheet: {e}")

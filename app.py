import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import time
from datetime import datetime

# Page Configuration
st.set_page_config(page_title="Agent Case Tracker", page_icon="⏱️", layout="centered")

# Custom CSS for clean UI
st.markdown("""
    <style>
    .main-header {
        background: linear-gradient(135deg, #1e3c72, #2a5298);
        padding: 20px;
        border-radius: 12px;
        color: white;
        text-align: center;
        margin-bottom: 25px;
    }
    </style>
""", unsafe_allow_html=True)

st.markdown("""
    <div style="background-color: #2b5497; padding: 20px; border-radius: 10px; text-align: center; color: white;">
        <h1>⏱️ AGENT REVERT CASE LOG</h1>
        <p>Start case ➔ Complete case ➔ Select Return Reason & Log Summary</p>
    </div>
""", unsafe_allow_html=True)

# Google Sheets Auth using Streamlit Secrets
@st.cache_resource
def get_gspread_client():
    scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
    return gspread.authorize(creds)

try:
    gc = get_gspread_client()
    sh = gc.open_by_key("19uOA-ylddWlcgvV92O3OyUEY9ekqHyoGXoF5-rslyIM")
    worksheet = sh.worksheet("Revert case")
    st.success("✅ Connected to Google Sheet!")
except Exception as e:
    st.error(f"❌ Real Error: {e}")

# Session State Initialization
if "tracking" not in st.session_state:
    st.session_state.tracking = False
if "completed" not in st.session_state:
    st.session_state.completed = False
if "start_time" not in st.session_state:
    st.session_state.start_time = None
if "start_str" not in st.session_state:
    st.session_state.start_str = ""
if "end_str" not in st.session_state:
    st.session_state.end_str = ""
if "formatted_time" not in st.session_state:
    st.session_state.formatted_time = ""
if "duration_sec" not in st.session_state:
    st.session_state.duration_sec = 0

# Agent Input Form
col1, col2 = st.columns(2)
with col1:
    agent_name = st.text_input("Agent Name", placeholder="e.g. Didi", disabled=st.session_state.tracking or st.session_state.completed)
with col2:
    case_id = st.text_input("Case ID", placeholder="e.g. 2000", disabled=st.session_state.tracking or st.session_state.completed)

st.markdown("---")

# Timer Controls
col_btn1, col_btn2 = st.columns(2)

with col_btn1:
    if st.button("▶️ START CASE", type="primary", use_container_width=True, disabled=st.session_state.tracking or st.session_state.completed):
        if not agent_name or not case_id:
            st.warning("⚠️ Please enter Agent Name and Case ID first!")
        else:
            st.session_state.start_time = time.time()
            st.session_state.start_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            st.session_state.tracking = True
            st.rerun()

with col_btn2:
    if st.button("⏹️ COMPLETE CASE", type="secondary", use_container_width=True, disabled=not st.session_state.tracking):
        end_time = time.time()
        st.session_state.end_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        st.session_state.duration_sec = int(end_time - st.session_state.start_time)
        
        minutes, seconds = divmod(st.session_state.duration_sec, 60)
        hours, minutes = divmod(minutes, 60)
        st.session_state.formatted_time = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        
        st.session_state.tracking = False
        st.session_state.completed = True
        st.rerun()

# Timer Status Banner
if st.session_state.tracking:
    st.info(f"🟢 **Timer running for {case_id}...** Started at: {st.session_state.start_str}")

# Post-Case Reason & Submission Form
if st.session_state.completed:
    st.success(f"⏹️ **Case Finished!** Total Handling Time: **{st.session_state.formatted_time}**")
    
    return_reasons = [
        'Select Return Reason...',
        'ITRR',
        'Parcel not delivered',
        'Missing part of the order',
        'Empty/Tampered Parcel',
        'Seller sent wrong item (e.g. wrong size, model)',
        'Damaged item',
        'Outer packaging damaged',
        'Scratch/dents',
        'Spilled liquid/contents',
        'Shattered products',
        'Other types of damage',
        'Product is defective or does not work',
        'Expired Product(s)',
        'Counterfeit product',
        'I want to return item in original / sealed condition'
    ]
    
    selected_reason = st.selectbox("Return Reason*", return_reasons)
    
    delay_remark = st.text_area(
        "Remarks",
        placeholder="Summarize any delays or issues faced (e.g., Hard to validate evidence / Unclear SOP / Complex case / Waiting for seller response / System lag)..."
    )
    
    if st.button("🚀 SUBMIT TO SHEET", type="primary", use_container_width=True):
        if selected_reason == 'Select Return Reason...':
            st.warning("⚠️ Please select a Return Reason before submitting!")
        else:
            final_remark = delay_remark.strip() if delay_remark.strip() else "No Remarks / Standard Handling"
            try:
                worksheet.append_row([
                    case_id, 
                    agent_name, 
                    st.session_state.start_str, 
                    st.session_state.end_str, 
                    st.session_state.duration_sec, 
                    st.session_state.formatted_time, 
                    "Completed", 
                    selected_reason, 
                    final_remark
                ])
                st.balloons()
                st.success("🎉 Case Logged Successfully to Google Sheets!")
                
                # Reset Form
                time.sleep(2)
                st.session_state.completed = False
                st.session_state.start_time = None
                st.rerun()
            except Exception as e:
                st.error(f"❌ Error submitting to Sheet: {e}")

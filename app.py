from google.colab import auth
import gspread
from google.auth import default
import ipywidgets as widgets
from IPython.display import display, HTML, clear_output
import time
from datetime import datetime

# 1. Google Sheets Connection
auth.authenticate_user()
creds, _ = default()
gc = gspread.authorize(creds)

try:
    sh = gc.open("Agent Case Time Tracker")
    worksheet = sh.sheet1
    status_msg = "✅ Connected to Google Sheet!"
except Exception as e:
    status_msg = "❌ Sheet Not Found! Please check the spreadsheet name in Google Drive."

# Global variables
start_time = None
start_str = ""
end_time = None
end_str = ""
duration_sec = 0
formatted_time = ""

# Header UI
display(HTML("""
<div style="background: linear-gradient(135deg, #1e3c72, #2a5298); padding: 18px; border-radius: 12px; color: white; text-align: center; font-family: 'Segoe UI', sans-serif; box-shadow: 0 4px 10px rgba(0,0,0,0.15);">
    <h2 style="margin: 0; color: #ffffff;">⏱️ AGENT CASE TRACKER & ISSUE LOG</h2>
    <p style="margin: 5px 0 0 0; opacity: 0.9;">Start case ➔ Complete case ➔ Select Return Reason & Log Delay Summary</p>
</div>
"""))

# 2. Widgets Definition
agent_input = widgets.Text(placeholder="e.g. Didi", description="Agent Name:", style={'description_width': 'initial'})
case_input = widgets.Text(placeholder="e.g. 2000", description="Case ID:", style={'description_width': 'initial'})

btn_start = widgets.Button(description="▶️ START CASE", button_style='success', layout=widgets.Layout(width='180px', height='40px'))
btn_complete = widgets.Button(description="⏹️ COMPLETE CASE", button_style='warning', disabled=True, layout=widgets.Layout(width='180px', height='40px'))

# Return Reasons List
return_reasons_list = [
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

reason_dropdown = widgets.Dropdown(
    options=return_reasons_list,
    value='Select Return Reason...',
    description='Return Reason:',
    disabled=True,
    style={'description_width': 'initial'},
    layout=widgets.Layout(width='480px')
)

remark_input = widgets.Textarea(
    placeholder="Summarize any delays or issues faced (e.g.,Hard to validate evidence / Unclear SOP / Complex case / Waiting for seller response / System lag)...",
    description="Remarks:",
    disabled=True,
    rows=3,
    style={'description_width': 'initial'},
    layout=widgets.Layout(width='480px')
)

btn_submit = widgets.Button(description="🚀 SUBMIT TO SHEET", button_style='danger', disabled=True, layout=widgets.Layout(width='200px', height='40px'))

output = widgets.Output()

# 3. Logic Handlers
def on_start_clicked(b):
    global start_time, start_str
    if not agent_input.value or not case_input.value:
        with output:
            clear_output()
            print("⚠️ Please enter Agent Name and Case ID first!")
        return
    
    start_time = time.time()
    start_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    agent_input.disabled = True
    case_input.disabled = True
    btn_start.disabled = True
    btn_complete.disabled = False
    
    with output:
        clear_output()
        display(HTML(f"<b style='color: #28a745;'>🟢 Timer running for {case_input.value}... Started at: {start_str}</b>"))

def on_complete_clicked(b):
    global end_time, end_str, duration_sec, formatted_time
    end_time = time.time()
    end_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    duration_sec = int(end_time - start_time)
    minutes, seconds = divmod(duration_sec, 60)
    hours, minutes = divmod(minutes, 60)
    formatted_time = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    
    # Unlock reason & remark inputs
    btn_complete.disabled = True
    reason_dropdown.disabled = False
    remark_input.disabled = False
    btn_submit.disabled = False
    
    with output:
        clear_output()
        display(HTML(f"""
        <div style="background-color: #fff3cd; color: #856404; padding: 12px; border-radius: 8px; font-family: sans-serif;">
            ⏹️ <b>Case Finished!</b> Total Handling Time: <b>{formatted_time}</b>.<br>
            Please select the <b>Return Reason</b> and provide a brief <b>Delay Summary / Remarks</b> below before submitting.
        </div>
        """))

def on_submit_clicked(b):
    if reason_dropdown.value == 'Select Return Reason...':
        with output:
            print("⚠️ Please select a Return Reason before submitting!")
        return

    reason = reason_dropdown.value
    remark = remark_input.value if remark_input.value.strip() != "" else "No Remarks / Standard Handling"

    try:
        worksheet.append_row([case_input.value, agent_input.value, start_str, end_str, duration_sec, formatted_time, "Completed", reason, remark])
        with output:
            clear_output()
            display(HTML(f"""
            <div style="background-color: #d4edda; color: #155724; padding: 15px; border-radius: 8px; margin-top: 10px; font-family: sans-serif;">
                🎉 <b>Case Logged Successfully!</b><br>
                🆔 <b>Case ID:</b> {case_input.value}<br>
                👤 <b>Agent:</b> {agent_input.value}<br>
                ⏱️ <b>Handling Time:</b> {formatted_time}<br>
                📌 <b>Return Reason:</b> {reason}<br>
                📝 <b>Delay Summary / Remarks:</b> {remark}
            </div>
            """))
    except Exception as e:
        with output:
            clear_output()
            print(f"❌ Error submitting to Google Sheets: {e}")

    # Reset Form for next case
    agent_input.disabled = False
    case_input.disabled = False
    case_input.value = ''
    reason_dropdown.value = 'Select Return Reason...'
    reason_dropdown.disabled = True
    remark_input.value = ''
    remark_input.disabled = True
    btn_start.disabled = False
    btn_submit.disabled = True

btn_start.on_click(on_start_clicked)
btn_complete.on_click(on_complete_clicked)
btn_submit.on_click(on_submit_clicked)

# 4. Display Layout
form_box = widgets.VBox([
    widgets.HTML(f"<b>Status:</b> {status_msg}<br><br>"),
    widgets.HBox([agent_input, case_input]),
    widgets.HBox([btn_start, btn_complete]),
    widgets.HTML("<hr>"),
    reason_dropdown,
    remark_input,
    btn_submit,
    output
])

display(form_box)

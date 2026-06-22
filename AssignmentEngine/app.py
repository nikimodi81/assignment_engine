import streamlit as st
import datetime
import pandas as pd
import config
import parsers
import matcher
import servicenow_mock

# Set page configuration for a wider, more premium look
st.set_page_config(
    page_title="ServiceNow AI Auto-Assignment Hub",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom premium styling using CSS
st.markdown("""
<style>
    .main-title {
        font-size: 2.2rem;
        font-weight: 700;
        color: #1E3A8A;
        margin-bottom: 0.5rem;
    }
    .subtitle {
        font-size: 1.1rem;
        color: #4B5563;
        margin-bottom: 2rem;
    }
    .card {
        background-color: #F3F4F6;
        padding: 1.2rem;
        border-radius: 8px;
        border-left: 5px solid #3B82F6;
        margin-bottom: 1rem;
    }
    .reason-box {
        background-color: #EFF6FF;
        padding: 0.8rem 1.2rem;
        border-radius: 6px;
        border-left: 4px solid #60A5FA;
        margin-top: 0.5rem;
        font-size: 0.95rem;
        color: #1E40AF;
    }
    .agent-card {
        padding: 10px;
        background-color: #FAFAFA;
        border: 1px solid #E5E7EB;
        border-radius: 6px;
        margin-bottom: 8px;
    }
</style>
""", unsafe_allow_html=True)

# 1. Initialize Session State
if 'tickets' not in st.session_state:
    st.session_state.tickets = [dict(t) for t in servicenow_mock.MOCK_TICKETS]
if 'queues' not in st.session_state:
    st.session_state.queues = dict(servicenow_mock.MOCK_QUEUES)
if 'logs' not in st.session_state:
    st.session_state.logs = []

# 2. Sidebar Simulation Settings
st.sidebar.image("https://upload.wikimedia.org/wikipedia/commons/thumb/c/c9/JSON_vector_logo.svg/120px-JSON_vector_logo.svg.png", width=60)
st.sidebar.title("AI Assignment Settings")
st.sidebar.markdown("Configure the current simulated timezone details below:")

sim_day = st.sidebar.slider(
    "Day of the Month", 
    min_value=1, 
    max_value=31, 
    value=config.SIMULATION_CURRENT_DAY
)

sim_time_str = st.sidebar.text_input(
    "Current Time (UTC) - HH:MM format", 
    value=config.SIMULATION_CURRENT_TIME_UTC
)

# Parse active in-shift users based on settings
try:
    in_shift_users = parsers.get_in_shift_users(sim_day, sim_time_str)
    in_shift_ids = {u['user_id'] for u in in_shift_users}
except Exception as e:
    st.sidebar.error(f"Time format error. Please enter as HH:MM. Error: {e}")
    in_shift_users = []
    in_shift_ids = set()

# Load team details
team_eligibility = parsers.load_team_eligibility()

# Reset button
if st.sidebar.button("Reset Simulation State"):
    st.session_state.tickets = [dict(t) for t in servicenow_mock.MOCK_TICKETS]
    st.session_state.queues = dict(servicenow_mock.MOCK_QUEUES)
    st.session_state.logs = []
    st.success("State reset successfully!")

# 3. Main Dashboard Header
st.markdown("<div class='main-title'>ServiceNow AI Auto-Assignment Control Center</div>", unsafe_allow_html=True)
st.markdown("<div class='subtitle'>Real-time incident & request routing based on shifts, queues, and AI semantic capability matching</div>", unsafe_allow_html=True)

col_left, col_right = st.columns([3, 2])

# Left Column: Unassigned Tickets Checklist
with col_left:
    st.subheader("📋 Unassigned ServiceNow Tickets")
    
    unassigned = [t for t in st.session_state.tickets if t["assigned_to"] is None]
    
    if not unassigned:
        st.success("All tickets are currently assigned!")
    else:
        st.write("Select tickets to process:")
        
        # Select all checkbox
        select_all = st.checkbox("Select All Tickets", value=False)
        
        selected_ticket_ids = []
        for idx, t in enumerate(unassigned):
            checkbox_state = st.checkbox(
                f"[{t['type']}] {t['sys_id']} - {t['short_description']} (Region: {t['region']}, BP: {t['bp']})", 
                value=select_all,
                key=f"check_{t['sys_id']}"
            )
            if checkbox_state:
                selected_ticket_ids.append(t["sys_id"])
                
        # Assign Action
        if st.button("Assign Selected", type="primary"):
            if not selected_ticket_ids:
                st.warning("Please select at least one ticket to assign.")
            elif not in_shift_users:
                st.error("No team members are currently on shift for the selected date/time. Cannot assign.")
            else:
                assigned_count = 0
                temp_logs = []
                
                # Create a lookup dictionary for shift codes
                in_shift_dict = {u['user_id']: u['shift_code'] for u in in_shift_users}
                
                for t_id in selected_ticket_ids:
                    # Find ticket
                    ticket = next(t for t in st.session_state.tickets if t["sys_id"] == t_id)
                    
                    # 1. Find eligible agents
                    candidates = matcher.find_eligible_agents(ticket, team_eligibility)
                    
                    if not candidates:
                        temp_logs.append({
                            "ticket_id": t_id,
                            "title": ticket['short_description'],
                            "assigned_to": "Unassigned",
                            "reason": "No eligible agents found with matching skills/capabilities for this ticket's Region/BP/Technology."
                        })
                        continue
                        
                    # 2. Filter by shift status
                    in_shift_candidates = []
                    for agent, match_type, score, reason in candidates:
                        if agent['user_id'] in in_shift_ids:
                            # Read queue count from session state
                            queue_count = st.session_state.queues.get(agent['user_id'], 0)
                            in_shift_candidates.append({
                                'agent': agent,
                                'match_type': match_type,
                                'score': score,
                                'reason': reason,
                                'shift_code': in_shift_dict.get(agent['user_id'], "N/A"),
                                'queue_count': queue_count
                            })
                            
                    if not in_shift_candidates:
                        off_shift_names = ", ".join([f"{a['name']} ({a['user_id']})" for a, _, _, _ in candidates])
                        temp_logs.append({
                            "ticket_id": t_id,
                            "title": ticket['short_description'],
                            "assigned_to": "Unassigned",
                            "reason": f"Eligible specialists found ({off_shift_names}) but all are currently OFF shift."
                        })
                        continue
                        
                    # 3. Sort: Least queue count first, highest semantic match score second
                    in_shift_candidates.sort(key=lambda x: (x['queue_count'], -x['score']))
                    
                    selected_cand = in_shift_candidates[0]
                    selected_agent = selected_cand['agent']
                    
                    # Update state
                    ticket["assigned_to"] = selected_agent["user_id"]
                    st.session_state.queues[selected_agent["user_id"]] = st.session_state.queues.get(selected_agent["user_id"], 0) + 1
                    
                    # Format a detailed assignment reasoning
                    detailed_reason = (
                        f"Assigned to {selected_agent['name']} ({selected_agent['user_id']}) because they are "
                        f"currently in shift ({selected_cand['shift_code']}) with the lowest active queue load "
                        f"({selected_cand['queue_count']} tickets). "
                        f"Match details: {selected_cand['reason']}."
                    )
                    
                    temp_logs.append({
                        "ticket_id": t_id,
                        "title": ticket['short_description'],
                        "assigned_to": f"{selected_agent['name']} ({selected_agent['user_id']})",
                        "reason": detailed_reason
                    })
                    assigned_count += 1
                
                # Prepend logs to show newest first
                st.session_state.logs = temp_logs + st.session_state.logs
                st.success(f"Processed assignment request. {assigned_count} tickets successfully assigned!")
                st.rerun()

# Right Column: Shift Status & Queue Sizes
with col_right:
    st.subheader("👥 Shift & Queue Dashboard")
    st.write(f"Active roster status for **UTC {sim_time_str}**:")
    
    # Render active queue load per agent
    for agent in team_eligibility:
        u_id = agent['user_id']
        name = agent['name']
        role = agent['role_type']
        
        is_on = u_id in in_shift_ids
        status_color = "🟢 On Shift" if is_on else "🔴 Off Shift"
        
        q_load = st.session_state.queues.get(u_id, 0)
        
        # Display agent card
        st.markdown(f"""
        <div class="agent-card">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <strong>{name}</strong>
                <span style="font-size:0.85em; font-weight:bold; color:{'green' if is_on else 'gray'}">{status_color}</span>
            </div>
            <div style="font-size:0.9em; color:#6B7280; margin-top:3px;">
                Role: {role} | Tech: {", ".join(agent['technologies'])}
            </div>
            <div style="margin-top:6px;">
                Queue Load: <strong>{q_load}</strong> active tickets
            </div>
        </div>
        """, unsafe_allow_html=True)

# Assignment Log / Reasonings below
st.markdown("---")
st.subheader("📝 Assignment Execution & Reason Logs")

if not st.session_state.logs:
    st.info("No auto-assignments run yet in this session. Select tickets above and click 'Assign'.")
else:
    for log in st.session_state.logs:
        st.markdown(f"### Ticket {log['ticket_id']}: **{log['title']}**")
        st.markdown(f"**Assigned to:** `{log['assigned_to']}`")
        st.markdown(f"<div class='reason-box'>💡 <strong>Reason:</strong> {log['reason']}</div>", unsafe_allow_html=True)
        st.markdown("")

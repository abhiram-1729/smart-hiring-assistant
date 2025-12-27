import streamlit as st
import time
import threading
import plotly.graph_objects as go
import os
from state_manager import StateManager
from realtime_bot import BotService

st.set_page_config(
    page_title="AI Resume Agent",
    page_icon="🤖",
    layout="wide"
)

# Initialize Session State for Bot Thread
if 'bot_thread' not in st.session_state:
    st.session_state.bot_thread = None
if 'stop_event' not in st.session_state:
    st.session_state.stop_event = threading.Event()
if 'bot_running' not in st.session_state:
    st.session_state.bot_running = False

# Sidebar Controls
with st.sidebar:
    st.title("Admin Controls")
    jd_path = st.text_input("JD Path", value="data/jd.txt")
    model_name = st.text_input("Model", value="llama3.2:3b")
    cutoff = st.slider("ATS Cutoff", 0, 100, 70)
    
    col_start, col_stop = st.columns(2)
    
    with col_start:
        if st.button("Start Bot", disabled=st.session_state.bot_running, type="primary"):
            if not st.session_state.bot_running:
                st.session_state.stop_event.clear()
                service = BotService(jd_path, model_name, cutoff, 10) # 10s interval for UI responsiveness
                t = threading.Thread(target=service.run, args=(st.session_state.stop_event,), daemon=True)
                t.start()
                st.session_state.bot_thread = t
                st.session_state.bot_running = True
                st.rerun()

    with col_stop:
        if st.button("Stop Bot", disabled=not st.session_state.bot_running, type="secondary"):
            if st.session_state.bot_running:
                st.session_state.stop_event.set()
                # Wait briefly for thread to detect stop
                time.sleep(1) 
                st.session_state.bot_running = False
                st.rerun()
    
    st.markdown("---")
    
    if st.button("Shutdown App", type="primary"):
        st.session_state.stop_event.set()
        st.warning("Keep the terminal open to restart easily.")
        time.sleep(1)
        os._exit(0)
    
    st.markdown("---")
    if st.session_state.bot_running:
        st.success("Bot is Running")
    else:
        st.warning("Bot is Stopped")

# Custom CSS for modern look
st.markdown("""
<style>
    .metric-card {
        background-color: #1E1E1E;
        padding: 20px;
        border-radius: 10px;
        color: white;
        text-align: center;
    }
    .stMetric > div {
        justify-content: center;
    }
</style>
""", unsafe_allow_html=True)

state_manager = StateManager()

def create_gauge(score):
    fig = go.Figure(go.Indicator(
        mode = "gauge+number",
        value = score,
        domain = {'x': [0, 1], 'y': [0, 1]},
        title = {'text': "ATS Score"},
        gauge = {
            'axis': {'range': [None, 100]},
            'bar': {'color': "#00CC96" if score >= 70 else "#EF553B"},
            'steps': [
                {'range': [0, 50], 'color': "lightgray"},
                {'range': [50, 70], 'color': "gray"},
            ],
        }
    ))
    return fig

# Header
col1, col2 = st.columns([3, 1])
with col1:
    st.title("🤖 Autonomous Hiring Agent")
with col2:
    st.empty() 

# Placeholder for auto-refresh
placeholder = st.empty()

while True:
    state = state_manager.load_state()
    
    with placeholder.container():
        # Top Row: Pulse & Metrics
        status_col, count_col, last_active_col = st.columns(3)
        
        with status_col:
            st.metric("Status", state.get("status", "Unknown"))
            
        with count_col:
            st.metric("Processed Candidates", state.get("processed_count", 0))

        with last_active_col:
            st.metric("Last Updated", time.strftime("%H:%M:%S", time.localtime(state.get("last_updated", 0))))

        st.markdown("---")

        # Main Content: Latest Candidate vs Log
        main_col, side_col = st.columns([2, 1])
        
        with main_col:
            st.subheader("Latest Analysis")
            candidate = state.get("latest_candidate")
            
            if candidate:
                c1, c2 = st.columns([1, 1])
                with c1:
                    st.markdown(f"**Name:** {candidate.get('name')}")
                    st.markdown(f"**Decision:** `{candidate.get('decision')}`")
                    
                    # Chart
                    st.plotly_chart(create_gauge(candidate.get('score', 0)), use_container_width=True, key=f"gauge_{time.time()}")
                
                with c2:
                    st.markdown("**Score Breakdown**")
                    breakdown = candidate.get("breakdown", {})
                    st.write(breakdown)
                    
                    st.markdown("**Skills**")
                    st.markdown(", ".join(candidate.get("skills", [])[:10]))
            else:
                st.info("Waiting for first candidate...")

        with side_col:
            st.subheader("Live Activity Log")
            logs = state.get("activity_log", [])
            for log in reversed(logs[-20:]): # Show more logs
                st.text(log)

    time.sleep(1)

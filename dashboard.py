import streamlit as st
import json
import time
import threading
from pathlib import Path
from state_manager import StateManager
from realtime_bot import BotService
import plotly.graph_objects as go

# Page config
st.set_page_config(
    page_title="Resume Screening Dashboard",
    page_icon="🤖",
    layout="wide"
)

# Initialize state manager
state_mgr = StateManager()

# Session state for bot thread
if 'bot_thread' not in st.session_state:
    st.session_state.bot_thread = None
if 'bot_service' not in st.session_state:
    st.session_state.bot_service = None

# Title
st.title("🤖 AI Resume Screening Dashboard")

# Sidebar controls
with st.sidebar:
    st.header("Bot Controls")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("▶️ Start Bot", use_container_width=True):
            if st.session_state.bot_thread is None or not st.session_state.bot_thread.is_alive():
                # Initialize bot service with parameters
                st.session_state.bot_service = BotService(
                    jd_path="data/jd.txt",
                    model="llama3.2:3b",
                    cutoff=70,
                    interval=10
                )
                st.session_state.stop_event = threading.Event()
                st.session_state.bot_thread = threading.Thread(
                    target=st.session_state.bot_service.run,
                    args=(st.session_state.stop_event,),
                    daemon=True
                )
                st.session_state.bot_thread.start()
                st.success("Bot started!")
            else:
                st.warning("Bot is already running")
    
    with col2:
        if st.button("⏸️ Stop Bot", use_container_width=True):
            if st.session_state.bot_service and hasattr(st.session_state, 'stop_event'):
                st.session_state.stop_event.set()
                st.session_state.bot_thread = None
                st.session_state.bot_service = None
                st.info("Bot stopped")
            else:
                st.warning("Bot is not running")
    
    st.divider()
    
    # Bot status
    if st.session_state.bot_thread and st.session_state.bot_thread.is_alive():
        st.success("🟢 Bot Status: Running")
    else:
        st.error("🔴 Bot Status: Stopped")
    
    st.divider()
    
    if st.button("🔄 Shutdown App", use_container_width=True):
        if st.session_state.bot_service and hasattr(st.session_state, 'stop_event'):
            st.session_state.stop_event.set()
        st.stop()

# Auto-refresh
st_autorefresh = st.empty()
with st_autorefresh:
    time.sleep(2)
    st.rerun()

# Load state
state = state_mgr.load_state()

# Metrics
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Total Processed", state.get("total_processed", 0))

with col2:
    st.metric("Proceeded", state.get("proceeded", 0), delta_color="normal")

with col3:
    st.metric("Rejected", state.get("rejected", 0), delta_color="inverse")

with col4:
    avg_score = state.get("average_score", 0)
    st.metric("Avg Score", f"{avg_score:.1f}")

st.divider()

# Two column layout
col_left, col_right = st.columns([1, 1])

with col_left:
    st.subheader("📋 Recent Logs")
    logs = state.get("logs", [])
    
    if logs:
        # Show last 10 logs
        for log in logs[-10:]:
            timestamp = log.get("timestamp", "")
            message = log.get("message", "")
            level = log.get("level", "INFO")
            
            if level == "ERROR":
                st.error(f"[{timestamp}] {message}")
            elif level == "WARNING":
                st.warning(f"[{timestamp}] {message}")
            elif level == "SUCCESS":
                st.success(f"[{timestamp}] {message}")
            else:
                st.info(f"[{timestamp}] {message}")
    else:
        st.info("No logs yet. Start the bot to begin processing.")

with col_right:
    st.subheader("👥 Recent Candidates")
    candidates = state.get("candidates", [])
    
    if candidates:
        for candidate in candidates[-5:]:
            with st.expander(f"📧 {candidate.get('name', 'Unknown')} - Score: {candidate.get('score', 0):.1f}"):
                st.write(f"**Email:** {candidate.get('email', 'N/A')}")
                st.write(f"**Experience:** {candidate.get('experience', 0)} years")
                st.write(f"**Decision:** {candidate.get('decision', 'N/A')}")
                
                # Score breakdown
                breakdown = candidate.get('breakdown', {})
                if breakdown:
                    st.write("**Score Breakdown:**")
                    fig = go.Figure(data=[
                        go.Bar(
                            x=['Skills', 'Experience', 'Keywords', 'Education'],
                            y=[
                                breakdown.get('skill_score', 0),
                                breakdown.get('experience_score', 0),
                                breakdown.get('keyword_score', 0),
                                breakdown.get('education_score', 0)
                            ],
                            marker_color=['#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A']
                        )
                    ])
                    fig.update_layout(
                        height=250,
                        margin=dict(l=0, r=0, t=0, b=0),
                        yaxis_range=[0, 100]
                    )
                    st.plotly_chart(fig, use_container_width=True, key=f"chart_{candidate.get('email', '')}")
                
                # Skills
                skills = candidate.get('skills', [])
                if skills:
                    st.write(f"**Skills:** {', '.join(skills[:10])}")
    else:
        st.info("No candidates processed yet.")

st.divider()

# Footer
st.caption("🤖 Powered by Ollama (Llama 3.2) | Built with Streamlit")

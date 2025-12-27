import json
import time
import os
from typing import Dict, Any, List

STATE_FILE = "dashboard_state.json"

class StateManager:
    def __init__(self):
        self.state_file = STATE_FILE
        self._ensure_file()

    def _ensure_file(self):
        if not os.path.exists(self.state_file):
            initial_state = {
                "status": "Initializing...",
                "last_updated": time.time(),
                "processed_count": 0,
                "latest_candidate": None,  # {name, score, decision, skills...}
                "activity_log": []
            }
            self.save_state(initial_state)

    def load_state(self) -> Dict[str, Any]:
        try:
            with open(self.state_file, 'r') as f:
                return json.load(f)
        except Exception:
            self._ensure_file()
            return self.load_state()

    def save_state(self, state: Dict[str, Any]):
        state["last_updated"] = time.time()
        # Keep log size manageable
        if "activity_log" in state:
            state["activity_log"] = state["activity_log"][-50:]
            
        with open(self.state_file, 'w') as f:
            json.dump(state, f, indent=2)

    def update_status(self, status: str):
        state = self.load_state()
        state["status"] = status
        self.save_state(state)

    def log_activity(self, message: str):
        state = self.load_state()
        timestamp = time.strftime("%H:%M:%S")
        state["activity_log"].append(f"[{timestamp}] {message}")
        self.save_state(state)

    def update_candidate(self, candidate_data: Dict[str, Any]):
        state = self.load_state()
        state["processed_count"] = state.get("processed_count", 0) + 1
        state["latest_candidate"] = candidate_data
        self.save_state(state)

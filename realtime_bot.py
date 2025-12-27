import time
import argparse
import sys
import os
import threading
from termcolor import colored
from gmail_client import GmailClient
from agent import HiringAgent
from llm_client import LLMClient
from state_manager import StateManager

class BotService:
    def __init__(self, jd_path: str, model: str, cutoff: int, interval: int):
        self.jd_path = jd_path
        self.model = model
        self.cutoff = cutoff
        self.interval = interval
        self.state = StateManager()

    def run(self, stop_event: threading.Event):
        """
        Main loop designed to run in a thread.
        Checks stop_event.is_set() to exit.
        """
        self.state.update_status("Starting up...")

        # Load resources
        try:
            with open(self.jd_path, 'r') as f:
                jd_text = f.read()
        except Exception as e:
            print(f"Error reading JD file: {e}")
            self.state.update_status(f"Error: {e}")
            return

        print(colored(f"--- Starting Resume Agent Bot ---", "green"))
        
        # Initialize Clients
        try:
            gmail = GmailClient() 
            llm = LLMClient(model_name=self.model)
            agent = HiringAgent(llm)
            config = {"cutoff_score": self.cutoff}
            self.state.update_status("Clients Initialized. Listening...")
        except Exception as e:
            print(colored(f"Initialization Error: {e}", "red"))
            self.state.update_status(f"Init Error: {e}")
            return

        print(colored("Listening for new emails...", "yellow"))

        while not stop_event.is_set():
            try:
                self.state.update_status("Polling Gmail...")
                messages = gmail.fetch_unread_emails()
                
                if not messages:
                    print(".", end="", flush=True) 
                    self.state.update_status("Idle. Waiting for emails.")
                    # Sleep in small chunks to allow quick shutdown
                    for _ in range(self.interval):
                        if stop_event.is_set(): break
                        time.sleep(1)
                    continue
                
                self.state.log_activity(f"Found {len(messages)} unread messages.")
                print(f"\nFound {len(messages)} messages.")

                for msg_meta in messages:
                    if stop_event.is_set(): break
                    
                    msg_id = msg_meta['id']
                    try:
                        email_data = gmail.get_email_details(msg_id)
                        self.state.log_activity(f"Analyzing: {email_data.sender_email}")
                        
                        # 1. Classify
                        classification = agent.classify_email(email_data)
                        if not classification.is_job_application:
                            self.state.log_activity(f"Skipping {email_data.sender_email}: Not application")
                            gmail.mark_as_read(msg_id)
                            continue

                        if not email_data.attachment_path:
                            self.state.log_activity(f"Skipping {email_data.sender_email}: No resume")
                            gmail.mark_as_read(msg_id)
                            continue
                            
                        # 2. Run Agent
                        self.state.update_status(f"Processing candidate: {email_data.sender_email}")
                        print(f" -> Processing {email_data.sender_email}")
                        result = agent.run(email_data, jd_text, config)

                        if result: 
                            # Save to dashboard
                            candidate_info = {
                                "name": result['resume']['name'],
                                "score": result['score']['final_ats_score'],
                                "decision": result['decision']['decision'],
                                "skills": result['resume']['skills'],
                                "breakdown": result['score']
                            }
                            self.state.update_candidate(candidate_info)
                            
                            # 3. Send Reply
                            email_draft = result['email']
                            gmail.send_reply(
                                to_email=email_data.sender_email,
                                subject=email_draft['email_subject'],
                                body=email_draft['email_body']
                            )
                            self.state.log_activity(f"Reply sent to {email_data.sender_email}")
                        
                        # 4. Cleanup
                        gmail.mark_as_read(msg_id)
                    
                    except Exception as e:
                        err_msg = f"Error processing message {msg_id}: {e}"
                        print(colored(err_msg, "red"))
                        self.state.log_activity(err_msg)
                
                self.state.update_status("Waiting...")
                # Sleep loop
                for _ in range(self.interval):
                    if stop_event.is_set(): break
                    time.sleep(1)

            except KeyboardInterrupt:
                break
            except Exception as e:
                print(colored(f"\nCritical Loop Error: {e}", "red"))
                self.state.update_status(f"Crashed: {e}")
                time.sleep(self.interval)
        
        self.state.update_status("Stopped.")
        print("Bot Service Stopped.")

def main():
    parser = argparse.ArgumentParser(description="Realtime Resume Screening Bot (Gmail)")
    parser.add_argument("--jd", required=True, help="Path to Job Description file (TXT)")
    parser.add_argument("--model", default="llama3.2:3b", help="Ollama model name")
    parser.add_argument("--cutoff", type=int, default=70, help="ATS Score Cutoff")
    parser.add_argument("--interval", type=int, default=60, help="Polling interval in seconds")

    args = parser.parse_args()

    # Create stop event for standalone run (Ctrl+C will handle it mainly, but good practice)
    stop_event = threading.Event()
    service = BotService(args.jd, args.model, args.cutoff, args.interval)
    
    try:
        service.run(stop_event)
    except KeyboardInterrupt:
        stop_event.set()

if __name__ == "__main__":
    main()

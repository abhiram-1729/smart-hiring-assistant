import argparse
import sys
import json
from agent import HiringAgent
from llm_client import LLMClient
from models import IncomingEmail

def main():
    parser = argparse.ArgumentParser(description="Automated Resume Screening Agent")
    parser.add_argument("--jd", required=True, help="Path to Job Description file (TXT or JSON)")
    parser.add_argument("--resume", required=True, help="Path to Resume file (PDF or DOCX)")
    parser.add_argument("--model", default="llama3.2:3b", help="Ollama model name")
    parser.add_argument("--cutoff", type=int, default=70, help="ATS Score Cutoff")
    parser.add_argument("--mock", action="store_true", help="Run in mock mode (no Ollama required)")
    
    args = parser.parse_args()

    # Load resources
    try:
        with open(args.jd, 'r') as f:
            jd_text = f.read()
    except Exception as e:
        print(f"Error reading JD file: {e}")
        sys.exit(1)

    # Convert resume file path to absolute if needed, generally fine as is if passed correctly
    resume_path = args.resume

    # Simulate Incoming Email
    email = IncomingEmail(
        sender_email="candidate@example.com",
        subject="Application for the Software Engineer Role",
        body_text="Dear Hiring Manager,\n\nPlease find attached my resume for the position. I have strong experience in Python and AI.\n\nBest,\nCandidate",
        attachment_path=resume_path
    )

    # Config
    config = {
        "cutoff_score": args.cutoff
    }

    # Initialize Agent
    client = LLMClient(model_name=args.model, mock_mode=args.mock)
    agent = HiringAgent(client)

    # Run
    try:
        agent.run(email, jd_text, config)
    except Exception as e:
        print(f"\nError during execution: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()

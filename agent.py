import json
from termcolor import colored
from models import (
    IncomingEmail, JobDescription, ResumeData, 
    ATSScore, DecisionOutput, EmailDraft, ClassificationResult
)
from llm_client import LLMClient
from resume_parser import ResumeParser
from ats_scorer import ATSScorer

class HiringAgent:
    def __init__(self, llm_client: LLMClient):
        self.llm = llm_client

    def run(self, email: IncomingEmail, jd_text: str, config: dict):
        print(colored("\n--- STEP 1: Email Classification ---", "cyan"))
        classification = self.classify_email(email)
        print(f"Is Job Application: {classification.is_job_application} (Confidence: {classification.confidence}%)")
        
        if not classification.is_job_application:
            print(colored("Stopping processing: Not a job application.", "yellow"))
            return

        print(colored("\n--- STEP 3: Job Description Understanding ---", "cyan"))
        # Note: Swapped order slightly to have JD ready for matching or if input is raw text
        # If jd_text is provided, parse it.
        jd = self.parse_jd(jd_text)
        print(f"Role: {jd.role_title}")
        print(f"Mandatory Skills: {jd.mandatory_skills}")

        print(colored("\n--- STEP 2: Resume Parsing ---", "cyan"))
        resume_data = self.parse_resume(email.attachment_path)
        print(f"Candidate: {resume_data.name}")
        print(f"Experience: {resume_data.experience_years} years")
        print(f"Skills: {resume_data.skills}")

        print(colored("\n--- STEP 4: ATS Scoring ---", "cyan"))
        scorer = ATSScorer(jd, self.llm)
        score_result = scorer.score(resume_data)
        print(f"Final ATS Score: {score_result.final_ats_score}/100")
        print(f"Breakdown: {score_result.model_dump()}")

        print(colored("\n--- STEP 5: Decision Logic ---", "cyan"))
        cutoff_score = config.get("cutoff_score", 70)
        decision = self.make_decision(score_result.final_ats_score, cutoff_score)
        print(f"Decision: {decision.decision}")
        print(f"Reason: {decision.reason_summary}")

        print(colored("\n--- STEP 6: Email Generation ---", "cyan"))
        email_draft = self.generate_email(decision, resume_data.name, jd.role_title)
        print(f"Subject: {email_draft.email_subject}")
        print(f"Body Preview: {email_draft.email_body[:100]}...")
        
        return {
            "classification": classification.model_dump(),
            "jd": jd.model_dump(),
            "resume": resume_data.model_dump(),
            "score": score_result.model_dump(),
            "decision": decision.model_dump(),
            "email": email_draft.model_dump()
        }

    def classify_email(self, email: IncomingEmail) -> ClassificationResult:
        prompt = f"""
        Analyze the following email to determine if it is a job application.
        Sender: {email.sender_email}
        Subject: {email.subject}
        Body: {email.body_text}
        Has Attachment: {bool(email.attachment_path)}

        Return valid JSON with 'is_job_application' (boolean) and 'confidence' (0-100).
        """
        return self.llm.generate_json(prompt, ClassificationResult)

    def parse_jd(self, jd_text: str) -> JobDescription:
        prompt = f"""
        Extract structured information from the following Job Description text.
        
        JD Text:
        {jd_text}
        
        Return valid JSON matching the JobDescription schema.
        Ensure 'mandatory_skills' and 'preferred_skills' are extracted as lists of strings.
        Normalize skill names (e.g. "Python 3" -> "Python").
        """
        return self.llm.generate_json(prompt, JobDescription)

    def parse_resume(self, file_path: str) -> ResumeData:
        # 1. Extract raw text
        raw_text = ResumeParser.extract_text(file_path)
        
        # 2. Structure with LLM
        prompt = f"""
        Extract structured data from the following Resume text.
        
        Resume Text:
        {raw_text[:4000]}  # Truncate to avoid context window issues if too long
        
        Return valid JSON matching the ResumeData schema.
        IMPORTANT: Extract specific technical skills, tools, languages, and frameworks as a flat list of strings. 
        Do NOT summarize them into categories (e.g. use "Python", "SQL", "React" instead of "Backend Development").
        
        CRITICAL: For experience_years, ONLY count actual work experience (internships, jobs, freelance).
        DO NOT count education years (college, university) as work experience.
        If no work experience is found, return 0 for experience_years.
        The experience_years field must be a simple number (e.g., 2.5), NOT a string with dates.
        """
        return self.llm.generate_json(prompt, ResumeData)

    def make_decision(self, score: float, cutoff: float) -> DecisionOutput:
        if score >= cutoff:
            return DecisionOutput(
                decision="PROCEED",
                reason_summary=f"Score {score} is above cutoff {cutoff}."
            )
        else:
            return DecisionOutput(
                decision="REJECT",
                reason_summary=f"Score {score} is below cutoff {cutoff}."
            )

    def generate_email(self, decision: DecisionOutput, candidate_name: str, role_title: str) -> EmailDraft:
        prompt = f"""
        Write a professional email to the candidate based on the hiring decision.
        
        Candidate Name: {candidate_name}
        Role: {role_title}
        Decision: {decision.decision}
        
        Guidelines:
        - If PROCEED: Thank them, confirm shortlisting, mention next steps (interview). Professional tone.
        - If REJECT: Thank them, inform politely, encourage future applications. Do NOT mention specific scores.
        
        Return valid JSON with 'email_subject' and 'email_body'.
        """
        return self.llm.generate_json(prompt, EmailDraft)

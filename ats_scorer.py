from models import JobDescription, ResumeData, ATSScore
from llm_client import LLMClient
import json

class ATSScorer:
    def __init__(self, jd: JobDescription, llm_client: LLMClient):
        self.jd = jd
        self.llm = llm_client

    def score(self, resume: ResumeData) -> ATSScore:
        prompt = f"""
        Act as an expert Technical Recruiter. Evaluate the candidate's resume against the Job Description.
        
        ### Job Description
        Role: {self.jd.role_title}
        Mandatory Skills: {', '.join(self.jd.mandatory_skills)}
        Preferred Skills: {', '.join(self.jd.preferred_skills)}
        Min Experience: {self.jd.min_experience_years} years
        
        ### Candidate Resume
        Name: {resume.name}
        Experience: {resume.experience_years} years
        Skills: {', '.join(resume.skills)}
        Projects: {', '.join(resume.projects)}
        Education: {', '.join(resume.education)}
        
        ### Scoring Instructions (0-100 Scale)
        ### Scoring Instructions (0-100 Scale)
        1. **Skill Score**: Compare Candidate Skills vs JD Skills. 
           - Match indiscriminately (e.g. "Python" == "Python 3", "React" == "ReactJS"). 
           - If most mandatory skills are present, score high (>80). 
           - If some are missing but related skills exist, give partial credit.
        2. **Experience Score**: 
           - If Candidate Experience >= Min Experience, score 100.
           - If Candidate Experience is within 1 year of Min, score 80.
           - Otherwise, scale down.
        3. **Keyword Score**: How well does the resume terminology align with the JD?
        4. **Education Score**: 100 for relevant degree, 50 for unrelated degree, 0 if missing.
        5. **Final ATS Score**: Calculate weighted average: Skills (50%) + Exp (20%) + Keywords (20%) + Edu (10%).

        Return valid JSON matching the ATSScore schema.
        
        CRITICAL: The following is just an example of the JSON format. Do NOT use these scores. You MUST calculate scores based on the actual candidate data above.
        Your response must contain ACTUAL NUMBERS (like 75.5), NOT schema definitions (like {{"type": "number"}}).
        
        Example JSON Structure:
        {{
            "skill_score": 0.0,
            "experience_score": 0.0,
            "keyword_score": 0.0,
            "education_score": 0.0,
            "final_ats_score": 0.0
        }}
        """
        
        return self.llm.generate_json(prompt, ATSScore)


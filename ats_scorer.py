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
        1. **Skill Score**: Match candidate skills to JD (Mandatory counts double). heavily penalize missing mandatory skills. Handle semantic matches (e.g. "React" == "React.js").
        2. **Experience Score**: Does their experience years meet the minimum? Are the projects relevant?
        3. **Keyword Score**: How well does the resume reflect industry standard keywords for this role?
        4. **Education Score**: 100 if they meet degree requirements, 50 if partial, 0 if missing.
        5. **Final ATS Score**: Weighted average: Skills (50%) + Exp (20%) + Keywords (20%) + Edu (10%).

        Return valid JSON matching the ATSScore schema.
        
        CRITICAL: The following is just an example of the JSON format. Do NOT use these scores. You MUST calculate scores based on the actual candidate data above.
        
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


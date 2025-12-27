from typing import List, Optional, Dict
from pydantic import BaseModel, Field, field_validator

class IncomingEmail(BaseModel):
    sender_email: str
    subject: str
    body_text: str
    attachment_path: Optional[str] = None

class JobDescription(BaseModel):
    role_title: str
    mandatory_skills: List[str]
    preferred_skills: List[str] = []
    min_experience_years: int
    responsibilities: List[str] = []
    keywords: List[str] = []

class ResumeData(BaseModel):
    name: str
    email: str
    phone: Optional[str] = None
    experience_years: Optional[float] = 0.0
    education: List[str] = []
    skills: List[str] = []
    projects: List[str] = []
    companies: List[str] = []
    certifications: List[str] = []

    @field_validator('experience_years', mode='before')
    @classmethod
    def set_experience_default(cls, v):
        if v is None:
            return 0.0
        if isinstance(v, str):
            # Extract numeric part from strings like "4.5 (2021-2025)" or "4.5"
            import re
            match = re.search(r'(\d+\.?\d*)', v)
            if match:
                return float(match.group(1))
            return 0.0
        return v

    @field_validator('education', 'skills', 'projects', 'companies', 'certifications', mode='before')
    @classmethod
    def flatten_dicts(cls, v):
        """
        Handle cases where LLM returns a list of dictionaries instead of strings.
        Extracts the first string value found in the dictionary values.
        """
        if not isinstance(v, list):
            return v
        
        new_list = []
        for item in v:
            if isinstance(item, str):
                new_list.append(item)
            elif isinstance(item, dict):
                # Extract the first useful string value
                # e.g. {'skill_name': 'python'} -> 'python'
                # e.g. {'title': 'Degree', 'gpa': '4.0'} -> 'Degree: 4.0' or just 'Degree'
                vals = [str(val) for val in item.values() if isinstance(val, (str, int, float))]
                if vals:
                    new_list.append(" - ".join(vals))
            else:
                new_list.append(str(item))
        return new_list

class ATSScore(BaseModel):
    skill_score: float
    experience_score: float
    keyword_score: float
    education_score: float
    final_ats_score: float

class DecisionOutput(BaseModel):
    decision: str  # "PROCEED" or "REJECT"
    reason_summary: str

class EmailDraft(BaseModel):
    email_subject: str
    email_body: str

class ClassificationResult(BaseModel):
    is_job_application: bool
    confidence: float

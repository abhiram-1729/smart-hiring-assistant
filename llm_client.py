import requests
import json
from typing import Dict, Any, Type, TypeVar
from pydantic import BaseModel

T = TypeVar('T', bound=BaseModel)

class LLMClient:
    def __init__(self, model_name: str = "mistral", base_url: str = "http://localhost:11434", mock_mode: bool = False):
        self.model_name = model_name
        self.base_url = base_url
        self.mock_mode = mock_mode

    def generate_json(self, prompt: str, schema: Type[T]) -> T:
        """
        Generates a JSON response from the LLM conforming to the Pydantic schema.
        """
        if self.mock_mode:
            return self._generate_mock(schema)

        schema_json = json.dumps(schema.model_json_schema(), indent=2)
        system_prompt = f"""
You are an AI assistant that outputs strictly valid JSON.
Your task is to generate a JSON object that strictly follows this schema:
{schema_json}

Rules:
1. Output ONLY the JSON object.
2. Do NOT output the schema itself.
3. Do NOT wrap the content in markdown blocks (no ```json).
4. The root object should contain the fields directly, not nested under "properties".
5. Do NOT include schema metadata like "type", "title", "default", "items" in the values. Fill them with actual extracted data.
"""

        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "system": system_prompt,
            "stream": False,
            "format": "json"
        }

        try:
            response = requests.post(f"{self.base_url}/api/generate", json=payload)
            response.raise_for_status()
            result = response.json()
            raw_json = result.get("response", "")
            
            # Basic cleanup if the model adds markdown code blocks
            if "```json" in raw_json:
                raw_json = raw_json.split("```json")[1].split("```")[0]
            elif "```" in raw_json:
                raw_json = raw_json.split("```")[1].split("```")[0]
            
            data = json.loads(raw_json)
            
            # Robustness fix: Llama 3.2 often wraps data in "properties" key resembling schema
            # Robustness fix: Handle various hallucinated JSON structures
            if isinstance(data, dict):
                # 1. Nested under "properties" (common schema reflection)
                if "properties" in data and isinstance(data["properties"], dict):
                    # Check if the "properties" dict contains the actual data values
                    # Sometimes LLM puts values INSIDE properties: {"properties": {"field": "value"}}
                    # Sometimes it puts schemas INSIDE properties: {"properties": {"field": {"type": "string"}}}
                    # We check if the values start looking like schema definitions (dicts with 'type')
                    # OR if the top level has the data.
                    
                    # Heuristic: If top level has the keys we want (excluding schema keys), use top level.
                    # Schema keys: title, type, properties, required
                    schema_keys = {"title", "type", "properties", "required", "$defs", "definitions"}
                    data_keys = set(data.keys()) - schema_keys
                    
                    # If we have substantial data keys at root, just strip schema keys
                    if data_keys:
                        for k in schema_keys:
                            data.pop(k, None)
                    else:
                        # Maybe data is inside properties? 
                        # Check one value in properties
                        props = data["properties"]
                        if props:
                            first_val = next(iter(props.values()))
                            # It is a schema definition ONLY if it has 'type' AND NO 'value'
                            # If it has 'value', we treat it as data (wrapped)
                            is_pure_schema = isinstance(first_val, dict) and "type" in first_val and "value" not in first_val
                            
                            if not is_pure_schema:
                                # It's data (possibly wrapped), so extract it
                                data = props

                # 2. Strip schema reflection if it leaked into the data
                data.pop("title", None)
                data.pop("type", None)
                data.pop("required", None)
                data.pop("properties", None)

                # 3. Handle nested "value" keys (e.g. {"field": {"value": 85}})
                for key, val in data.items():
                    if isinstance(val, dict) and "value" in val:
                        # Heuristic: if it has "value", use that.
                        # But be careful it's not some actual nested dict user wanted.
                        # Given our models (simple integers/strings mostly), this is safely likely a hallucination.
                        data[key] = val["value"]

            return schema.model_validate(data)
        except Exception as e:
            print(f"Error calling Ollama or parsing JSON: {e}")
            print(f"Raw response: {raw_json}") 
            raise

    def _generate_mock(self, schema: Type[T]) -> T:
        schema_name = schema.__name__
        if schema_name == "ClassificationResult":
            return schema(is_job_application=True, confidence=95.0)
        elif schema_name == "JobDescription":
            return schema(
                role_title="Senior Python Developer",
                mandatory_skills=["Python", "FastAPI", "SQL"],
                preferred_skills=["Docker", "Kubernetes"],
                min_experience_years=5,
                responsibilities=["Build APIs", "Deploy models"],
                keywords=["Python", "AI", "Backend"]
            )
        elif schema_name == "ResumeData":
            return schema(
                name="John Doe",
                email="john@example.com",
                experience_years=6.0,
                education=["Bachelor of Computer Science"],
                skills=["Python", "Django", "FastAPI", "Docker", "AWS"],
                projects=["AI Chatbot", "E-commerce API"],
                companies=["Tech Corp", "StartUp Inc"],
                certifications=[]
            )
        elif schema_name == "DecisionOutput":
            # This logic is usually heuristic in the agent, but if agent asks LLM for decision (it doesn't, it asks logic)
            # Wait, make_decision is in Agent. generate_email calls LLM.
            pass
        elif schema_name == "EmailDraft":
            return schema(
                email_subject="Update on your application",
                email_body="Dear Candidate,\n\nWe are pleased to inform you..."
            )
        
        # Fallback
        return schema()


    def generate_text(self, prompt: str) -> str:
        """
        Generates a text response from the LLM.
        """
        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "stream": False
        }

        try:
            response = requests.post(f"{self.base_url}/api/generate", json=payload)
            response.raise_for_status()
            result = response.json()
            return result.get("response", "")
        except Exception as e:
            print(f"Error calling Ollama: {e}")
            raise

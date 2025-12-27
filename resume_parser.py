import os
from pypdf import PdfReader
from docx import Document

class ResumeParser:
    @staticmethod
    def extract_text(file_path: str) -> str:
        """
        Extracts text from a PDF or DOCX file.
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        _, ext = os.path.splitext(file_path)
        ext = ext.lower()

        if ext == '.pdf':
            return ResumeParser._extract_from_pdf(file_path)
        elif ext in ['.docx', '.doc']:
            return ResumeParser._extract_from_docx(file_path)
        else:
            raise ValueError(f"Unsupported file format: {ext}")

    @staticmethod
    def _extract_from_pdf(file_path: str) -> str:
        text = ""
        try:
            reader = PdfReader(file_path)
            for page in reader.pages:
                text += page.extract_text() + "\n"
        except Exception as e:
            print(f"Error reading PDF: {e}")
            raise
        return text

    @staticmethod
    def _extract_from_docx(file_path: str) -> str:
        text = ""
        try:
            doc = Document(file_path)
            for para in doc.paragraphs:
                text += para.text + "\n"
        except Exception as e:
            print(f"Error reading DOCX: {e}")
            raise
        return text

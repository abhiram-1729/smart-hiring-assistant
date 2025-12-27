# 🤖 AI-Powered Resume Screening Agent

An intelligent, automated hiring assistant that processes job applications via Gmail, extracts resume data, scores candidates using LLM-based ATS logic, and sends personalized responses—all in real-time.

![Python](https://img.shields.io/badge/python-3.13-blue.svg)
![Streamlit](https://img.shields.io/badge/streamlit-1.40-red.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

## 🎥 Demo
[▶️ Click here to watch the demo video](https://github.com/abhiram-1729/smart-hiring-assistant/blob/main/video/vedio.mp4?raw=true)

_(Note: GitHub redirects to the raw file which browser plays)_

## ✨ Features

- 📧 **Gmail API Integration** - Automatically monitors inbox for job applications
- 📄 **Smart Resume Parsing** - Extracts structured data from PDF/DOCX resumes using LLM
- 🎯 **Semantic ATS Scoring** - Understands context (e.g., "LangChain" matches "LLM Framework")
- 🚀 **Real-time Dashboard** - Live Streamlit UI with metrics, logs, and candidate analysis
- ✉️ **Automated Responses** - Sends professional proceed/reject emails automatically
- 🔧 **Local LLM Inference** - Powered by Ollama (Llama 3.2) for privacy and cost-efficiency

## 🏗️ Architecture

```
┌─────────────┐
│   Gmail     │ ──► New Email with Resume
└─────────────┘
       │
       ▼
┌─────────────────────────────────────────┐
│         Resume Screening Agent          │
│  ┌───────────────────────────────────┐  │
│  │ 1. Email Classification           │  │
│  │ 2. Resume Parsing (PDF/DOCX)      │  │
│  │ 3. Job Description Understanding  │  │
│  │ 4. ATS Scoring (LLM-based)        │  │
│  │ 5. Decision Logic (Proceed/Reject)│  │
│  │ 6. Email Generation               │  │
│  └───────────────────────────────────┘  │
└─────────────────────────────────────────┘
       │
       ▼
┌─────────────┐         ┌──────────────┐
│ Send Reply  │         │  Dashboard   │
│   Email     │         │  (Streamlit) │
└─────────────┘         └──────────────┘
```

## 🚀 Quick Start

### Prerequisites

- Python 3.13+
- [Ollama](https://ollama.ai/) installed and running
- Gmail account with API access
- Google Cloud Project with Gmail API enabled

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/ai-resume-screener.git
   cd ai-resume-screener
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up Ollama**
   ```bash
   # Install Ollama from https://ollama.ai/
   ollama pull llama3.2:3b
   ollama serve
   ```

4. **Configure Gmail API**
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project
   - Enable Gmail API
   - Create OAuth 2.0 credentials (Desktop App)
   - Download `credentials.json` and place it in the project root

5. **Customize Job Description**
   ```bash
   # Edit data/jd.txt with your job requirements
   nano data/jd.txt
   ```

### Running the Application

#### Option 1: Streamlit Dashboard (Recommended)
```bash
streamlit run dashboard.py
```
- Opens at `http://localhost:8501`
- Use Start/Stop buttons to control the bot
- View real-time logs and candidate scores

#### Option 2: CLI Mode (Testing)
```bash
python main.py --email sample_email.txt --resume sample_resume.pdf
```

## 📁 Project Structure

```
email agent/
├── agent.py              # Main workflow orchestration
├── ats_scorer.py         # LLM-based ATS scoring logic
├── dashboard.py          # Streamlit UI
├── gmail_client.py       # Gmail API integration
├── llm_client.py         # Ollama LLM client
├── models.py             # Pydantic data models
├── realtime_bot.py       # Background bot service
├── resume_parser.py      # PDF/DOCX text extraction
├── state_manager.py      # Dashboard state management
├── main.py               # CLI entry point
├── data/
│   └── jd.txt           # Job description
├── temp/                # Downloaded attachments
└── credentials.json     # Gmail OAuth credentials (not in repo)
```

## 🎯 How It Works

### 1. Email Classification
Uses LLM to determine if an email is a job application (confidence score).

### 2. Resume Parsing
- Extracts text from PDF/DOCX
- LLM structures data: name, email, skills, experience, education, projects

### 3. Job Description Understanding
LLM extracts: role, mandatory/preferred skills, min experience, keywords

### 4. ATS Scoring (LLM-based)
- **Skill Score (50%)**: Semantic matching of candidate skills to JD requirements
- **Experience Score (20%)**: Years of experience vs. minimum required
- **Keyword Score (20%)**: Industry-standard keyword matching
- **Education Score (10%)**: Degree/certification alignment

### 5. Decision Logic
- Score ≥ 70: **PROCEED** (send positive email)
- Score < 70: **REJECT** (send polite rejection)

### 6. Email Generation
LLM generates personalized, professional response emails.

## ⚙️ Configuration

### Changing the LLM Model
Edit `main.py` or `dashboard.py`:
```python
llm = LLMClient(model_name="llama3.2:3b")  # Change model here
```

### Adjusting Score Threshold
Edit `agent.py`:
```python
def make_decision(self, score: ATSScore) -> DecisionOutput:
    threshold = 70  # Adjust threshold here
```

### Customizing Email Templates
The LLM generates emails dynamically. To influence tone, edit the prompt in `agent.py`:
```python
def generate_email(self, decision: DecisionOutput, resume: ResumeData) -> EmailDraft:
    # Modify the prompt here
```

## 🐛 Troubleshooting

### Gmail API Issues
- **Error**: `redirect_uri_mismatch`
  - **Fix**: Ensure `http://localhost:8080/` is in authorized redirect URIs in Google Cloud Console

### Ollama Connection Issues
- **Error**: `Connection refused`
  - **Fix**: Run `ollama serve` in a separate terminal

### Resume Parsing Errors
- **Error**: `experience_years validation error`
  - **Fix**: The system now handles null/string values automatically via validators

## 🤝 Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- [Ollama](https://ollama.ai/) for local LLM inference
- [Streamlit](https://streamlit.io/) for the dashboard framework
- [Google Gmail API](https://developers.google.com/gmail/api) for email automation

## 📧 Contact

For questions or support, please open an issue on GitHub.

---

**Built with ❤️ using Python, Streamlit, and Ollama**

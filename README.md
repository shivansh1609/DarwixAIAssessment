# 🎙️ VoxIntel AI

<div align="center">

# AI-Powered Voice Intelligence Platform

### Voice Agent • Knowledge Retrieval • Multilingual AI • Live Insights

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-Backend-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![Groq](https://img.shields.io/badge/Groq-LLM-black?style=for-the-badge)
![JavaScript](https://img.shields.io/badge/JavaScript-Frontend-F7DF1E?style=for-the-badge&logo=javascript&logoColor=black)

</div>

---

# 📖 Overview

VoxIntel AI is an AI Engineering assessment project demonstrating the core building blocks of a modern conversational AI platform.

The repository consists of four independent modules that showcase voice interaction, knowledge-grounded retrieval (RAG), multilingual localization, and real-time conversational intelligence.

---

# ✨ Features

- 🎤 AI Voice Agent
- 🧠 Retrieval-Augmented Generation (RAG)
- 🌍 Multilingual Voice Support
- 📚 Semantic Knowledge Base
- ⚡ Real-Time Live Insights
- 🔊 Text-to-Speech
- 🎧 Speech Recognition
- 📡 WebSocket Communication
- 💻 Modern Dark Responsive UI

---

# 🏗️ Architecture

```text
                           User
                             │
                             ▼
                  +----------------------+
                  |     Frontend UI      |
                  +----------+-----------+
                             │
                             ▼
                  +----------------------+
                  |    FastAPI Backend   |
                  +----------+-----------+
                             │
      ┌──────────────────────┼──────────────────────┐
      │                      │                      │
      ▼                      ▼                      ▼
+-------------+     +----------------+     +----------------+
|  Groq LLM   |     | Knowledge Base |     | Speech Services|
+-------------+     +----------------+     +----------------+
                             │
                             ▼
                  +----------------------+
                  |   Live Insights      |
                  +----------------------+
```

---

# 📂 Repository Structure

```text
VoxIntelAI
│
├── docs/
│
├── VoiceAgent/
│   ├── api/
│   ├── frontend/
│   └── vapi_config/
│
├── KnowledgeBase/
│   ├── data/
│   ├── scripts/
│   └── run_pipeline.py
│
├── Multilingual/
│   ├── indoVoiceAgent/
│   └── phillVoiceAgent/
│
├── LiveInsights/
│   ├── dashboard/
│   └── pipeline/
│
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

---

# 🛠️ Tech Stack

## Backend

- FastAPI
- Python
- WebSockets

## AI

- Groq LLM
- Retrieval-Augmented Generation (RAG)
- Sentence Transformers

## Speech

- Web Speech API
- Microsoft Edge TTS
- Vosk

## Knowledge Base

- Semantic Search
- Vector Embeddings
- NumPy
- BeautifulSoup
- PDF & DOCX Parsing

## Frontend

- HTML5
- CSS3
- JavaScript (ES6)

---

# 🚀 Getting Started

## Clone Repository

```bash
git clone https://github.com/shivansh1609/DarwixAIAssessment.git

cd DarwixAIAssessment
```

---

## Create Virtual Environment

### Windows

```bash
python -m venv venv

venv\Scripts\activate
```

### Linux / macOS

```bash
python3 -m venv venv

source venv/bin/activate
```

---

## Install Dependencies

```bash
pip install -r requirements.txt
```

---

## Configure Environment

Create a `.env` file.

```env
GROQ_API_KEY=your_groq_api_key

HOST=0.0.0.0
PORT=8000

DEBUG=True
```

---

# ▶️ Running Modules

## 🎤 Voice Agent

```bash
cd VoiceAgent/api

uvicorn main:app --reload
```

Open:

```
http://127.0.0.1:8000
```

---

## 📚 Knowledge Base

```bash
cd KnowledgeBase

python run_pipeline.py
```

---

## 📊 Live Insights

Open

```
LiveInsights/dashboard/index.html
```

or run its backend (if available):

```bash
cd LiveInsights

python main.py
```

---

## 🌍 Multilingual

Contains localized conversational resources for:

- Indonesia
- Philippines

No separate execution is required.

---

# 📦 Modules

## 🎤 Voice Agent

- Voice conversation
- Speech Recognition
- Groq LLM
- Edge TTS
- Responsive Frontend

---

## 📚 Knowledge Base

- Document ingestion
- Semantic search
- Source-grounded retrieval
- Vector similarity search

---

## 🌍 Multilingual

- Localization
- Code-switching
- Region-specific prompts
- Cultural adaptations

---

## 📊 Live Insights

- Conversation transcript
- AI nudges
- Live dashboard
- Signal monitoring

---

# 🔒 Environment Variables

Create a `.env` file based on `.env.example`.

```env
GROQ_API_KEY=your_groq_api_key
```

> Never commit your `.env` file or API keys to GitHub.

---

# 📌 Future Enhancements

- Resume Upload & Parsing
- Candidate Evaluation Dashboard
- Docker Support
- Authentication
- Cloud Deployment
- Conversation History
- Additional LLM Providers
- CI/CD Pipeline

---

# 👨‍💻 Author

**Shivanshu Pandey**

GitHub: https://github.com/shivansh1609

LinkedIn: https://www.linkedin.com/in/shivanshupandey16

---

⭐ If you found this project useful, consider giving it a star.
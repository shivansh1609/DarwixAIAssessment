# 🎙️ VoxIntel AI

<div align="center">

### AI-Powered Voice Intelligence Platform

Knowledge-Grounded • Multilingual • Real-Time Insights

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-Backend-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![Groq](https://img.shields.io/badge/Groq-LLM-black?style=for-the-badge)
![JavaScript](https://img.shields.io/badge/JavaScript-Frontend-F7DF1E?style=for-the-badge&logo=javascript&logoColor=black)

</div>

---

# 📖 Overview

VoxIntel AI is a modern AI-powered voice assistant platform that combines speech recognition, large language models, knowledge-grounded retrieval, multilingual support, and live conversational analytics into a unified web experience.

The platform enables natural voice conversations while retrieving contextual information from a knowledge base and providing real-time insights through an interactive dashboard.

---

# ✨ Features

- 🎤 AI Voice Assistant
- 🧠 Knowledge-Grounded Responses (RAG)
- 🌍 Multilingual Voice Support
- 📚 Semantic Knowledge Retrieval
- ⚡ Real-Time Live Insights Dashboard
- 🔊 Text-to-Speech Responses
- 🎧 Speech Recognition
- 📡 WebSocket Communication
- 💻 Modern Responsive UI

---

# 🏗️ Project Architecture

```
                    User
                      │
                      ▼
             ┌─────────────────┐
             │   Frontend UI   │
             │ Voice Dashboard │
             └────────┬────────┘
                      │
                      ▼
             ┌─────────────────┐
             │ FastAPI Backend │
             └───┬─────┬───────┘
                 │     │
                 │     ├────────────► Knowledge Base
                 │
                 ├────────────► Groq LLM
                 │
                 └────────────► Speech Services
                      │
                      ▼
             ┌─────────────────┐
             │ Live Insights   │
             └─────────────────┘
```

---

# 📂 Project Structure

```
VoxIntelAI
│
├── docs/
│
├── VoiceAgent/
│   ├── api/
│   ├── vapi_config/
│   └── web_client/
│
├── KnowledgeBase/
│
├── Multilingual/
│   ├── indonesia/
│   └── philippines/
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

### Backend

- FastAPI
- Python
- WebSockets

### AI

- Groq LLM
- Retrieval-Augmented Generation (RAG)
- Sentence Transformers

### Speech

- Web Speech API
- Microsoft Edge TTS
- Vosk

### Knowledge Base

- Vector Embeddings
- Semantic Search
- NumPy
- BeautifulSoup

### Frontend

- HTML
- CSS
- JavaScript

---

# 🚀 Getting Started

## Clone Repository

```bash
git clone https://github.com/shivansh1609/DarwixAIAssessment.git
cd DarwixAIAssessment
```

---

## Create Virtual Environment

Windows

```bash
python -m venv venv
venv\Scripts\activate
```

Linux / macOS

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

Create a `.env` file from `.env.example`.

```env
GROQ_API_KEY=your_api_key

HOST=0.0.0.0
PORT=8000

DEBUG=True
```

---

## Run Backend

```bash
uvicorn api.main:app --reload
```

---

## Open Frontend

Open

```
VoiceAgent/web_client/index.html
```

or serve it using any local web server.

---

# 📦 Modules

### 🎤 Voice Agent

- Voice interaction
- Speech recognition
- AI responses
- Text-to-Speech

---

### 📚 Knowledge Base

- Semantic retrieval
- Source-grounded responses
- Vector search

---

### 🌍 Multilingual Support

- Indonesia
- Philippines

Supports localization, code-switching, and region-specific conversational behavior.

---

### 📊 Live Insights

- Conversation transcript
- Signal detection
- AI nudges
- Real-time dashboard

---

# 🔒 Environment Variables

Create a `.env` file using the provided `.env.example`.

Example:

```
GROQ_API_KEY=your_api_key
```

> **Note:** Never commit your `.env` file or API keys to GitHub.

---

# 📌 Future Improvements

- Docker Support
- Authentication
- Conversation History
- Cloud Deployment
- Additional LLM Providers
- Voice Analytics
- Admin Dashboard
- CI/CD Pipeline

---

# 📷 Screenshots

You can add screenshots here after uploading them.

```
docs/screenshots/home.png

docs/screenshots/dashboard.png

docs/screenshots/voice-agent.png
```

---

# 🤝 Contributing

Contributions are always welcome.

Feel free to fork the repository and submit a pull request.

---

# 📄 License

This project is licensed under the MIT License.

---

# 👨‍💻 Author

**Shivansh Pandey**

GitHub:
https://github.com/shivansh1609

LinkedIn:
https://www.linkedin.com/in/shivanshupandey16/

---

<div align="center">

⭐ If you found this project useful, consider giving it a star.

</div>

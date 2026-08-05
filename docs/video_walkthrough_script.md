# Video Walkthrough Script

## Target Duration: 10-15 minutes

---

## Intro (1 min)
- "Hi, I'm [Name]. This is my submission for the AI Engineer Assessment."
- "I built a complete AI-powered candidate screening system called TalentBridge."
- "The key constraint: everything runs on FREE tools — no paid API keys."
- Brief tech stack overview: Groq (free LLM), ChromaDB + sentence-transformers (free embeddings), Web Speech API (free STT), edge-tts (free TTS), Vosk (free streaming ASR)

## Q2: Knowledge Base (3 min)
1. Show raw data: `q2_knowledge_base/data/raw/scraped_pages.json`
   - "I created realistic recruitment data simulating a company website with 15+ pages including job listings, FAQs, policies, and a document with PII."
2. Run the pipeline: `python run_pipeline.py`
   - Show each step: cleaning → PII detection → dedup → chunking → indexing
3. Show PII detection output: "Found Aadhaar numbers, emails, phone numbers — all flagged and redacted"
4. Show dedup: "Caught the duplicate SSE job listing"
5. Show retrieval test: Query "What benefits do you offer?" → show relevant results with source citations
6. Show KB schema: `kb_records.json` — record_id, category, source_url, version, pii_flag

## Q1: Voice Agent Demo (3 min)
1. Start the server: `python api/main.py`
2. Open http://localhost:8000 in Chrome
3. **Live demo call**: Click "Start Screening Call"
   - Say: "Hi, I'm Rahul. I applied for the Senior Software Engineer position."
   - Show the bot asking qualification questions
   - Show a KB lookup happening (check server logs)
   - Ask: "What benefits do you offer?" → bot searches KB and answers with real data
   - Say: "The salary seems low" → bot handles objection with KB-grounded response
   - Say: "Can I speak to a human?" → bot transfers immediately
4. Show the transcript download feature
5. Show leads in API: `GET /api/leads`

## Q3: Multilingual Bots (2 min)
1. Show Philippines system prompt: cultural adaptations (po/opo, Taglish)
2. Show localization examples: literal vs. localized (3 examples)
3. Show Indonesia system prompt: Bapak/Ibu, Javanese accent handling
4. Show Indonesia localization examples
5. Show cross-market comparison table
6. Explain TTS voices: fil-PH-BlessicaNeural, id-ID-GadisNeural
7. Discuss ASR limitations: no native Tagalog model in free tier

## Q4: Live Insights (3 min)
1. Run the pipeline: `python pipeline/orchestrator.py`
2. Open dashboard in browser
3. **Live demo**: Watch simulated call play through
   - Show transcript appearing in real-time
   - Point out signal detection: "Here, the customer mentions their friend needs a role — MISSED_CROSS_SELL detected"
   - Show frustration escalation: "Customer says 'I'm getting frustrated' — nudge appears immediately"
   - Show nudge filtering: "Low-confidence signals are suppressed — see the suppression counter"
4. Show latency report: P50/P95 for each component
5. Show the nudge engine rules: confidence threshold, cooldown, dedup

## Architecture & Design Decisions (1 min)
- "Why Groq over local Ollama? Llama 3.1 70B is too large to run locally on most machines. Groq's free tier gives us 70B quality at no cost."
- "Why Web Speech API over Whisper? Zero setup, works immediately in Chrome, decent accuracy for demo."
- "Why ChromaDB over Pinecone? Local, no account needed, sufficient for KB of this size."

## Known Limitations & Production Path (1 min)
- List top 3 limitations
- "For production: Deepgram for ASR, Vapi for phone numbers, OpenAI for embeddings"
- "Q4 at 10x scale would need local LLM or batch processing to avoid Groq rate limits"

## Closing (30 sec)
- "Everything runs from a single `git clone` + one free API key."
- "The system demonstrates: grounded responses (never hallucinate), safe fallback, measurable latency, and cultural localization — not just translation."

# Known Limitations

## Q1 — Voice Agent
- **Browser dependency**: Web Speech API only works in Google Chrome. Firefox, Safari, Edge have limited/no support.
- **STT accuracy**: Web Speech API is ~90% for clear English but degrades with accents, background noise, or fast speech.
- **Internet required**: Both edge-tts and Groq need internet. No fully offline voice mode.
- **No phone number**: Web-based calling only. No traditional phone/SIP integration without paid service (Vapi/Twilio).
- **Conversation memory**: Kept in-memory per session. Restarting the server loses all conversations.
- **Rate limits**: Groq free tier allows 30 RPM. Rapid testing may hit limits.
- **No concurrent calls**: Single-user design. Would need WebSocket sessions for multi-user.

## Q2 — Knowledge Base
- **Static content**: KB is indexed once at startup. No real-time crawling or update mechanism.
- **Embedding quality**: all-MiniLM-L6-v2 is good but not state-of-the-art. OpenAI text-embedding-3-large would perform better.
- **No reranking**: Results are ranked by cosine similarity only. A cross-encoder reranker would improve precision.
- **Limited dedup**: Jaccard similarity on 3-gram shingles may miss paraphrased duplicates.
- **PII detection**: Regex-based only. Would miss complex PII patterns. NER models would be more robust.

## Q3 — Multilingual Bots
- **ASR for Filipino/Indonesian**: No dedicated Tagalog or Bahasa Indonesia ASR model in free tier. Using English model with reduced accuracy.
- **TTS accent**: Edge-tts Filipino voice exists but sounds formal. Natural Taglish prosody not perfectly captured.
- **Regional accents**: Javanese, Sundanese, Bisaya accents not specifically supported in ASR. Accuracy drops ~15-20%.
- **Code-switching detection**: Not programmatic. Relies on LLM to detect and match language register.
- **No native speaker validation**: Scripts and localization need review by native Filipino and Indonesian speakers.
- **Regulatory compliance**: BSP (Philippines) and OJK (Indonesia) regulatory requirements not implemented.

## Q4 — Live Insights
- **Simulated mode only**: Vosk integration requires proper audio file. Default mode uses pre-written transcript.
- **Signal extraction latency**: LLM-based extraction adds 500-2000ms latency per analysis window.
- **False positives**: Rule-based fallback is crude. LLM-based extraction is better but still ~70-80% precision.
- **No speaker diarization**: Vosk basic model doesn't separate speakers. Deepgram or specialized models needed.
- **Scale limitations**: At 10x concurrent calls, Groq rate limits become bottleneck. Local LLM (Ollama) or batch processing needed.
- **Noisy audio**: Vosk WER increases ~20% with background noise. Pre-processing (noise reduction) not implemented.
- **No recording storage**: Dashboard shows live data only. Recordings need manual save.

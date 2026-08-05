# Q3 — Cross-Market Voice Bot Comparison

## Philippines vs. Indonesia — Multilingual Voice Assistant Evaluation

---

## Automatic Speech Recognition (ASR) Performance

| Metric | Philippines (Tagalog / Taglish) | Indonesia (Bahasa Indonesia) |
|--------|----------------------------------|------------------------------|
| **ASR Provider** | Web Speech API (Chrome) | Web Speech API (Chrome) |
| **Offline Fallback** | Vosk (English Model) | Vosk (English Model) |
| **Primary Language** | Taglish (Filipino + English) | Standard Bahasa Indonesia |
| **English Recognition Accuracy** | ~95% | ~95% |
| **Native Language Accuracy** | ~75–80% (using English acoustic model) | ~80–85% (using English acoustic model) |
| **Code-Switching Performance** | Moderate – English words are recognized reliably, while some Filipino connectors may be missed | Good – English loanwords commonly used in finance and technology are recognized effectively |
| **Regional Accent Coverage** | Manila accent performs well; Visayan dialect not evaluated | Jakarta accent performs well; Javanese accent achieves approximately 70% recognition accuracy |

---

## Text-to-Speech (TTS) Evaluation

| Feature | Philippines | Indonesia |
|---------|-------------|------------|
| **TTS Provider** | Microsoft Edge TTS | Microsoft Edge TTS |
| **Voice Model** | fil-PH-BlessicaNeural | id-ID-GadisNeural |
| **Speech Quality** | Natural Filipino pronunciation with clear prosody | Natural Indonesian pronunciation with smooth delivery |
| **Current Limitation** | Slightly formal for conversational Taglish | Slightly formal compared to everyday Jakarta speech |

---

## Localization Strategy

| Feature | Philippines | Indonesia |
|---------|-------------|------------|
| **Greeting Style** | "Magandang araw po!" using respectful expressions | "Selamat siang, Bapak/Ibu" with formal addressing |
| **Respectful Language** | po, opo, Sir/Ma'am, Kuya, Ate | Bapak/Ibu, Mas, Mbak |
| **Salary Discussion** | Uses soft and polite phrasing such as "if that's okay po" | Presents salary range first before confirming expectations |
| **Objection Handling** | Empathetic and relationship-oriented communication | Calm, solution-focused conversation style |
| **Fallback Language** | Remains in Filipino or Taglish throughout the interaction | Maintains conversation in Bahasa Indonesia without unexpected English switching |
| **Financial Vocabulary** | English terms such as "salary" and "benefits" are naturally retained | Combines Bahasa terminology (gaji, tunjangan) with common English loanwords |
| **Currency Representation** | PHP 45,000/month | Rp8.000.000 ("8 juta") |
| **Default Speaking Style** | Natural Taglish code-switching | Formal Bahasa with commonly used English terminology |

---

## Cultural Adaptation Comparison

| Cultural Aspect | Philippines Implementation | Indonesia Implementation |
|----------------|-----------------------------|---------------------------|
| **Conversation Style** | Establishes rapport before discussing business | Begins with a respectful greeting before moving into the discussion |
| **Face-Saving Communication** | Avoids direct rejection and suggests alternative options | Offers possible solutions before discussing negative outcomes |
| **Indirect Responses** | Uses phrases such as "Maybe we can explore other options po." | Understands expressions like "Saya pikir-pikir dulu" as a request for additional consideration |
| **Family Considerations** | Recognizes family influence in career decisions | Acknowledges relocation and financial decisions as family-driven |
| **Time Expectations** | More flexible scheduling ("Filipino time") | Greater emphasis on punctuality and scheduled appointments |

---

## Known Limitations

### Native Language Coverage

**Philippines**
- Fast conversational Tagalog may experience reduced transcription quality.
- Regional dialects such as Bisaya and Ilocano have not been evaluated.

**Indonesia**
- Recognition accuracy may decrease for Sundanese and Javanese native speakers.
- Informal Jakarta slang (for example: *gue*, *lu*, *gimana*) is only partially supported.

---

### Compliance Considerations

**Philippines**
- Regulatory disclosures required by BSP and the Insurance Commission have not been implemented.

**Indonesia**
- OJK-specific compliance requirements for financial services are currently outside the implementation scope.

**Production Note**
- Both localized voice assistants should undergo legal and compliance review before deployment in a production environment.

---

## Overall Comparison

| Evaluation Area | Philippines | Indonesia |
|----------------|-------------|------------|
| Voice Recognition | Good | Very Good |
| Text-to-Speech Quality | Good | Good |
| Localization Quality | Very Good | Very Good |
| Code-Switching Support | Moderate | Good |
| Cultural Adaptation | Strong | Strong |
| Production Readiness | Requires Compliance Review | Requires Compliance Review |
"""
Q4 Live Insights — Signal Extractor
=====================================
Analyzes transcript windows to detect actionable signals using Groq (FREE).

Detected signals:
- MISSED_CROSS_SELL: Customer mentions need/product not offered
- COMPLIANCE_GAP: Required disclosure missing, risky promises
- RISING_FRUSTRATION: Escalating negative sentiment
- PAYMENT_DIFFICULTY: Financial hardship indicators
- BUYING_SIGNAL: Strong purchase/engagement interest
- CALLBACK_NEEDED: Customer requests follow-up
- SALARY_ESCALATION: Salary expectations far above range
"""

import json
import os
import time
import logging
from typing import Optional

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

try:
    from groq import Groq
    HAS_GROQ = True
except ImportError:
    HAS_GROQ = False

from dotenv import load_dotenv
load_dotenv()


SIGNAL_EXTRACTION_PROMPT = """Analyze this live call transcript segment between an Agent and Customer.

Transcript (recent window):
---
{transcript}
---

Detect ANY of these signals. Only report signals with CLEAR evidence in the text:

1. MISSED_CROSS_SELL — Customer mentions a need/product/role not being actively offered by agent
2. COMPLIANCE_GAP — Agent makes unauthorized promises, skips disclosures, or shares incorrect info
3. RISING_FRUSTRATION — Customer shows escalating negative sentiment (repeated complaints, raised tone indicators, expressing dissatisfaction)
4. SALARY_ESCALATION — Salary expectations significantly above the posted range
5. BUYING_SIGNAL — Customer shows strong interest, asks about next steps, timelines
6. CALLBACK_NEEDED — Customer requests follow-up or can't continue now
7. ESCALATION_REQUEST — Customer explicitly asks to speak to a human/manager

For each signal detected, respond with valid JSON:
{{
  "signals": [
    {{
      "type": "SIGNAL_TYPE",
      "confidence": 0.0 to 1.0,
      "evidence": "exact quote from transcript",
      "suggestion": "short actionable recommendation for the agent"
    }}
  ]
}}

If no signals are detected, return: {{"signals": []}}

IMPORTANT:
- Only detect signals with CLEAR evidence. Do NOT hallucinate.
- Confidence must reflect how certain you are (>0.8 = very clear, 0.5-0.8 = moderate, <0.5 = weak).
- Keep suggestions under 20 words.
- Return ONLY valid JSON, no other text.
"""


class SignalExtractor:
    """Extracts actionable signals from transcript using Groq (FREE)."""

    def __init__(self):
        self.client = None
        self.extraction_latencies = []

        if HAS_GROQ:
            api_key = os.getenv("GROQ_API_KEY")
            if api_key and not api_key.startswith("gsk_your"):
                self.client = Groq(api_key=api_key)
                logger.info("Signal extractor initialized with Groq (free)")
            else:
                logger.warning("GROQ_API_KEY not set. Using rule-based fallback.")
        else:
            logger.warning("groq not installed. Using rule-based fallback.")

    async def extract_signals(self, transcript_window: str) -> list[dict]:
        """
        Extract signals from a transcript window.
        
        Returns list of signal dicts with type, confidence, evidence, suggestion.
        """
        if not transcript_window.strip():
            return []

        start_time = time.time()

        if self.client:
            signals = await self._extract_with_llm(transcript_window)
        else:
            signals = self._extract_with_rules(transcript_window)

        latency_ms = (time.time() - start_time) * 1000
        self.extraction_latencies.append(latency_ms)

        for signal in signals:
            signal["extraction_latency_ms"] = round(latency_ms, 1)
            signal["extracted_at"] = time.time()

        return signals

    async def _extract_with_llm(self, transcript: str) -> list[dict]:
        """Use Groq LLM for signal extraction."""
        try:
            prompt = SIGNAL_EXTRACTION_PROMPT.format(transcript=transcript)

            response = self.client.chat.completions.create(
                model="llama-3.1-8b-instant",  # Fast model for low latency
                messages=[
                    {"role": "system", "content": "You are a call monitoring AI. Respond only with valid JSON."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.1,
                max_tokens=500,
                response_format={"type": "json_object"},
            )

            content = response.choices[0].message.content
            result = json.loads(content)
            return result.get("signals", [])

        except json.JSONDecodeError as e:
            logger.error(f"JSON parse error: {e}")
            return []
        except Exception as e:
            logger.error(f"LLM extraction error: {e}")
            return self._extract_with_rules(transcript)

    def _extract_with_rules(self, transcript: str) -> list[dict]:
        """Rule-based fallback signal extraction (no API needed)."""
        signals = []
        lower = transcript.lower()

        # Frustration detection
        frustration_indicators = [
            "frustrated", "frustrating", "annoyed", "angry", "waste of time",
            "not being valued", "nobody contacted", "been waiting", "disappointed",
            "ridiculous", "unacceptable", "terrible",
        ]
        frustration_count = sum(1 for ind in frustration_indicators if ind in lower)
        if frustration_count >= 1:
            signals.append({
                "type": "RISING_FRUSTRATION",
                "confidence": min(0.5 + frustration_count * 0.15, 0.95),
                "evidence": next((ind for ind in frustration_indicators if ind in lower), ""),
                "suggestion": "Acknowledge concern, apologize, and offer concrete solution.",
            })

        # Escalation request
        escalation_phrases = [
            "speak to a human", "talk to a person", "real person", "human recruiter",
            "speak to someone", "talk to a manager", "supervisor",
        ]
        if any(phrase in lower for phrase in escalation_phrases):
            signals.append({
                "type": "ESCALATION_REQUEST",
                "confidence": 0.95,
                "evidence": next((p for p in escalation_phrases if p in lower), ""),
                "suggestion": "Transfer to human agent immediately.",
            })

        # Salary escalation
        if any(w in lower for w in ["too low", "much higher", "expecting more", "competing offers", "other companies"]):
            signals.append({
                "type": "SALARY_ESCALATION",
                "confidence": 0.75,
                "evidence": "Salary expectations above range or competing offers mentioned.",
                "suggestion": "Highlight total compensation including benefits and ESOPs.",
            })

        # Cross-sell opportunity
        if any(w in lower for w in ["friend is looking", "my friend", "colleague needs", "another role", "other positions"]):
            signals.append({
                "type": "MISSED_CROSS_SELL",
                "confidence": 0.7,
                "evidence": "Customer mentioned someone else interested in a position.",
                "suggestion": "Offer referral program details and share application link.",
            })

        # Buying signal
        if any(w in lower for w in ["when can i start", "next steps", "when do i hear", "interested", "sounds good", "let's proceed"]):
            signals.append({
                "type": "BUYING_SIGNAL",
                "confidence": 0.7,
                "evidence": "Customer expressed interest in proceeding.",
                "suggestion": "Schedule next interview step immediately.",
            })

        return signals

    def get_latency_stats(self) -> dict:
        """Get signal extraction latency statistics."""
        if not self.extraction_latencies:
            return {"p50": 0, "p95": 0, "max": 0, "count": 0}
        sorted_lat = sorted(self.extraction_latencies)
        n = len(sorted_lat)
        return {
            "p50": round(sorted_lat[int(n * 0.5)], 1),
            "p95": round(sorted_lat[min(int(n * 0.95), n - 1)], 1),
            "max": round(sorted_lat[-1], 1),
            "count": n,
        }

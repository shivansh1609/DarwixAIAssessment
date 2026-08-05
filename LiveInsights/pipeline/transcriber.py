"""
Q4 Live Insights — Streaming Transcriber (FREE — Vosk)
=======================================================


"""

import asyncio
import json
import time
import logging
import os
from typing import Optional

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

try:
    from vosk import Model, KaldiRecognizer
    HAS_VOSK = True
except ImportError:
    HAS_VOSK = False
    logger.warning("vosk not installed. Run: pip install vosk")


class StreamingTranscriber:
    """
    Real-time streaming transcriber using Vosk (FREE, offline).
    
    Accepts audio chunks and emits partial/final transcripts
    with timestamps for latency measurement.
    """

    def __init__(self, model_path: str = None, sample_rate: int = 16000):
        self.sample_rate = sample_rate
        self.recognizer = None
        self.transcript_buffer = []  # Rolling transcript
        self.latencies = []  # ASR latency measurements

        if HAS_VOSK:
            try:
                if model_path and os.path.exists(model_path):
                    model = Model(model_path)
                else:
                    # Auto-download small English model
                    logger.info("Downloading Vosk model (first run only, ~50MB)...")
                    model = Model(lang="en-us")

                self.recognizer = KaldiRecognizer(model, sample_rate)
                self.recognizer.SetWords(True)
                logger.info("Vosk transcriber initialized successfully")
            except Exception as e:
                logger.error(f"Vosk init failed: {e}")
                self.recognizer = None
        else:
            logger.warning("Vosk not available. Using simulated transcription.")

    def process_chunk(self, audio_data: bytes, audio_received_at: float) -> Optional[dict]:
        """
        Process an audio chunk and return transcript if available.
        
        Returns:
            dict with:
                - text: transcribed text
                - is_final: bool
                - timestamp: float
                - asr_latency_ms: float
        """
        if self.recognizer is None:
            return None

        process_start = time.time()

        if self.recognizer.AcceptWaveform(audio_data):
            # Final result for this utterance
            result = json.loads(self.recognizer.Result())
            text = result.get("text", "").strip()
            if text:
                asr_done = time.time()
                latency_ms = (asr_done - audio_received_at) * 1000
                self.latencies.append(latency_ms)

                self.transcript_buffer.append(text)

                return {
                    "text": text,
                    "is_final": True,
                    "timestamp": audio_received_at,
                    "asr_latency_ms": round(latency_ms, 1),
                }
        else:
            # Partial result
            partial = json.loads(self.recognizer.PartialResult())
            text = partial.get("partial", "").strip()
            if text:
                return {
                    "text": text,
                    "is_final": False,
                    "timestamp": audio_received_at,
                    "asr_latency_ms": round((time.time() - audio_received_at) * 1000, 1),
                }

        return None

    def get_full_transcript(self) -> str:
        """Get the full transcript so far."""
        return " ".join(self.transcript_buffer)

    def get_recent_window(self, n_sentences: int = 5) -> str:
        """Get the last N sentences for signal extraction."""
        return " ".join(self.transcript_buffer[-n_sentences:])

    def get_latency_stats(self) -> dict:
        """Get ASR latency statistics."""
        if not self.latencies:
            return {"p50": 0, "p95": 0, "max": 0, "count": 0}

        sorted_lat = sorted(self.latencies)
        n = len(sorted_lat)
        return {
            "p50": round(sorted_lat[int(n * 0.5)], 1),
            "p95": round(sorted_lat[int(n * 0.95)], 1),
            "max": round(sorted_lat[-1], 1),
            "count": n,
        }


class SimulatedTranscriber:
    """
    Simulated transcriber for demo purposes.
    Feeds pre-written transcript segments at realistic intervals.
    """

    # Simulated call transcript (insurance screening call)
    SIMULATED_SEGMENTS = [
        {"time": 0.0, "speaker": "agent", "text": "Hello, thank you for calling. I'm Sarah from TalentBridge. How can I help you today?"},
        {"time": 3.0, "speaker": "customer", "text": "Hi Sarah, I applied for the Senior Software Engineer position. I wanted to follow up on my application."},
        {"time": 7.0, "speaker": "agent", "text": "Great! Let me pull up your application. Could you confirm your name for me?"},
        {"time": 10.0, "speaker": "customer", "text": "Sure, my name is Rahul Verma. I have about 7 years of experience in backend development."},
        {"time": 14.0, "speaker": "agent", "text": "Wonderful, Rahul. 7 years is great experience. What technologies are you currently working with?"},
        {"time": 18.0, "speaker": "customer", "text": "I mainly work with Python and Go. I've built microservices on AWS using Kubernetes. Also have experience with PostgreSQL and Redis."},
        {"time": 24.0, "speaker": "agent", "text": "That aligns well with our tech stack. Now, could you tell me about your current compensation?"},
        {"time": 28.0, "speaker": "customer", "text": "I'm currently at 30 lakhs per annum. But honestly, I was expecting something closer to 55 to 60 lakhs for this role."},
        {"time": 33.0, "speaker": "agent", "text": "I understand. The posted range for this role goes up to 45 lakhs. Let me check what our total compensation package looks like."},
        {"time": 38.0, "speaker": "customer", "text": "That seems quite low for my experience level. I have competing offers from two other companies that are much higher."},
        {"time": 43.0, "speaker": "customer", "text": "Also, I noticed you have a role for DevOps Engineer. My friend is looking for something like that. Does he need to apply separately?"},
        {"time": 48.0, "speaker": "agent", "text": "For the DevOps role, yes, your friend would need to submit a separate application through our website."},
        {"time": 53.0, "speaker": "customer", "text": "I'm getting a bit frustrated honestly. I've been waiting for two weeks since I applied and nobody contacted me until now."},
        {"time": 58.0, "speaker": "customer", "text": "I feel like my time isn't being valued here. Can I please speak to a human recruiter instead?"},
        {"time": 63.0, "speaker": "agent", "text": "I completely understand your frustration, Rahul, and I sincerely apologize for the delay. Let me connect you with our senior recruiter right away."},
    ]

    def __init__(self):
        self.current_index = 0
        self.transcript_buffer = []
        self.latencies = []
        self.start_time = None

    async def stream_segments(self):
        """Yield transcript segments at realistic timing."""
        self.start_time = time.time()

        for segment in self.SIMULATED_SEGMENTS:
            # Wait until the right time
            elapsed = time.time() - self.start_time
            if elapsed < segment["time"]:
                await asyncio.sleep(segment["time"] - elapsed)

            asr_latency = 350  # Simulated 350ms ASR latency
            self.latencies.append(asr_latency)
            self.transcript_buffer.append(segment["text"])

            yield {
                "text": segment["text"],
                "speaker": segment["speaker"],
                "is_final": True,
                "timestamp": segment["time"],
                "asr_latency_ms": asr_latency,
            }

    def get_recent_window(self, n_sentences: int = 5) -> str:
        return " ".join(self.transcript_buffer[-n_sentences:])

    def get_full_transcript(self) -> str:
        return " ".join(self.transcript_buffer)

    def get_latency_stats(self) -> dict:
        if not self.latencies:
            return {"p50": 0, "p95": 0, "max": 0, "count": 0}
        sorted_lat = sorted(self.latencies)
        n = len(sorted_lat)
        return {
            "p50": round(sorted_lat[int(n * 0.5)], 1),
            "p95": round(sorted_lat[min(int(n * 0.95), n - 1)], 1),
            "max": round(sorted_lat[-1], 1),
            "count": n,
        }

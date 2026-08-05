"""
Q4 Live Insights — Audio Streamer
===================================
Reads a recorded call audio file and streams it in real-time chunks
to simulate live audio processing.
"""

import asyncio
import wave
import os
import logging
import time

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


class AudioStreamer:
    """Streams audio in real-time chunks from a file or microphone."""

    def __init__(self, chunk_duration_ms: int = 250):
        self.chunk_duration_ms = chunk_duration_ms
        self.sample_rate = 16000  # Vosk expects 16kHz
        self.channels = 1         # Mono
        self.sample_width = 2     # 16-bit

    def bytes_per_chunk(self) -> int:
        """Calculate bytes per chunk based on duration."""
        samples_per_chunk = int(self.sample_rate * self.chunk_duration_ms / 1000)
        return samples_per_chunk * self.sample_width * self.channels

    async def stream_from_file(self, filepath: str):
        """
        Generator that yields audio chunks at real-time speed.
        
        Yields:
            dict with:
                - audio_data: bytes
                - timestamp: float (seconds from start)
                - chunk_index: int
        """
        if not os.path.exists(filepath):
            logger.error(f"Audio file not found: {filepath}")
            return

        logger.info(f"Streaming audio from: {filepath}")
        logger.info(f"Chunk size: {self.chunk_duration_ms}ms")

        try:
            wf = wave.open(filepath, "rb")
        except Exception as e:
            logger.error(f"Failed to open audio: {e}")
            return

        # Log audio properties
        orig_rate = wf.getframerate()
        orig_channels = wf.getnchannels()
        logger.info(f"Audio: {orig_rate}Hz, {orig_channels}ch, {wf.getnframes()} frames")

        chunk_size = self.bytes_per_chunk()
        chunk_index = 0
        start_time = time.time()

        while True:
            data = wf.readframes(int(self.sample_rate * self.chunk_duration_ms / 1000))
            if not data:
                break

            elapsed = time.time() - start_time
            expected_time = chunk_index * (self.chunk_duration_ms / 1000)

            # Sleep to maintain real-time speed
            if elapsed < expected_time:
                await asyncio.sleep(expected_time - elapsed)

            yield {
                "audio_data": data,
                "timestamp": chunk_index * (self.chunk_duration_ms / 1000),
                "chunk_index": chunk_index,
                "audio_received_at": time.time(),
            }

            chunk_index += 1

        wf.close()
        duration = chunk_index * (self.chunk_duration_ms / 1000)
        logger.info(f"Stream complete: {chunk_index} chunks, {duration:.1f}s duration")

    async def stream_silence(self, duration_seconds: float = 5.0):
        """Stream silence chunks for testing pipeline without audio file."""
        chunk_size = self.bytes_per_chunk()
        total_chunks = int(duration_seconds * 1000 / self.chunk_duration_ms)
        start_time = time.time()

        for i in range(total_chunks):
            await asyncio.sleep(self.chunk_duration_ms / 1000)
            yield {
                "audio_data": b'\x00' * chunk_size,
                "timestamp": i * (self.chunk_duration_ms / 1000),
                "chunk_index": i,
                "audio_received_at": time.time(),
            }


def create_test_audio(output_path: str, duration_seconds: float = 10.0):
    """Create a simple test WAV file with silence for pipeline testing."""
    sample_rate = 16000
    channels = 1
    sample_width = 2
    num_frames = int(sample_rate * duration_seconds)

    os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else ".", exist_ok=True)

    with wave.open(output_path, "wb") as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(sample_width)
        wf.setframerate(sample_rate)
        wf.writeframes(b'\x00' * (num_frames * sample_width * channels))

    logger.info(f"Created test audio: {output_path} ({duration_seconds}s)")


if __name__ == "__main__":
    # Create a test audio file
    test_path = os.path.join(os.path.dirname(__file__), "..", "test_audio", "test_silence.wav")
    create_test_audio(test_path, duration_seconds=30.0)
    print(f"Test audio created at: {test_path}")

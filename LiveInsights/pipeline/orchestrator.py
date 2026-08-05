
import asyncio
import json
import time
import os
import sys
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# Add pipeline dir to path
sys.path.insert(0, os.path.dirname(__file__))

from transcriber import SimulatedTranscriber, StreamingTranscriber
from signal_extractor import SignalExtractor
from nudge_engine import NudgeEngine

try:
    import websockets
    HAS_WS = True
except ImportError:
    HAS_WS = False


class PipelineOrchestrator:
    """
    Orchestrates the real-time analysis pipeline.
    
    Components:
    - Transcriber (Vosk or Simulated)
    - Signal Extractor (Groq or rule-based)
    - Nudge Engine (filtering + prioritization)
    - WebSocket broadcast (to dashboard)
    """

    def __init__(self, mode: str = "simulated"):
        self.mode = mode
        self.signal_extractor = SignalExtractor()
        self.nudge_engine = NudgeEngine(
            confidence_threshold=0.7,
            cooldown_seconds=30.0,
            max_active_nudges=3,
            expiry_seconds=60.0,
        )
        self.ws_clients: set = set()
        self.pipeline_start_time = None
        self.events_log: list[dict] = []  # Full event log for analysis
        self.latency_records: list[dict] = []  # End-to-end latency tracking

        if mode == "simulated":
            self.transcriber = SimulatedTranscriber()
        else:
            self.transcriber = StreamingTranscriber()

    async def broadcast(self, event: dict):
        """Broadcast event to all connected WebSocket clients."""
        if not self.ws_clients:
            return
        message = json.dumps(event, default=str)
        disconnected = set()
        for ws in self.ws_clients:
            try:
                await ws.send(message)
            except Exception:
                disconnected.add(ws)
        self.ws_clients -= disconnected

    async def run_simulated_pipeline(self):
        """Run the pipeline with simulated transcript (no audio file needed)."""
        logger.info("=" * 60)
        logger.info("LIVE INSIGHTS PIPELINE — SIMULATED MODE")
        logger.info("=" * 60)

        self.pipeline_start_time = time.time()
        transcript_window = []

        # Broadcast pipeline start
        await self.broadcast({
            "type": "pipeline_start",
            "timestamp": datetime.now().isoformat(),
            "mode": "simulated",
        })

        async for segment in self.transcriber.stream_segments():
            # Step 1: Transcript received
            t_transcript = time.time()

            await self.broadcast({
                "type": "transcript",
                "speaker": segment.get("speaker", "unknown"),
                "text": segment["text"],
                "timestamp": segment["timestamp"],
                "asr_latency_ms": segment["asr_latency_ms"],
            })

            transcript_window.append(f"{segment.get('speaker', 'unknown').upper()}: {segment['text']}")

            # Log
            self.events_log.append({
                "event": "transcript",
                "time": segment["timestamp"],
                "text": segment["text"],
                "speaker": segment.get("speaker"),
            })

            # Step 2: Signal extraction (every 2 segments or on final)
            if len(transcript_window) >= 2:
                window_text = "\n".join(transcript_window[-5:])  # Last 5 segments
                t_extraction_start = time.time()

                signals = await self.signal_extractor.extract_signals(window_text)
                t_extraction_done = time.time()

                if signals:
                    # Step 3: Nudge generation
                    t_nudge_start = time.time()
                    nudges = self.nudge_engine.process_signals(signals)
                    t_nudge_done = time.time()

                    for nudge in nudges:
                        # Calculate end-to-end latency
                        e2e_latency_ms = (t_nudge_done - t_transcript) * 1000

                        latency_record = {
                            "nudge_id": nudge["nudge_id"],
                            "asr_latency_ms": segment["asr_latency_ms"],
                            "extraction_latency_ms": round((t_extraction_done - t_extraction_start) * 1000, 1),
                            "nudge_gen_latency_ms": round((t_nudge_done - t_nudge_start) * 1000, 1),
                            "e2e_latency_ms": round(e2e_latency_ms, 1),
                        }
                        self.latency_records.append(latency_record)

                        nudge["latency"] = latency_record

                        await self.broadcast({
                            "type": "nudge",
                            **nudge,
                        })

                        self.events_log.append({
                            "event": "nudge",
                            "nudge_id": nudge["nudge_id"],
                            "signal_type": nudge["type"],
                            "message": nudge["message"],
                            "confidence": nudge["confidence"],
                            "latency": latency_record,
                        })

                    # Broadcast signals even if no nudges (for dashboard)
                    for signal in signals:
                        if not any(n["type"] == signal["type"] for n in nudges):
                            await self.broadcast({
                                "type": "signal_suppressed",
                                "signal_type": signal["type"],
                                "confidence": signal.get("confidence", 0),
                                "reason": "filtered by nudge engine",
                            })

        # Pipeline complete
        await self._report_results()

    async def _report_results(self):
        """Generate and broadcast the final analysis report."""
        report = self.get_full_report()

        logger.info("\n" + "=" * 60)
        logger.info("PIPELINE RESULTS")
        logger.info("=" * 60)
        logger.info(f"\nASR Latency: {json.dumps(report['asr_latency'], indent=2)}")
        logger.info(f"Extraction Latency: {json.dumps(report['extraction_latency'], indent=2)}")
        logger.info(f"Nudge Gen Latency: {json.dumps(report['nudge_gen_latency'], indent=2)}")
        logger.info(f"End-to-End Latency: {json.dumps(report['e2e_latency'], indent=2)}")
        logger.info(f"\nNudge Stats: {json.dumps(report['nudge_stats'], indent=2)}")
        logger.info(f"\nTotal Events: {len(self.events_log)}")

        await self.broadcast({
            "type": "pipeline_complete",
            "report": report,
        })

        # Save report to file
        report_path = os.path.join(os.path.dirname(__file__), "..", "latency_report.json")
        with open(report_path, "w") as f:
            json.dump(report, f, indent=2, default=str)
        logger.info(f"Report saved to: {report_path}")

    def get_full_report(self) -> dict:
        """Get comprehensive pipeline report."""
        asr_stats = self.transcriber.get_latency_stats()
        extraction_stats = self.signal_extractor.get_latency_stats()
        nudge_gen_stats = self.nudge_engine.get_latency_stats()
        nudge_stats = self.nudge_engine.get_stats()

        # Calculate E2E latency stats
        e2e_latencies = [r["e2e_latency_ms"] for r in self.latency_records]
        e2e_stats = {"p50": 0, "p95": 0, "max": 0, "count": 0}
        if e2e_latencies:
            sorted_lat = sorted(e2e_latencies)
            n = len(sorted_lat)
            e2e_stats = {
                "p50": round(sorted_lat[int(n * 0.5)], 1),
                "p95": round(sorted_lat[min(int(n * 0.95), n - 1)], 1),
                "max": round(sorted_lat[-1], 1),
                "count": n,
            }

        return {
            "pipeline_mode": self.mode,
            "asr_latency": asr_stats,
            "extraction_latency": extraction_stats,
            "nudge_gen_latency": nudge_gen_stats,
            "e2e_latency": e2e_stats,
            "nudge_stats": nudge_stats,
            "latency_records": self.latency_records,
            "total_transcript_segments": len([e for e in self.events_log if e["event"] == "transcript"]),
            "total_nudges_generated": nudge_stats["total_generated"],
            "total_suppressed": nudge_stats["suppressed"],
        }


async def run_dashboard_server(orchestrator: PipelineOrchestrator, port: int = 8765):
    """Start WebSocket server for dashboard connections."""
    if not HAS_WS:
        logger.warning("websockets not installed. Dashboard disabled.")
        return

    async def handler(websocket, path=None):
        orchestrator.ws_clients.add(websocket)
        logger.info(f"Dashboard client connected ({len(orchestrator.ws_clients)} total)")
        try:
            # Send current state
            await websocket.send(json.dumps({
                "type": "init",
                "active_nudges": [
                    {k: v for k, v in n.items() if k != "created_at" and k != "expires_at"}
                    for n in orchestrator.nudge_engine.get_active_nudges()
                ],
            }, default=str))
            # Keep connection alive
            async for message in websocket:
                data = json.loads(message)
                if data.get("action") == "dismiss":
                    orchestrator.nudge_engine.dismiss_nudge(data.get("nudge_id"))
        except Exception:
            pass
        finally:
            orchestrator.ws_clients.discard(websocket)
            logger.info(f"Dashboard client disconnected")

    server = await websockets.serve(handler, "localhost", port)
    logger.info(f"Dashboard WebSocket server running on ws://localhost:{port}")
    return server


async def main():
    """Main entry point — run pipeline with dashboard."""
    orchestrator = PipelineOrchestrator(mode="simulated")

    # Start WebSocket server
    ws_server = None
    if HAS_WS:
        ws_server = await run_dashboard_server(orchestrator, port=8765)

    logger.info("Open the dashboard at http://localhost:8080 (or see q4_live_insights/dashboard/)")
    logger.info("Connect WebSocket to ws://localhost:8765 for live updates")
    logger.info("")

    # Wait a moment for dashboard to connect
    await asyncio.sleep(2)

    # Run pipeline
    await orchestrator.run_simulated_pipeline()

    # Keep server running for a bit so dashboard can read results
    if ws_server:
        await asyncio.sleep(10)
        ws_server.close()


if __name__ == "__main__":
    asyncio.run(main())

"""
Q4 Live Insights — Nudge Engine
=================================

"""

import time
import hashlib
import logging
from typing import Optional
from collections import defaultdict

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


# Signal type → priority mapping
SIGNAL_PRIORITY = {
    "COMPLIANCE_GAP": "CRITICAL",
    "RISING_FRUSTRATION": "HIGH",
    "ESCALATION_REQUEST": "HIGH",
    "SALARY_ESCALATION": "MEDIUM",
    "MISSED_CROSS_SELL": "MEDIUM",
    "BUYING_SIGNAL": "LOW",
    "CALLBACK_NEEDED": "LOW",
    "PAYMENT_DIFFICULTY": "HIGH",
}

PRIORITY_ORDER = {"CRITICAL": 4, "HIGH": 3, "MEDIUM": 2, "LOW": 1}

# Nudge message templates
NUDGE_TEMPLATES = {
    "COMPLIANCE_GAP": "⚠️ COMPLIANCE: {suggestion}",
    "RISING_FRUSTRATION": "😤 FRUSTRATION: {suggestion}",
    "ESCALATION_REQUEST": "🔴 ESCALATION: Customer wants to speak to a human. Transfer immediately.",
    "SALARY_ESCALATION": "💰 SALARY: {suggestion}",
    "MISSED_CROSS_SELL": "💡 OPPORTUNITY: {suggestion}",
    "BUYING_SIGNAL": "✅ BUYING SIGNAL: {suggestion}",
    "CALLBACK_NEEDED": "📞 CALLBACK: {suggestion}",
    "PAYMENT_DIFFICULTY": "💳 PAYMENT: {suggestion}",
}


class NudgeEngine:
    """
    Manages nudge generation, filtering, and delivery.
    
    Implements:
    - Confidence threshold filtering
    - Cooldown per signal type
    - Duplicate suppression
    - Priority management
    - Active nudge limit
    - Expiry
    """

    def __init__(
        self,
        confidence_threshold: float = 0.7,
        cooldown_seconds: float = 30.0,
        max_active_nudges: int = 3,
        expiry_seconds: float = 60.0,
    ):
        self.confidence_threshold = confidence_threshold
        self.cooldown_seconds = cooldown_seconds
        self.max_active_nudges = max_active_nudges
        self.expiry_seconds = expiry_seconds

        self.active_nudges: list[dict] = []
        self.all_nudges: list[dict] = []  # History
        self.last_signal_time: dict[str, float] = defaultdict(float)  # type → last time
        self.seen_hashes: set[str] = set()  # For dedup
        self.suppressed_count: int = 0
        self.generation_latencies: list[float] = []

    def process_signals(self, signals: list[dict]) -> list[dict]:
        """
        Process extracted signals into nudges.
        
        Applies all filtering rules and returns new nudges to display.
        """
        start_time = time.time()
        new_nudges = []

        # Clean expired nudges first
        self._expire_nudges()

        for signal in signals:
            nudge = self._create_nudge(signal)
            if nudge:
                new_nudges.append(nudge)

        latency_ms = (time.time() - start_time) * 1000
        self.generation_latencies.append(latency_ms)

        return new_nudges

    def _create_nudge(self, signal: dict) -> Optional[dict]:
        """Create a nudge from a signal, applying all filters."""
        signal_type = signal.get("type", "UNKNOWN")
        confidence = signal.get("confidence", 0)
        evidence = signal.get("evidence", "")
        suggestion = signal.get("suggestion", "")

        # Filter 1: Confidence threshold
        if confidence < self.confidence_threshold:
            logger.debug(f"Suppressed {signal_type}: confidence {confidence} < {self.confidence_threshold}")
            self.suppressed_count += 1
            return None

        # Filter 2: Cooldown
        now = time.time()
        last_time = self.last_signal_time.get(signal_type, 0)
        if (now - last_time) < self.cooldown_seconds:
            logger.debug(f"Suppressed {signal_type}: cooldown active ({self.cooldown_seconds}s)")
            self.suppressed_count += 1
            return None

        # Filter 3: Duplicate suppression
        content_hash = hashlib.md5(f"{signal_type}:{evidence}".encode()).hexdigest()
        if content_hash in self.seen_hashes:
            logger.debug(f"Suppressed {signal_type}: duplicate")
            self.suppressed_count += 1
            return None

        # Filter 4: Max active nudges
        if len(self.active_nudges) >= self.max_active_nudges:
            # Remove lowest priority nudge
            self.active_nudges.sort(key=lambda n: PRIORITY_ORDER.get(n["priority"], 0))
            removed = self.active_nudges.pop(0)
            logger.info(f"Evicted nudge: {removed['type']} (priority: {removed['priority']})")

        # Create nudge
        priority = SIGNAL_PRIORITY.get(signal_type, "LOW")
        template = NUDGE_TEMPLATES.get(signal_type, "📋 {suggestion}")
        message = template.format(suggestion=suggestion)

        nudge = {
            "nudge_id": f"N{len(self.all_nudges) + 1:04d}",
            "type": signal_type,
            "priority": priority,
            "priority_order": PRIORITY_ORDER.get(priority, 0),
            "message": message,
            "evidence": evidence,
            "confidence": confidence,
            "created_at": now,
            "expires_at": now + self.expiry_seconds,
            "status": "active",
            "generation_latency_ms": signal.get("extraction_latency_ms", 0),
        }

        # Update state
        self.active_nudges.append(nudge)
        self.all_nudges.append(nudge)
        self.last_signal_time[signal_type] = now
        self.seen_hashes.add(content_hash)

        logger.info(f"🔔 Nudge created: [{priority}] {signal_type} — {message[:80]}")
        return nudge

    def _expire_nudges(self):
        """Remove expired nudges from active list."""
        now = time.time()
        before = len(self.active_nudges)
        self.active_nudges = [n for n in self.active_nudges if n["expires_at"] > now]
        expired = before - len(self.active_nudges)
        if expired > 0:
            logger.debug(f"Expired {expired} nudges")

    def get_active_nudges(self) -> list[dict]:
        """Get currently active (non-expired) nudges, sorted by priority."""
        self._expire_nudges()
        return sorted(
            self.active_nudges,
            key=lambda n: n["priority_order"],
            reverse=True,
        )

    def dismiss_nudge(self, nudge_id: str):
        """Dismiss a specific nudge."""
        self.active_nudges = [n for n in self.active_nudges if n["nudge_id"] != nudge_id]

    def get_stats(self) -> dict:
        """Get nudge engine statistics."""
        return {
            "total_generated": len(self.all_nudges),
            "currently_active": len(self.active_nudges),
            "suppressed": self.suppressed_count,
            "suppression_rate": round(
                self.suppressed_count / max(self.suppressed_count + len(self.all_nudges), 1) * 100, 1
            ),
            "by_type": self._count_by_type(),
            "by_priority": self._count_by_priority(),
        }

    def _count_by_type(self) -> dict:
        counts = defaultdict(int)
        for n in self.all_nudges:
            counts[n["type"]] += 1
        return dict(counts)

    def _count_by_priority(self) -> dict:
        counts = defaultdict(int)
        for n in self.all_nudges:
            counts[n["priority"]] += 1
        return dict(counts)

    def get_latency_stats(self) -> dict:
        if not self.generation_latencies:
            return {"p50": 0, "p95": 0, "max": 0, "count": 0}
        sorted_lat = sorted(self.generation_latencies)
        n = len(sorted_lat)
        return {
            "p50": round(sorted_lat[int(n * 0.5)], 1),
            "p95": round(sorted_lat[min(int(n * 0.95), n - 1)], 1),
            "max": round(sorted_lat[-1], 1),
            "count": n,
        }

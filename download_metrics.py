"""Estimated Ollama layer transfer speed, computed exclusively from /api/pull bytes.

Unlike a network adapter meter, this reports only the selected model layer as
Ollama acknowledges downloaded bytes. It never inspects other network traffic.
"""
from __future__ import annotations
import time
from collections import deque


class PullSpeedMeter:
    """Consume streaming progress events and expose an age-aware transfer speed."""

    def __init__(self, clock=None, window_seconds=8.0, zero_after=3.0):
        self.clock = clock or time.monotonic
        self.window_seconds = window_seconds
        self.zero_after = zero_after
        self.samples = deque()
        self.layer = None
        self.last_bytes = None
        self.last_change = None
        self.phase = "idle"
        self.status = "No download started"
        self.total = None
        self.completed = None

    def observe(self, event: dict):
        now = self.clock()
        self.status = str(event.get("status") or "Working")
        status = self.status.lower()
        total, completed = event.get("total"), event.get("completed")
        if status == "success":
            self.phase = "ready"
        elif "verif" in status or "manifest" in status and "writing" in status or "removing" in status:
            self.phase = "verifying"
        elif isinstance(total, (float, int)) and total > 0 and isinstance(completed, (float, int)) and completed >= 0:
            self.phase = "downloading"
        else:
            self.phase = "preparing"

        if self.phase != "downloading":
            self.samples.clear()
            self.layer = None
            self.last_bytes = None
            self.last_change = None
            return self.snapshot()

        # Each Ollama blob has its own digest. Do not calculate across blobs or
        # across a backwards progress jump, which would inflate throughput.
        layer = event.get("digest") or self.status
        amount = int(completed)
        if layer != self.layer or (self.last_bytes is not None and amount < self.last_bytes):
            self.samples.clear()
            self.layer = layer
            self.last_bytes = None
            self.last_change = None
        if self.last_bytes is None or amount > self.last_bytes:
            self.samples.append((now, amount))
            self.last_change = now
        self.last_bytes = amount
        self.total = int(total)
        self.completed = amount
        self._trim(now)
        return self.snapshot()

    def _trim(self, now):
        # Retain at most one sample just outside the window for a stable slope.
        while len(self.samples) > 2 and self.samples[1][0] < now - self.window_seconds:
            self.samples.popleft()

    def snapshot(self):
        now = self.clock()
        if self.phase != "downloading":
            return {"phase": self.phase, "status": self.status, "speed_bps": None,
                    "idle_seconds": None, "completed": self.completed, "total": self.total}
        self._trim(now)
        idle = max(0., now - self.last_change) if self.last_change is not None else None
        speed = None
        if idle is not None and idle >= self.zero_after:
            speed = 0.0
        elif len(self.samples) >= 2:
            first_t, first_b = self.samples[0]
            last_t, last_b = self.samples[-1]
            if last_t > first_t:
                speed = max(0.0, (last_b - first_b) / (last_t - first_t))
        return {"phase": self.phase, "status": self.status, "speed_bps": speed,
                "idle_seconds": idle, "completed": self.completed, "total": self.total}


def format_transfer_speed(speed_bps):
    """Decimal megabytes per second and megabits per second, or no sample."""
    if speed_bps is None:
        return "— MB/s    ·    — Mbps"
    return f"{speed_bps / 1_000_000:.2f} MB/s    ·    {8 * speed_bps / 1_000_000:.1f} Mbps"

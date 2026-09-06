"""Prompt injection detection via Little Canary (optional dependency)."""

from __future__ import annotations

import asyncio
import os
from dataclasses import dataclass, field
from typing import Any, Literal

DEFAULT_CANARY_MODEL = "qwen2.5:1.5b"
DEFAULT_OLLAMA_URL = "http://localhost:11434"

# Little Canary advisory severity -> ORBIT SecurityEventRecord.severity (1-10).
_SEVERITY_MAP: dict[str, int] = {"high": 9, "medium": 6, "low": 3}

ScanStatus = Literal["ok", "degraded", "unavailable", "error"]


@dataclass(frozen=True)
class InjectionScanResult:
    """Outcome of one injection scan.

    ``status`` distinguishes the three ways a scan can end without a detection:

    - ``ok``          — screening ran; ``detected`` is the real answer.
    - ``degraded``    — screening ran only partially (canary probe or analysis
      failed, e.g. Ollama is down). ``detected`` may still be True from the
      structural layer, but a False here does *not* mean the text is clean.
    - ``unavailable`` — little-canary is not installed; nothing was screened.
    - ``error``       — the detector raised unexpectedly; nothing is asserted.
    """

    detected: bool
    reason: str | None
    status: ScanStatus
    severity: int | None = None
    risk_score: float | None = None
    signals: tuple[str, ...] = field(default_factory=tuple)

    @property
    def screened(self) -> bool:
        """True only when injection screening actually completed."""
        return self.status == "ok"


class PromptInjectionDetector:
    """Wraps Little Canary's ``SecurityPipeline`` in advisory mode.

    ORBIT observes and records; it does not block LLM calls. Advisory mode
    matches that: the pipeline never blocks, it reports what it found so the
    guardrail can write a ``SecurityEventRecord``.

    Requires ``little-canary>=0.3.3`` for ``PipelineVerdict.degraded``, which is
    how we tell "screened and clean" apart from "could not screen".
    """

    def __init__(
        self,
        canary_model: str | None = None,
        ollama_url: str | None = None,
        pipeline: Any | None = None,
    ) -> None:
        self._canary_model: str = (
            canary_model if canary_model else os.getenv("ORBIT_CANARY_MODEL", DEFAULT_CANARY_MODEL)
        )
        self._ollama_url: str = (
            ollama_url if ollama_url else os.getenv("ORBIT_OLLAMA_URL", DEFAULT_OLLAMA_URL)
        )

        if pipeline is not None:
            self._pipeline: Any | None = pipeline
            self._available = True
            return

        try:
            from little_canary import SecurityPipeline  # type: ignore[import-not-found]

            self._pipeline = SecurityPipeline(
                canary_model=self._canary_model,
                ollama_url=self._ollama_url,
                mode="advisory",
            )
            self._available = True
        except ImportError:
            self._pipeline = None
            self._available = False

    async def scan(self, text: str) -> tuple[bool, str | None]:
        """Scan text for prompt injection. Returns (is_injection, reason).

        If little-canary is not installed, returns (False, None) and skips
        the check. Install it with: pip install 'orbit[security]'

        A (False, None) result also occurs when screening could not complete —
        use :meth:`scan_detailed` when the caller needs to tell those apart.
        """
        result = await self.scan_detailed(text)
        return result.detected, result.reason if result.detected else None

    async def scan_detailed(self, text: str) -> InjectionScanResult:
        """Scan text and return the full result, including screening status."""
        if not self._available or self._pipeline is None:
            return InjectionScanResult(
                detected=False,
                reason=None,
                status="unavailable",
            )

        try:
            # SecurityPipeline.check() is synchronous and does blocking HTTP to
            # Ollama, so keep it off the event loop.
            verdict = await asyncio.to_thread(self._pipeline.check, text)
        except Exception as exc:  # pragma: no cover - defensive
            return InjectionScanResult(
                detected=False,
                reason=f"Little Canary screening failed: {exc}",
                status="error",
            )

        return self._to_result(verdict)

    def _to_result(self, verdict: Any) -> InjectionScanResult:
        advisory = verdict.advisory
        flagged = advisory is not None and advisory.flagged
        degraded = bool(verdict.degraded)

        signals = tuple(advisory.signals) if flagged and advisory.signals else ()
        severity = _SEVERITY_MAP.get(advisory.severity, 6) if flagged else None
        status: ScanStatus = "degraded" if degraded else "ok"

        if flagged:
            reason = advisory.message or "Little Canary flagged a prompt injection attempt."
            if degraded:
                reason = f"{reason} (partial screening: {verdict.summary})"
            return InjectionScanResult(
                detected=True,
                reason=reason,
                status=status,
                severity=severity,
                risk_score=verdict.canary_risk_score,
                signals=signals,
            )

        if degraded:
            return InjectionScanResult(
                detected=False,
                reason=f"Little Canary screening incomplete: {verdict.summary}",
                status="degraded",
                risk_score=verdict.canary_risk_score,
            )

        return InjectionScanResult(
            detected=False,
            reason=None,
            status="ok",
            risk_score=verdict.canary_risk_score,
        )

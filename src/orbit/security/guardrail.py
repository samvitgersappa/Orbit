from datetime import UTC, datetime

from orbit.database.models import SecurityEventRecord
from orbit.database.session import AsyncSessionLocal
from orbit.security.injection import PromptInjectionDetector
from orbit.security.ollama_guard import LLAMA_GUARD_ERROR_PREFIX, LlamaGuard


class SecurityGuard:
    def __init__(self):
        self.injection_detector = PromptInjectionDetector()
        self.llama_guard = LlamaGuard()

    async def close(self) -> None:
        """Release resources (the Llama Guard HTTP client)."""
        await self.llama_guard.close()

    async def _record_event(
        self,
        run_id: int,
        direction: str,
        detector: str,
        risk_type: str,
        severity: int,
        details: str,
        owasp_category: str | None = None,
    ):
        async with AsyncSessionLocal() as session:
            event = SecurityEventRecord(
                run_id=run_id,
                direction=direction,
                detector=detector,
                risk_type=risk_type,
                severity=severity,
                details={"reason": details},
                owasp_category=owasp_category,
                created_at=datetime.now(UTC),
            )
            session.add(event)
            await session.commit()

    async def _record_screening_degraded(
        self, run_id: int, direction: str, detector: str, details: str
    ) -> None:
        """Record that screening could not complete.

        Deliberately not an OWASP-tagged finding: it reflects detector
        availability, not a detected risk, so it must not inflate the OWASP
        category buckets or the security-findings metric.
        """
        await self._record_event(
            run_id=run_id,
            direction=direction,
            detector=detector,
            risk_type="screening_degraded",
            severity=3,
            details=details,
            owasp_category=None,
        )

    async def scan_input(self, run_id: int, text: str):
        # 1. Prompt Injection
        injection = await self.injection_detector.scan_detailed(text)
        if injection.detected:
            await self._record_event(
                run_id=run_id,
                direction="input",
                detector="little_canary",
                risk_type="prompt_injection",
                severity=injection.severity or 9,
                details=injection.reason or "Detected prompt injection attempt",
                owasp_category="LLM01: Prompt Injection",
            )
        if injection.status in ("degraded", "unavailable", "error"):
            # Screening did not complete. Recorded independently of the
            # detection above — a structural hit does not mean the behavioral
            # layer ran, and the trace should not imply it did.
            await self._record_screening_degraded(
                run_id=run_id,
                direction="input",
                detector="little_canary",
                details=injection.reason
                or (
                    "Little Canary is unavailable; install the orbit[security] extra to enable screening."
                    if injection.status == "unavailable"
                    else "Injection screening did not complete"
                ),
            )

        # 2. Content Safety (Toxicity/Unsafe)
        is_unsafe, detail = await self.llama_guard.scan(role="User", text=text)
        if is_unsafe:
            await self._record_event(
                run_id=run_id,
                direction="input",
                detector="llama_guard3",
                risk_type="unsafe_content",
                severity=7,
                details=f"Unsafe categories: {detail}",
                owasp_category="LLM07: Insecure Plugin Design / Unsafe Content",
            )
        elif detail and detail.startswith(LLAMA_GUARD_ERROR_PREFIX):
            await self._record_screening_degraded(
                run_id=run_id,
                direction="input",
                detector="llama_guard3",
                details=detail,
            )

    async def scan_output(self, run_id: int, text: str):
        # Content Safety (Toxicity/Unsafe) for output
        is_unsafe, detail = await self.llama_guard.scan(role="Agent", text=text)
        if is_unsafe:
            await self._record_event(
                run_id=run_id,
                direction="output",
                detector="llama_guard3",
                risk_type="unsafe_content",
                severity=8,
                details=f"Unsafe categories: {detail}",
                owasp_category="LLM06: Sensitive Information Disclosure",
            )
        elif detail and detail.startswith(LLAMA_GUARD_ERROR_PREFIX):
            await self._record_screening_degraded(
                run_id=run_id,
                direction="output",
                detector="llama_guard3",
                details=detail,
            )

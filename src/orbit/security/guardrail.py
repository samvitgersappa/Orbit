from typing import List, Optional
from datetime import datetime, timezone
from orbit.database.models import SecurityEventRecord
from orbit.database.session import AsyncSessionLocal
from orbit.security.injection import PromptInjectionDetector
from orbit.security.ollama_guard import LlamaGuard

class SecurityGuard:
    def __init__(self):
        self.injection_detector = PromptInjectionDetector()
        self.llama_guard = LlamaGuard()

    async def _record_event(
        self, 
        run_id: int, 
        direction: str, 
        detector: str, 
        risk_type: str, 
        severity: int, 
        details: str,
        owasp_category: Optional[str] = None
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
                created_at=datetime.now(timezone.utc)
            )
            session.add(event)
            await session.commit()

    async def scan_input(self, run_id: int, text: str):
        # 1. Prompt Injection
        is_inj, reason = await self.injection_detector.scan(text)
        if is_inj:
            await self._record_event(
                run_id=run_id,
                direction="input",
                detector="little_canary",
                risk_type="prompt_injection",
                severity=9,
                details=reason or "Detected prompt injection attempt",
                owasp_category="LLM01: Prompt Injection"
            )

        # 2. Content Safety (Toxicity/Unsafe)
        is_unsafe, categories = await self.llama_guard.scan(role="User", text=text)
        if is_unsafe:
            await self._record_event(
                run_id=run_id,
                direction="input",
                detector="llama_guard3",
                risk_type="unsafe_content",
                severity=7,
                details=f"Unsafe categories: {categories}",
                owasp_category="LLM07: Insecure Plugin Design / Unsafe Content"
            )

    async def scan_output(self, run_id: int, text: str):
        # Content Safety (Toxicity/Unsafe) for output
        is_unsafe, categories = await self.llama_guard.scan(role="Agent", text=text)
        if is_unsafe:
            await self._record_event(
                run_id=run_id,
                direction="output",
                detector="llama_guard3",
                risk_type="unsafe_content",
                severity=8,
                details=f"Unsafe categories: {categories}",
                owasp_category="LLM06: Sensitive Information Disclosure"
            )

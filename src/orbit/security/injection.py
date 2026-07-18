"""Prompt injection detection via Little Canary (optional dependency)."""

from __future__ import annotations


class PromptInjectionDetector:
    def __init__(self) -> None:
        try:
            from little_canary import CanaryDetector  # type: ignore

            self._detector = CanaryDetector()
            self._available = True
        except ImportError:
            self._detector = None
            self._available = False

    async def scan(self, text: str) -> tuple[bool, str | None]:
        """Scan text for prompt injection. Returns (is_injection, reason).

        If little-canary is not installed, returns (False, None) and skips
        the check. Install it with: pip install little-canary
        """
        if not self._available or self._detector is None:
            return False, None

        is_injection = self._detector.is_injection(text)
        if is_injection:
            return True, "Little Canary detected a prompt injection attempt."
        return False, None

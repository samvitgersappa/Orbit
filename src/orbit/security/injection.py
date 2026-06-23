from typing import Tuple, Optional
from little_canary import CanaryDetector

class PromptInjectionDetector:
    def __init__(self):
        # Initializes the local canary detector
        self.detector = CanaryDetector()

    async def scan(self, text: str) -> Tuple[bool, Optional[str]]:
        """
        Scan text for prompt injection.
        Returns (is_injection, reason)
        """
        is_injection = self.detector.is_injection(text)
        if is_injection:
            return True, "Little Canary detected a prompt injection."
        return False, None

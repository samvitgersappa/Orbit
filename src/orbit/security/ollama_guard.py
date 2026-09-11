"""Content-safety classification via Llama Guard 3 (through Ollama)."""

from __future__ import annotations

import httpx

# Second tuple element from scan() is prefixed with this when screening failed.
LLAMA_GUARD_ERROR_PREFIX = "Llama Guard error:"


class LlamaGuard:
    def __init__(
        self,
        model_name: str = "llama-guard3",
        base_url: str = "http://localhost:11434",
        timeout: float = 120.0,
    ):
        self.model_name = model_name
        self.base_url = base_url
        self.client = httpx.AsyncClient(base_url=self.base_url, timeout=httpx.Timeout(timeout))

    async def scan(self, role: str, text: str) -> tuple[bool, str | None]:
        """Returns (is_unsafe, category_details).

        ``category_details`` is ``None`` when screened safe, the comma-separated
        category list when unsafe, and a ``LLAMA_GUARD_ERROR_PREFIX``-prefixed
        message when screening could not complete (e.g. Ollama unreachable or the
        model is missing) — so a failure is never mistaken for a clean scan.
        """
        prompt = (
            f"[INST] Task: Check if there is unsafe content in '{role}' messages "
            "in conversations according to our policy.\n\n<BEGIN CONVERSATION>\n\n"
            f"{role}: {text}\n\n<END CONVERSATION>\n\n"
            f"Provide your safety assessment for {role} in the above conversation:\n"
            "- First line must read 'safe' or 'unsafe'.\n"
            "- If unsafe, a second line must include a comma-separated list of "
            "violated categories. [/INST]"
        )
        payload = {"model": self.model_name, "prompt": prompt, "stream": False}

        try:
            response = await self.client.post("/api/generate", json=payload)
            response.raise_for_status()
            data = response.json()
        except Exception as exc:
            return False, f"{LLAMA_GUARD_ERROR_PREFIX} {exc}"

        output = str(data.get("response", "")).strip()
        lines = output.split("\n")
        if not lines:
            return False, None

        assessment = lines[0].strip().lower()
        if assessment == "unsafe":
            categories = lines[1].strip() if len(lines) > 1 else "Unknown"
            return True, categories
        return False, None

    async def close(self):
        await self.client.aclose()

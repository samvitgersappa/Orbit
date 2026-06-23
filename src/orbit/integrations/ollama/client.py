import httpx
from typing import AsyncGenerator, Dict, Any, List, Optional

class OllamaClient:
    def __init__(self, base_url: str = "http://localhost:11434"):
        self.base_url = base_url
        self.client = httpx.AsyncClient(base_url=self.base_url)

    async def list_models(self) -> List[Dict[str, Any]]:
        response = await self.client.get("/api/tags")
        response.raise_for_status()
        return response.json().get("models", [])

    async def generate(self, model: str, prompt: str, **kwargs) -> Dict[str, Any]:
        payload = {"model": model, "prompt": prompt, "stream": False, **kwargs}
        response = await self.client.post("/api/generate", json=payload)
        response.raise_for_status()
        return response.json()

    async def chat(self, model: str, messages: List[Dict[str, str]], **kwargs) -> Dict[str, Any]:
        payload = {"model": model, "messages": messages, "stream": False, **kwargs}
        response = await self.client.post("/api/chat", json=payload)
        response.raise_for_status()
        return response.json()

    async def health_check(self) -> bool:
        try:
            response = await self.client.get("/")
            return response.status_code == 200
        except httpx.RequestError:
            return False

    async def close(self):
        await self.client.aclose()

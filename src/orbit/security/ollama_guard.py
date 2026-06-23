import httpx
from typing import Tuple, Optional

class LlamaGuard:
    def __init__(self, model_name: str = "llama-guard3", base_url: str = "http://localhost:11434"):
        self.model_name = model_name
        self.base_url = base_url
        self.client = httpx.AsyncClient(base_url=self.base_url)

    async def scan(self, role: str, text: str) -> Tuple[bool, Optional[str]]:
        """
        Returns (is_unsafe, category_details).
        LlamaGuard expects prompts in a specific format, but Ollama handles some of it.
        We will pass a simple conversation.
        """
        prompt = f"[INST] Task: Check if there is unsafe content in '{role}' messages in conversations according to our policy.\n\n<BEGIN CONVERSATION>\n\n{role}: {text}\n\n<END CONVERSATION>\n\nProvide your safety assessment for {role} in the above conversation:\n- First line must read 'safe' or 'unsafe'.\n- If unsafe, a second line must include a comma-separated list of violated categories. [/INST]"
        
        payload = {"model": self.model_name, "prompt": prompt, "stream": False}
        
        try:
            response = await self.client.post("/api/generate", json=payload)
            response.raise_for_status()
            data = response.json()
            output = data.get("response", "").strip()
            
            lines = output.split('\n')
            if not lines:
                return False, None
                
            assessment = lines[0].strip().lower()
            if assessment == "unsafe":
                categories = lines[1].strip() if len(lines) > 1 else "Unknown"
                return True, categories
            return False, None
        except Exception as e:
            # If model is missing or error occurs, default to safe and maybe log it
            return False, f"Error calling Llama Guard: {str(e)}"
            
    async def close(self):
        await self.client.aclose()

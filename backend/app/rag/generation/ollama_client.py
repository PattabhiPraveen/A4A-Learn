import httpx

from app.core.config import settings


class OllamaClient:

    def __init__(self):
        self.base_url = settings.OLLAMA_BASE_URL.rstrip("/")
        self.model = settings.OLLAMA_MODEL

    def generate(self, prompt: str) -> str:

        if not prompt.strip():
            raise ValueError("Prompt cannot be empty.")

        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.1,
                "top_p": 0.9,
            },
        }

        try:
            response = httpx.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=120.0,
            )

            response.raise_for_status()

        except httpx.ConnectError as exc:
            raise RuntimeError(
                "Unable to connect to local Ollama service."
            ) from exc

        except httpx.HTTPError as exc:
            raise RuntimeError(
                f"Ollama generation failed: {exc}"
            ) from exc

        data = response.json()

        answer = data.get("response", "").strip()

        if not answer:
            raise RuntimeError(
                "Ollama returned an empty response."
            )

        return answer
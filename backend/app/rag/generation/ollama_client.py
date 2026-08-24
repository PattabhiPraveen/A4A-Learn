import httpx

from app.core.config import settings


class OllamaClient:

    def __init__(self):
        self.base_url = settings.OLLAMA_BASE_URL
        self.model = settings.OLLAMA_MODEL

    def generate(
        self,
        prompt: str,
    ) -> str:

        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.2,
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
                "Unable to connect to Ollama. "
                "Make sure Ollama is running."
            ) from exc

        except httpx.HTTPError as exc:
            raise RuntimeError(
                f"Ollama request failed: {exc}"
            ) from exc

        data = response.json()

        return data.get(
            "response",
            "",
        ).strip()
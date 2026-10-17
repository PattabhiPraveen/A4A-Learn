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
            # Direct connection to Ollama.
            # trust_env=False prevents HTTPX from using
            # Windows proxy/environment variables.
            with httpx.Client(
                timeout=httpx.Timeout(
                    connect=10.0,
                    read=120.0,
                    write=30.0,
                    pool=10.0,
                ),
                trust_env=False,
            ) as client:

                response = client.post(
                    f"{self.base_url}/api/generate",
                    json=payload,
                )

                response.raise_for_status()

        except httpx.ConnectError as exc:
            raise RuntimeError(
                f"Unable to connect to Ollama at {self.base_url}."
            ) from exc

        except httpx.TimeoutException as exc:
            raise RuntimeError(
                f"Ollama request timed out at {self.base_url}."
            ) from exc

        except httpx.HTTPStatusError as exc:
            raise RuntimeError(
                f"Ollama returned HTTP {exc.response.status_code}: "
                f"{exc.response.text[:500]}"
            ) from exc

        except httpx.HTTPError as exc:
            raise RuntimeError(
                f"Ollama HTTP request failed: {exc}"
            ) from exc

        try:
            data = response.json()

        except ValueError as exc:
            raise RuntimeError(
                "Ollama returned invalid JSON."
            ) from exc

        answer = data.get("response", "").strip()

        if not answer:
            raise RuntimeError(
                "Ollama returned an empty response."
            )

        return answer
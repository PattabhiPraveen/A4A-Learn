from urllib.parse import urlparse

from app.core.config import settings
from app.rag.web.models import (
    TrustedWebEvidence,
    WebSearchResult,
)


class WebSourcePolicy:
    """
    Enforce the allowlist for external learning sources.

    External content must never become trusted merely
    because a search provider returned it.
    """

    def __init__(
        self,
        allowed_domains: str | None = None,
    ):
        configured_domains = (
            allowed_domains
            if allowed_domains is not None
            else settings.A4A_WEB_ALLOWED_DOMAINS
        )

        self.allowed_domains = {
            domain.strip().lower().rstrip(".")
            for domain in configured_domains.split(",")
            if domain.strip()
        }

    @staticmethod
    def _normalize_hostname(
        url: str,
    ) -> str:
        hostname = (
            urlparse(url)
            .hostname
        )

        if not hostname:
            return ""

        return (
            hostname
            .lower()
            .rstrip(".")
        )

    def is_allowed(
        self,
        url: str,
    ) -> bool:
        hostname = self._normalize_hostname(
            url
        )

        if not hostname:
            return False

        return any(
            hostname == domain
            or hostname.endswith(
                f".{domain}"
            )
            for domain in self.allowed_domains
        )

    def approve(
        self,
        result: WebSearchResult,
    ) -> TrustedWebEvidence | None:
        url = str(result.url)

        if not self.is_allowed(url):
            return None

        hostname = self._normalize_hostname(
            url
        )

        return TrustedWebEvidence(
            title=result.title.strip(),
            url=result.url,
            domain=hostname,
            content=result.snippet.strip(),
        )
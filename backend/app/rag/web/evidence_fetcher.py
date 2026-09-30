import ipaddress
import socket
from urllib.parse import urljoin, urlparse

import httpx
from lxml import html

from app.core.config import settings
from app.rag.web.models import (
    FetchedWebDocument,
    TrustedWebEvidence,
)
from app.rag.web.source_policy import (
    WebSourcePolicy,
)


class WebEvidenceFetchError(RuntimeError):
    """
    Base exception for governed external evidence
    acquisition failures.
    """


class UnsafeWebDestinationError(
    WebEvidenceFetchError
):
    """
    Raised when an external destination fails the
    outbound web security policy.
    """


class WebEvidenceFetcher:
    """
    Fetch approved external learning evidence.

    Responsibilities:
    - HTTPS only
    - no URL credentials
    - approved-domain enforcement
    - public-IP destination validation
    - redirect revalidation
    - response-size boundary
    - HTML/XHTML only
    - removal of non-learning page elements
    - sanitized text extraction

    Important:
    This component acquires and sanitizes the complete
    bounded HTTP document. It does NOT decide which
    portion should be supplied to the LLM.

    Query-aware evidence selection is handled separately
    by EvidenceSelector.
    """

    REDIRECT_STATUS_CODES = {
        301,
        302,
        303,
        307,
        308,
    }

    ALLOWED_CONTENT_TYPES = {
        "text/html",
        "application/xhtml+xml",
    }

    def __init__(
        self,
        source_policy: WebSourcePolicy | None = None,
    ):
        self.source_policy = (
            source_policy
            or WebSourcePolicy(
                settings.A4A_WEB_ALLOWED_DOMAINS
            )
        )

    def _validate_url(
        self,
        url: str,
    ) -> str:
        """
        Validate an outbound evidence URL before making
        a network request.

        Every redirect destination must pass through this
        validation independently.
        """

        parsed = urlparse(
            url
        )

        if parsed.scheme.lower() != "https":
            raise UnsafeWebDestinationError(
                "External evidence must use HTTPS."
            )

        if (
            parsed.username is not None
            or parsed.password is not None
        ):
            raise UnsafeWebDestinationError(
                "External evidence URL credentials are "
                "not permitted."
            )

        hostname = (
            parsed.hostname
            or ""
        ).lower().rstrip(".")

        if not hostname:
            raise UnsafeWebDestinationError(
                "External evidence URL did not provide "
                "a hostname."
            )

        # WebSourcePolicy expects a complete URL because
        # it extracts the hostname internally using
        # urlparse().
        if not self.source_policy.is_allowed(
            url
        ):
            raise UnsafeWebDestinationError(
                "External evidence destination is not "
                "approved."
            )

        try:
            address_info = socket.getaddrinfo(
                hostname,
                443,
                type=socket.SOCK_STREAM,
            )
        except socket.gaierror as exc:
            raise UnsafeWebDestinationError(
                "External evidence hostname could not "
                "be resolved."
            ) from exc

        if not address_info:
            raise UnsafeWebDestinationError(
                "External evidence hostname did not "
                "resolve to an address."
            )

        for address in address_info:
            sockaddr = address[4]

            if not sockaddr:
                raise UnsafeWebDestinationError(
                    "External evidence hostname returned "
                    "an invalid network address."
                )

            raw_ip = sockaddr[0]

            try:
                ip_address = ipaddress.ip_address(
                    raw_ip
                )
            except ValueError as exc:
                raise UnsafeWebDestinationError(
                    "External evidence hostname returned "
                    "an invalid IP address."
                ) from exc

            # Reject loopback, private, link-local,
            # multicast, reserved, unspecified and other
            # non-global destinations.
            if not ip_address.is_global:
                raise UnsafeWebDestinationError(
                    "External evidence destination did "
                    "not resolve exclusively to public "
                    "IP addresses."
                )

        return url

    @staticmethod
    def _extract_text(
        body: bytes,
    ) -> str:
        """
        Extract readable text from HTML while removing
        common non-learning elements.

        External HTML remains untrusted data even after
        this sanitization step.
        """

        try:
            document = html.fromstring(
                body
            )
        except (
            ValueError,
            TypeError,
            html.etree.ParserError,
        ) as exc:
            raise WebEvidenceFetchError(
                "External evidence HTML could not be "
                "parsed."
            ) from exc

        removable_elements = (
            "script",
            "style",
            "noscript",
            "svg",
            "nav",
            "footer",
            "header",
            "form",
        )

        for element_name in removable_elements:
            for element in document.xpath(
                f"//{element_name}"
            ):
                parent = element.getparent()

                if parent is not None:
                    parent.remove(
                        element
                    )

        text_parts = [
            part.strip()
            for part in document.itertext()
            if part.strip()
        ]

        cleaned_text = " ".join(
            text_parts
        )

        # Normalize repeated whitespace produced by
        # HTML layout and formatting.
        cleaned_text = " ".join(
            cleaned_text.split()
        )

        if not cleaned_text:
            raise WebEvidenceFetchError(
                "External evidence page did not contain "
                "usable text."
            )

        return cleaned_text

    def fetch(
        self,
        evidence: TrustedWebEvidence,
    ) -> FetchedWebDocument:
        """
        Fetch and sanitize an approved external page.

        The HTTP response remains bounded by
        A4A_WEB_MAX_CONTENT_BYTES.

        The sanitized document is intentionally NOT
        truncated to 5,000 characters here. EvidenceSelector
        subsequently chooses a query-relevant bounded window
        before anything is supplied to the LLM.
        """

        current_url = str(
            evidence.url
        )

        redirect_count = 0

        while True:
            self._validate_url(
                current_url
            )

            try:
                with httpx.Client(
                    follow_redirects=False,
                    timeout=(
                        settings
                        .A4A_WEB_TIMEOUT_SECONDS
                    ),
                    headers={
                        "User-Agent": (
                            "A4A-Learn/"
                            f"{settings.APP_VERSION}"
                        ),
                        "Accept": (
                            "text/html,"
                            "application/xhtml+xml"
                        ),
                    },
                ) as client:
                    response = client.get(
                        current_url
                    )

            except httpx.TimeoutException as exc:
                raise WebEvidenceFetchError(
                    "External evidence request timed out."
                ) from exc

            except httpx.HTTPError as exc:
                raise WebEvidenceFetchError(
                    "External evidence request failed."
                ) from exc

            if (
                response.status_code
                in self.REDIRECT_STATUS_CODES
            ):
                location = response.headers.get(
                    "location"
                )

                if not location:
                    raise WebEvidenceFetchError(
                        "External evidence redirect did "
                        "not provide a destination."
                    )

                redirect_count += 1

                if (
                    redirect_count
                    > settings.A4A_WEB_MAX_REDIRECTS
                ):
                    raise WebEvidenceFetchError(
                        "External evidence exceeded the "
                        "maximum redirect limit."
                    )

                next_url = urljoin(
                    current_url,
                    location,
                )

                # The next loop iteration revalidates:
                # - HTTPS
                # - credentials
                # - allowlist
                # - DNS
                # - public IPs
                current_url = next_url

                continue

            try:
                response.raise_for_status()
            except httpx.HTTPStatusError as exc:
                raise WebEvidenceFetchError(
                    "External evidence returned an "
                    "unsuccessful HTTP status."
                ) from exc

            raw_content_type = (
                response.headers.get(
                    "content-type",
                    ""
                )
            )

            content_type = (
                raw_content_type
                .split(";", 1)[0]
                .strip()
                .lower()
            )

            if (
                content_type
                not in self.ALLOWED_CONTENT_TYPES
            ):
                raise WebEvidenceFetchError(
                    "External evidence returned an "
                    "unsupported content type."
                )

            body = response.content

            if (
                len(body)
                > settings.A4A_WEB_MAX_CONTENT_BYTES
            ):
                raise WebEvidenceFetchError(
                    "External evidence exceeded the "
                    "maximum permitted response size."
                )

            clean_text = self._extract_text(
                body
            ).strip()

            if not clean_text:
                raise WebEvidenceFetchError(
                    "External evidence page did not "
                    "contain usable text."
                )

            final_hostname = (
                urlparse(
                    current_url
                ).hostname
                or ""
            ).lower().rstrip(".")

            return FetchedWebDocument(
                title=evidence.title,
                url=current_url,
                domain=final_hostname,
                content=clean_text,
            )
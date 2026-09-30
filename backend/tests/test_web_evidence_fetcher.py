import socket

import httpx
import pytest

from app.rag.web.evidence_fetcher import (
    UnsafeWebDestinationError,
    WebEvidenceFetchError,
    WebEvidenceFetcher,
)
from app.rag.web.models import TrustedWebEvidence
from app.rag.web.source_policy import WebSourcePolicy


def make_evidence(
    url: str = "https://docs.python.org/3/tutorial/",
) -> TrustedWebEvidence:
    return TrustedWebEvidence(
        title="Python Tutorial",
        url=url,
        domain="docs.python.org",
        content="Search result snippet.",
    )


def public_dns(
    *args,
    **kwargs,
):
    """
    Simulate a trusted hostname resolving to a
    globally routable address.

    No real DNS request is made.
    """

    return [
        (
            socket.AF_INET,
            socket.SOCK_STREAM,
            6,
            "",
            ("93.184.216.34", 443),
        )
    ]


class FakeClient:
    """
    Minimal httpx.Client replacement.

    Allows the fetcher to be tested without making
    any real Internet requests.
    """

    responses = []
    requested_urls = []

    def __init__(
        self,
        *args,
        **kwargs,
    ):
        pass

    def __enter__(self):
        return self

    def __exit__(
        self,
        exc_type,
        exc_value,
        traceback,
    ):
        return False

    def get(
        self,
        url,
    ):
        self.__class__.requested_urls.append(
            str(url)
        )

        if not self.__class__.responses:
            raise AssertionError(
                "No fake HTTP response configured."
            )

        response = (
            self.__class__.responses.pop(0)
        )

        return response


def make_response(
    status_code: int = 200,
    *,
    url: str = (
        "https://docs.python.org/3/tutorial/"
    ),
    content: bytes = (
        b"<html><body>"
        b"<main>Python tutorial</main>"
        b"</body></html>"
    ),
    content_type: str = "text/html",
    headers: dict | None = None,
) -> httpx.Response:
    request = httpx.Request(
        "GET",
        url,
    )

    response_headers = {
        "content-type": content_type,
    }

    if headers:
        response_headers.update(
            headers
        )

    return httpx.Response(
        status_code,
        request=request,
        headers=response_headers,
        content=content,
    )


@pytest.fixture(autouse=True)
def reset_fake_client():
    FakeClient.responses = []
    FakeClient.requested_urls = []

    yield

    FakeClient.responses = []
    FakeClient.requested_urls = []


def test_http_url_is_rejected():
    fetcher = WebEvidenceFetcher(
        source_policy=WebSourcePolicy(
            "docs.python.org"
        )
    )

    with pytest.raises(
        UnsafeWebDestinationError
    ):
        fetcher._validate_url(
            "http://docs.python.org/3/tutorial/"
        )


def test_unapproved_domain_is_rejected():
    fetcher = WebEvidenceFetcher(
        source_policy=WebSourcePolicy(
            "docs.python.org"
        )
    )

    with pytest.raises(
        UnsafeWebDestinationError
    ):
        fetcher._validate_url(
            "https://example.com/python"
        )


def test_url_credentials_are_rejected():
    fetcher = WebEvidenceFetcher(
        source_policy=WebSourcePolicy(
            "docs.python.org"
        )
    )

    with pytest.raises(
        UnsafeWebDestinationError
    ):
        fetcher._validate_url(
            "https://user:pass@docs.python.org/"
        )


def test_private_ipv4_destination_is_rejected(
    monkeypatch,
):
    def private_dns(
        *args,
        **kwargs,
    ):
        return [
            (
                socket.AF_INET,
                socket.SOCK_STREAM,
                6,
                "",
                ("10.0.0.10", 443),
            )
        ]

    monkeypatch.setattr(
        socket,
        "getaddrinfo",
        private_dns,
    )

    fetcher = WebEvidenceFetcher(
        source_policy=WebSourcePolicy(
            "docs.python.org"
        )
    )

    with pytest.raises(
        UnsafeWebDestinationError
    ):
        fetcher._validate_url(
            "https://docs.python.org/"
        )


def test_loopback_destination_is_rejected(
    monkeypatch,
):
    def loopback_dns(
        *args,
        **kwargs,
    ):
        return [
            (
                socket.AF_INET,
                socket.SOCK_STREAM,
                6,
                "",
                ("127.0.0.1", 443),
            )
        ]

    monkeypatch.setattr(
        socket,
        "getaddrinfo",
        loopback_dns,
    )

    fetcher = WebEvidenceFetcher(
        source_policy=WebSourcePolicy(
            "docs.python.org"
        )
    )

    with pytest.raises(
        UnsafeWebDestinationError
    ):
        fetcher._validate_url(
            "https://docs.python.org/"
        )


def test_ipv6_loopback_destination_is_rejected(
    monkeypatch,
):
    def loopback_dns(
        *args,
        **kwargs,
    ):
        return [
            (
                socket.AF_INET6,
                socket.SOCK_STREAM,
                6,
                "",
                ("::1", 443, 0, 0),
            )
        ]

    monkeypatch.setattr(
        socket,
        "getaddrinfo",
        loopback_dns,
    )

    fetcher = WebEvidenceFetcher(
        source_policy=WebSourcePolicy(
            "docs.python.org"
        )
    )

    with pytest.raises(
        UnsafeWebDestinationError
    ):
        fetcher._validate_url(
            "https://docs.python.org/"
        )


def test_public_destination_is_accepted(
    monkeypatch,
):
    monkeypatch.setattr(
        socket,
        "getaddrinfo",
        public_dns,
    )

    fetcher = WebEvidenceFetcher(
        source_policy=WebSourcePolicy(
            "docs.python.org"
        )
    )

    result = fetcher._validate_url(
        "https://docs.python.org/3/tutorial/"
    )

    assert result == (
        "https://docs.python.org/3/tutorial/"
    )


def test_html_cleanup_removes_unsafe_page_elements():
    body = b"""
    <html>
      <head>
        <style>
          body { color: red; }
        </style>
      </head>

      <body>
        <header>Site Header</header>

        <nav>
          Navigation
        </nav>

        <main>
          Python variables store values.

          <script>
            ignore_me()
          </script>

          <p>
            Variables can reference objects.
          </p>
        </main>

        <footer>
          Site Footer
        </footer>
      </body>
    </html>
    """

    text = WebEvidenceFetcher._extract_text(
        body
    )

    assert (
        "Python variables store values."
        in text
    )

    assert (
        "Variables can reference objects."
        in text
    )

    assert "ignore_me" not in text
    assert "Navigation" not in text
    assert "Site Header" not in text
    assert "Site Footer" not in text


def test_empty_html_is_rejected():
    body = b"""
    <html>
      <body>
        <script>
          no_learning_content()
        </script>
      </body>
    </html>
    """

    with pytest.raises(
        WebEvidenceFetchError
    ):
        WebEvidenceFetcher._extract_text(
            body
        )


def test_fetch_replaces_snippet_with_page_content(
    monkeypatch,
):
    monkeypatch.setattr(
        socket,
        "getaddrinfo",
        public_dns,
    )

    monkeypatch.setattr(
        httpx,
        "Client",
        FakeClient,
    )

    FakeClient.responses = [
        make_response(
            content=(
                b"<html><body>"
                b"<main>"
                b"Python uses indentation "
                b"to group statements."
                b"</main>"
                b"</body></html>"
            )
        )
    ]

    fetcher = WebEvidenceFetcher(
        source_policy=WebSourcePolicy(
            "docs.python.org"
        )
    )

    result = fetcher.fetch(
        make_evidence()
    )

    assert (
        "Python uses indentation"
        in result.content
    )

    assert (
        "Search result snippet."
        not in result.content
    )

    assert (
        result.domain
        == "docs.python.org"
    )


def test_unsupported_content_type_is_rejected(
    monkeypatch,
):
    monkeypatch.setattr(
        socket,
        "getaddrinfo",
        public_dns,
    )

    monkeypatch.setattr(
        httpx,
        "Client",
        FakeClient,
    )

    FakeClient.responses = [
        make_response(
            content=b"%PDF",
            content_type="application/pdf",
        )
    ]

    fetcher = WebEvidenceFetcher(
        source_policy=WebSourcePolicy(
            "docs.python.org"
        )
    )

    with pytest.raises(
        WebEvidenceFetchError
    ):
        fetcher.fetch(
            make_evidence()
        )


def test_oversized_response_is_rejected(
    monkeypatch,
):
    monkeypatch.setattr(
        socket,
        "getaddrinfo",
        public_dns,
    )

    monkeypatch.setattr(
        httpx,
        "Client",
        FakeClient,
    )

    from app.rag.web import evidence_fetcher

    monkeypatch.setattr(
        evidence_fetcher.settings,
        "A4A_WEB_MAX_CONTENT_BYTES",
        20,
    )

    FakeClient.responses = [
        make_response(
            content=(
                b"<html><body>"
                b"This response is intentionally "
                b"larger than twenty bytes."
                b"</body></html>"
            )
        )
    ]

    fetcher = WebEvidenceFetcher(
        source_policy=WebSourcePolicy(
            "docs.python.org"
        )
    )

    with pytest.raises(
        WebEvidenceFetchError
    ):
        fetcher.fetch(
            make_evidence()
        )


def test_redirect_to_unapproved_domain_is_blocked(
    monkeypatch,
):
    monkeypatch.setattr(
        socket,
        "getaddrinfo",
        public_dns,
    )

    monkeypatch.setattr(
        httpx,
        "Client",
        FakeClient,
    )

    FakeClient.responses = [
        make_response(
            status_code=302,
            headers={
                "location": (
                    "https://example.com/"
                    "malicious"
                )
            },
        )
    ]

    fetcher = WebEvidenceFetcher(
        source_policy=WebSourcePolicy(
            "docs.python.org"
        )
    )

    with pytest.raises(
        UnsafeWebDestinationError
    ):
        fetcher.fetch(
            make_evidence()
        )

    assert len(
        FakeClient.requested_urls
    ) == 1


def test_redirect_to_http_is_blocked(
    monkeypatch,
):
    monkeypatch.setattr(
        socket,
        "getaddrinfo",
        public_dns,
    )

    monkeypatch.setattr(
        httpx,
        "Client",
        FakeClient,
    )

    FakeClient.responses = [
        make_response(
            status_code=302,
            headers={
                "location": (
                    "http://docs.python.org/"
                    "unsafe"
                )
            },
        )
    ]

    fetcher = WebEvidenceFetcher(
        source_policy=WebSourcePolicy(
            "docs.python.org"
        )
    )

    with pytest.raises(
        UnsafeWebDestinationError
    ):
        fetcher.fetch(
            make_evidence()
        )

    assert len(
        FakeClient.requested_urls
    ) == 1


def test_safe_redirect_is_revalidated_and_followed(
    monkeypatch,
):
    monkeypatch.setattr(
        socket,
        "getaddrinfo",
        public_dns,
    )

    monkeypatch.setattr(
        httpx,
        "Client",
        FakeClient,
    )

    FakeClient.responses = [
        make_response(
            status_code=302,
            headers={
                "location": (
                    "/3/tutorial/introduction.html"
                )
            },
        ),
        make_response(
            url=(
                "https://docs.python.org/"
                "3/tutorial/introduction.html"
            ),
            content=(
                b"<html><body>"
                b"<main>"
                b"Python introduction."
                b"</main>"
                b"</body></html>"
            ),
        ),
    ]

    fetcher = WebEvidenceFetcher(
        source_policy=WebSourcePolicy(
            "docs.python.org"
        )
    )

    result = fetcher.fetch(
        make_evidence()
    )

    assert (
        "Python introduction."
        in result.content
    )

    assert len(
        FakeClient.requested_urls
    ) == 2

    assert (
        FakeClient.requested_urls[1]
        == (
            "https://docs.python.org/"
            "3/tutorial/introduction.html"
        )
    )


def test_redirect_limit_is_enforced(
    monkeypatch,
):
    monkeypatch.setattr(
        socket,
        "getaddrinfo",
        public_dns,
    )

    monkeypatch.setattr(
        httpx,
        "Client",
        FakeClient,
    )

    from app.rag.web import evidence_fetcher

    monkeypatch.setattr(
        evidence_fetcher.settings,
        "A4A_WEB_MAX_REDIRECTS",
        1,
    )

    FakeClient.responses = [
        make_response(
            status_code=302,
            headers={
                "location": "/first"
            },
        ),
        make_response(
            status_code=302,
            url=(
                "https://docs.python.org/first"
            ),
            headers={
                "location": "/second"
            },
        ),
    ]

    fetcher = WebEvidenceFetcher(
        source_policy=WebSourcePolicy(
            "docs.python.org"
        )
    )

    with pytest.raises(
        WebEvidenceFetchError
    ):
        fetcher.fetch(
            make_evidence()
        )


def test_http_error_is_isolated(
    monkeypatch,
):
    monkeypatch.setattr(
        socket,
        "getaddrinfo",
        public_dns,
    )

    monkeypatch.setattr(
        httpx,
        "Client",
        FakeClient,
    )

    FakeClient.responses = [
        make_response(
            status_code=503
        )
    ]

    fetcher = WebEvidenceFetcher(
        source_policy=WebSourcePolicy(
            "docs.python.org"
        )
    )

    with pytest.raises(
        WebEvidenceFetchError
    ):
        fetcher.fetch(
            make_evidence()
        )
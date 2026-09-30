from app.rag.web.models import (
    TrustedWebEvidence,
)


def build_web_context(
    evidence: list[TrustedWebEvidence],
) -> str:
    """
    Build bounded, source-labelled external evidence
    context for the web-grounded prompt.

    The content remains untrusted data.
    """

    if not evidence:
        return ""

    sections: list[str] = []

    for index, item in enumerate(
        evidence,
        start=1,
    ):
        title = item.title.strip()
        url = str(item.url).strip()
        content = item.content.strip()

        if not content:
            continue

        sections.append(
            f"[External Source {index}]\n"
            f"Title: {title}\n"
            f"URL: {url}\n"
            f"Content:\n{content}"
        )

    return "\n\n".join(
        sections
    )
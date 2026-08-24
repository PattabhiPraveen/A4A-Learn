import re


def clean_text(text: str) -> str:
    """
    Basic deterministic text cleaning for MVP RAG.

    The goal is to remove obvious extraction noise
    without changing the meaning of the source.
    """

    if not text:
        return ""

    # Normalize line endings
    text = text.replace("\r\n", "\n")
    text = text.replace("\r", "\n")

    # Remove excessive whitespace
    text = re.sub(r"[ \t]+", " ", text)

    # Reduce excessive blank lines
    text = re.sub(r"\n{3,}", "\n\n", text)

    # Remove common page-number-only lines
    text = re.sub(
        r"(?m)^\s*Page\s+\d+\s*$",
        "",
        text,
        flags=re.IGNORECASE,
    )

    # Remove leading/trailing whitespace
    text = text.strip()

    return text
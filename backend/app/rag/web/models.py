from pydantic import (
    BaseModel,
    Field,
    HttpUrl,
)


class WebSearchResult(BaseModel):
    """
    Normalized external evidence returned by a web
    retrieval provider.

    This model does not imply that the source is trusted.
    SourcePolicy must approve the URL separately.
    """

    title: str = Field(
        ...,
        min_length=1,
        max_length=300,
    )

    url: HttpUrl

    snippet: str = Field(
        ...,
        min_length=1,
        max_length=5000,
    )


class TrustedWebEvidence(BaseModel):
    """
    Bounded external evidence admitted to the AI context
    after trusted-domain approval and evidence selection.

    content remains deliberately limited to 5,000
    characters.
    """

    title: str = Field(
        ...,
        min_length=1,
        max_length=300,
    )

    url: HttpUrl

    domain: str = Field(
        ...,
        min_length=1,
        max_length=255,
    )

    content: str = Field(
        ...,
        min_length=1,
        max_length=5000,
    )


class FetchedWebDocument(BaseModel):
    """
    Sanitized page content acquired from an approved
    external source before relevance selection.

    This object is not admitted directly to the LLM
    context.

    Network response size is independently constrained
    by A4A_WEB_MAX_CONTENT_BYTES in WebEvidenceFetcher.
    """

    title: str = Field(
        ...,
        min_length=1,
        max_length=300,
    )

    url: HttpUrl

    domain: str = Field(
        ...,
        min_length=1,
        max_length=255,
    )

    content: str = Field(
        ...,
        min_length=1,
    )
def build_context(
    results: list[dict],
) -> str:

    if not results:
        return ""

    sections = []

    for index, result in enumerate(
        results,
        start=1,
    ):

        metadata = result.get(
            "metadata",
            {},
        )

        title = metadata.get(
            "title",
            "Unknown source",
        )

        text = result.get(
            "text",
            "",
        )

        sections.append(
            f"[Source {index}: {title}]\n"
            f"{text}"
        )

    return "\n\n".join(sections)
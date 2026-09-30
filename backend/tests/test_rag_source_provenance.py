from app.schemas.rag import RAGSource


def test_curriculum_source_defaults_to_curriculum():
    source = RAGSource(
        title="Python Introduction",
        source="lessons/python_intro.md",
        distance=0.21,
    )

    assert (
        source.source_type
        == "curriculum"
    )

    assert source.distance == 0.21


def test_web_source_supports_null_distance():
    source = RAGSource(
        title="Official Python Documentation",
        source=(
            "https://docs.python.org/"
            "3/tutorial/"
        ),
        distance=None,
        source_type="web",
    )

    assert source.source_type == "web"
    assert source.distance is None


def test_curriculum_source_serializes_provenance():
    source = RAGSource(
        title="Python Functions",
        source="lessons/python_functions.md",
        distance=0.35,
    )

    result = source.model_dump()

    assert (
        result["source_type"]
        == "curriculum"
    )

    assert result["distance"] == 0.35


def test_web_source_serializes_provenance():
    source = RAGSource(
        title="Official Python Tutorial",
        source=(
            "https://docs.python.org/"
            "3/tutorial/"
        ),
        source_type="web",
    )

    result = source.model_dump()

    assert (
        result["source_type"]
        == "web"
    )

    assert result["distance"] is None
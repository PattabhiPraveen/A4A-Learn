import pytest

from app.core.config import settings
from app.rag.service import (
    FALLBACK_MESSAGE,
    RAGService,
)
from app.rag.web.web_retriever import (
    WebRetrievalDisabledError,
)


class FakeRetriever:
    def __init__(
        self,
        results=None,
    ):
        self.results = (
            results
            if results is not None
            else []
        )
        self.questions = []

    def retrieve(
        self,
        question: str,
    ):
        self.questions.append(
            question
        )

        return self.results


class FakeLLM:
    def __init__(
        self,
        answer: str,
    ):
        self.answer = answer
        self.prompts = []

    def generate(
        self,
        prompt: str,
    ) -> str:
        self.prompts.append(
            prompt
        )

        return self.answer


class FakeWebOrchestrator:
    def __init__(
        self,
        result=None,
        error=None,
    ):
        self.result = result
        self.error = error
        self.questions = []

    def answer(
        self,
        question: str,
    ):
        self.questions.append(
            question
        )

        if self.error is not None:
            raise self.error

        return self.result


def curriculum_result(
    *,
    distance: float = 0.20,
    title: str = "Python Introduction",
    source: str = "lesson_python_intro.md",
):
    return {
        "text": (
            "Python is a programming language."
        ),
        "distance": distance,
        "metadata": {
            "title": title,
            "source": source,
        },
    }


def web_success_result(
    question: str,
):
    return {
        "question": question,
        "answer": (
            "External grounded answer "
            "[External Source 1]."
        ),
        "grounded": True,
        "sources": [
            {
                "title": (
                    "Official Python Documentation"
                ),
                "source": (
                    "https://docs.python.org/"
                    "3/tutorial/"
                ),
                "distance": None,
                "source_type": "web",
            }
        ],
    }


def web_fallback_result(
    question: str,
):
    return {
        "question": question,
        "answer": (
            "I do not have enough information "
            "in the approved external sources "
            "to answer that question."
        ),
        "grounded": False,
        "sources": [],
    }


def test_empty_question_is_rejected():
    service = RAGService(
        retriever=FakeRetriever(),
        llm=FakeLLM("unused"),
        web_orchestrator=(
            FakeWebOrchestrator()
        ),
    )

    with pytest.raises(
        ValueError
    ):
        service.answer("   ")


def test_local_grounded_answer_does_not_call_web(
    monkeypatch,
):
    monkeypatch.setattr(
        settings,
        "A4A_WEB_SEARCH_ENABLED",
        True,
    )

    retriever = FakeRetriever(
        results=[
            curriculum_result(),
        ]
    )

    llm = FakeLLM(
        "Python is a programming language "
        "[Source 1]."
    )

    web = FakeWebOrchestrator(
        result=web_success_result(
            "What is Python?"
        )
    )

    service = RAGService(
        retriever=retriever,
        llm=llm,
        web_orchestrator=web,
    )

    result = service.answer(
        "What is Python?"
    )

    assert result["grounded"] is True

    assert (
        result["answer"]
        == (
            "Python is a programming language "
            "[Source 1]."
        )
    )

    assert len(result["sources"]) == 1

    source = result["sources"][0]

    assert (
        source["source_type"]
        == "curriculum"
    )

    assert source["distance"] == 0.2

    assert web.questions == []


def test_no_local_evidence_web_disabled_abstains(
    monkeypatch,
):
    monkeypatch.setattr(
        settings,
        "A4A_WEB_SEARCH_ENABLED",
        False,
    )

    web = FakeWebOrchestrator(
        result=web_success_result(
            "Unsupported question"
        )
    )

    service = RAGService(
        retriever=FakeRetriever(
            results=[]
        ),
        llm=FakeLLM("unused"),
        web_orchestrator=web,
    )

    result = service.answer(
        "Unsupported question"
    )

    assert result["grounded"] is False
    assert result["sources"] == []

    assert (
        result["answer"]
        == FALLBACK_MESSAGE
    )

    assert web.questions == []


def test_no_local_evidence_invokes_web_when_enabled(
    monkeypatch,
):
    monkeypatch.setattr(
        settings,
        "A4A_WEB_SEARCH_ENABLED",
        True,
    )

    web = FakeWebOrchestrator(
        result=web_success_result(
            "Explain Python decorators"
        )
    )

    service = RAGService(
        retriever=FakeRetriever(
            results=[]
        ),
        llm=FakeLLM("unused"),
        web_orchestrator=web,
    )

    result = service.answer(
        "Explain Python decorators"
    )

    assert result["grounded"] is True

    assert (
        result["sources"][0][
            "source_type"
        ]
        == "web"
    )

    assert (
        result["sources"][0][
            "distance"
        ]
        is None
    )

    assert web.questions == [
        "Explain Python decorators"
    ]


def test_local_model_fallback_invokes_web(
    monkeypatch,
):
    monkeypatch.setattr(
        settings,
        "A4A_WEB_SEARCH_ENABLED",
        True,
    )

    web = FakeWebOrchestrator(
        result=web_success_result(
            "Explain unsupported topic"
        )
    )

    service = RAGService(
        retriever=FakeRetriever(
            results=[
                curriculum_result(),
            ]
        ),
        llm=FakeLLM(
            FALLBACK_MESSAGE
        ),
        web_orchestrator=web,
    )

    result = service.answer(
        "Explain unsupported topic"
    )

    assert result["grounded"] is True

    assert (
        result["sources"][0][
            "source_type"
        ]
        == "web"
    )

    assert web.questions == [
        "Explain unsupported topic"
    ]


def test_web_insufficient_returns_canonical_fallback(
    monkeypatch,
):
    monkeypatch.setattr(
        settings,
        "A4A_WEB_SEARCH_ENABLED",
        True,
    )

    question = (
        "Explain unsupported topic"
    )

    web = FakeWebOrchestrator(
        result=web_fallback_result(
            question
        )
    )

    service = RAGService(
        retriever=FakeRetriever(
            results=[]
        ),
        llm=FakeLLM("unused"),
        web_orchestrator=web,
    )

    result = service.answer(
        question
    )

    assert result["grounded"] is False
    assert result["sources"] == []

    assert (
        result["answer"]
        == FALLBACK_MESSAGE
    )


def test_web_disabled_error_returns_canonical_fallback(
    monkeypatch,
):
    monkeypatch.setattr(
        settings,
        "A4A_WEB_SEARCH_ENABLED",
        True,
    )

    web = FakeWebOrchestrator(
        error=WebRetrievalDisabledError(
            "Web retrieval disabled."
        )
    )

    service = RAGService(
        retriever=FakeRetriever(
            results=[]
        ),
        llm=FakeLLM("unused"),
        web_orchestrator=web,
    )

    result = service.answer(
        "Unsupported question"
    )

    assert result["grounded"] is False
    assert result["sources"] == []

    assert (
        result["answer"]
        == FALLBACK_MESSAGE
    )


def test_question_is_normalized():
    retriever = FakeRetriever(
        results=[
            curriculum_result(),
        ]
    )

    service = RAGService(
        retriever=retriever,
        llm=FakeLLM(
            "Grounded answer [Source 1]."
        ),
        web_orchestrator=(
            FakeWebOrchestrator()
        ),
    )

    result = service.answer(
        "   What is Python?   "
    )

    assert (
        result["question"]
        == "What is Python?"
    )

    assert retriever.questions == [
        "What is Python?"
    ]
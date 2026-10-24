from app.rag.web.orchestrator import WebEvidenceOrchestrator
from app.rag.web.prompt_builder import WEB_FALLBACK_MESSAGE

from tests.test_web_orchestrator import (
    FakeRetriever,
    FakeFetcher,
    make_evidence,
)


class SequenceLLM:
    def __init__(self, responses):
        self.responses = list(responses)
        self.prompts = []

    def generate(self, prompt):
        self.prompts.append(prompt)
        index = len(self.prompts) - 1

        if index >= len(self.responses):
            raise AssertionError("Unexpected generation")

        response = self.responses[index]

        if isinstance(response, Exception):
            raise response

        return response


QUESTION = "Does Python support list comprehensions?"
UNCITED = "Python supports list comprehensions."
CITED = "Python supports list comprehensions. [External Source 1]"


def build_orchestrator(llm):
    candidate = make_evidence(content=UNCITED)

    return WebEvidenceOrchestrator(
        retriever=FakeRetriever(results=[candidate]),
        fetcher=FakeFetcher(),
        llm=llm,
    )


def test_retry_recovers_missing_citation():
    llm = SequenceLLM([UNCITED, CITED])
    result = build_orchestrator(llm).answer(QUESTION)

    assert result["grounded"] is True
    assert result["answer"] == CITED
    assert len(llm.prompts) == 2


def test_retry_still_uncited_fails_closed():
    llm = SequenceLLM([UNCITED, UNCITED])
    result = build_orchestrator(llm).answer(QUESTION)

    assert result["grounded"] is False
    assert result["answer"] == WEB_FALLBACK_MESSAGE
    assert len(llm.prompts) == 2


def test_valid_first_answer_does_not_retry():
    llm = SequenceLLM([CITED])
    result = build_orchestrator(llm).answer(QUESTION)

    assert result["grounded"] is True
    assert len(llm.prompts) == 1


def test_retry_invalid_citation_fails_closed():
    llm = SequenceLLM([
        UNCITED,
        "Python supports list comprehensions. [External Source 9]",
    ])
    result = build_orchestrator(llm).answer(QUESTION)

    assert result["grounded"] is False
    assert result["answer"] == WEB_FALLBACK_MESSAGE
    assert len(llm.prompts) == 2


def test_retry_unsupported_claim_fails_closed():
    llm = SequenceLLM([
        UNCITED,
        "Python supports underwater spacecraft. [External Source 1]",
    ])
    result = build_orchestrator(llm).answer(QUESTION)

    assert result["grounded"] is False
    assert result["answer"] == WEB_FALLBACK_MESSAGE
    assert len(llm.prompts) == 2


def test_retry_exception_fails_closed():
    llm = SequenceLLM([
        UNCITED,
        RuntimeError("Simulated Ollama failure"),
    ])
    result = build_orchestrator(llm).answer(QUESTION)

    assert result["grounded"] is False
    assert result["answer"] == WEB_FALLBACK_MESSAGE
    assert len(llm.prompts) == 2


def test_invalid_first_citation_does_not_retry():
    llm = SequenceLLM([
        "Python supports list comprehensions. [External Source 9]",
    ])
    result = build_orchestrator(llm).answer(QUESTION)

    assert result["grounded"] is False
    assert len(llm.prompts) == 1


def test_fallback_does_not_retry():
    llm = SequenceLLM([WEB_FALLBACK_MESSAGE])
    result = build_orchestrator(llm).answer(QUESTION)

    assert result["grounded"] is False
    assert len(llm.prompts) == 1


def test_retry_preserves_approved_evidence():
    llm = SequenceLLM([UNCITED, CITED])
    result = build_orchestrator(llm).answer(QUESTION)

    assert result["grounded"] is True
    assert len(llm.prompts) == 2

    for prompt in llm.prompts:
        assert QUESTION in prompt
        assert UNCITED in prompt
        assert "[External Source 1]" in prompt

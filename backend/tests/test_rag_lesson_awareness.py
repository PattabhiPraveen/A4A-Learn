from app.rag.service import (
    FALLBACK_MESSAGE,
    RAGService,
)


class FakeRetriever:
    def __init__(self):
        self.questions = []

    def retrieve(self, question):
        self.questions.append(question)

        return []


class FakeLLM:
    def __init__(self, answers):
        self.answers = list(answers)
        self.prompts = []

    def generate(self, prompt):
        self.prompts.append(prompt)

        return self.answers.pop(0)


class FakeWebOrchestrator:
    def __init__(self):
        self.questions = []

    def answer(self, question):
        self.questions.append(question)

        return {
            "question": question,
            "answer": FALLBACK_MESSAGE,
            "grounded": False,
            "sources": [],
        }


class FakeLessonContext:
    def as_retrieval_result(self):
        return {
            "document": (
                "A Python variable stores a value."
            ),
            "distance": 0.0,
            "metadata": {
                "title": "Python Variables",
                "source": "lesson_01",
                "curriculum_id": "PY-01",
                "course": "Python",
                "level": "Beginner",
                "evidence_scope": (
                    "selected_lesson"
                ),
            },
        }


class FakeLessonResolver:
    def __init__(self, context=None):
        self.context = context
        self.lesson_ids = []

    def resolve(self, lesson_id):
        self.lesson_ids.append(lesson_id)

        return self.context


def test_selected_lesson_is_used_before_retriever():
    retriever = FakeRetriever()

    llm = FakeLLM(
        [
            (
                "A variable stores a value "
                "in Python. [Source 1]"
            )
        ]
    )

    resolver = FakeLessonResolver(
        FakeLessonContext()
    )

    service = RAGService(
        retriever=retriever,
        llm=llm,
        web_orchestrator=(
            FakeWebOrchestrator()
        ),
        lesson_context_resolver=resolver,
    )

    result = service.answer(
        "What is a variable?",
        lesson_id="lesson_01",
    )

    assert result["grounded"] is True

    assert (
        result["sources"][0]["source"]
        == "lesson_01"
    )

    assert (
        result["sources"][0]["source_type"]
        == "curriculum"
    )

    assert (
        result["sources"][0]["distance"]
        == 0.0
    )

    assert retriever.questions == []

    assert resolver.lesson_ids == [
        "lesson_01"
    ]

    assert len(llm.prompts) == 1


def test_lesson_abstention_continues_to_normal_rag():
    retriever = FakeRetriever()

    llm = FakeLLM(
        [
            FALLBACK_MESSAGE,
        ]
    )

    resolver = FakeLessonResolver(
        FakeLessonContext()
    )

    service = RAGService(
        retriever=retriever,
        llm=llm,
        web_orchestrator=(
            FakeWebOrchestrator()
        ),
        lesson_context_resolver=resolver,
    )

    result = service.answer(
        "Explain neural networks",
        lesson_id="lesson_01",
    )

    assert resolver.lesson_ids == [
        "lesson_01"
    ]

    assert retriever.questions == [
        "Explain neural networks"
    ]

    assert result["grounded"] is False

    assert result["answer"] == (
        FALLBACK_MESSAGE
    )

    assert result["sources"] == []


def test_no_lesson_preserves_general_rag_path():
    retriever = FakeRetriever()

    resolver = FakeLessonResolver(
        context=None
    )

    service = RAGService(
        retriever=retriever,
        llm=FakeLLM([]),
        web_orchestrator=(
            FakeWebOrchestrator()
        ),
        lesson_context_resolver=resolver,
    )

    result = service.answer(
        "What is Python?"
    )

    assert resolver.lesson_ids == [
        None
    ]

    assert retriever.questions == [
        "What is Python?"
    ]

    assert result["grounded"] is False

    assert result["answer"] == (
        FALLBACK_MESSAGE
    )

    assert result["sources"] == []
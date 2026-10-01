import {
  FormEvent,
  useEffect,
  useState,
} from "react";

import {
  Link,
  useSearchParams,
} from "react-router-dom";

import {
  useAuth,
} from "../contexts/AuthContext";

import {
  ApiError,
} from "../services/apiClient";

import {
  getLearningLesson,
} from "../services/learningService";

import {
  askTutor,
} from "../services/tutorService";

import type {
  LearningLessonDetail,
} from "../types/learning";

import type {
  RAGResponse,
} from "../types/tutor";


export default function TutorPage() {
  const { token } = useAuth();

  const [
    searchParams,
  ] = useSearchParams();

  const lessonId =
    searchParams.get("lesson_id")?.trim() ?? "";

  const [
    lessonContext,
    setLessonContext,
  ] = useState<
    LearningLessonDetail | null
  >(null);

  const [
    isLoadingLessonContext,
    setIsLoadingLessonContext,
  ] = useState(false);

  const [
    lessonContextError,
    setLessonContextError,
  ] = useState<string | null>(
    null,
  );

  const [
    question,
    setQuestion,
  ] = useState("");

  const [
    result,
    setResult,
  ] = useState<RAGResponse | null>(
    null,
  );

  const [
    isSubmitting,
    setIsSubmitting,
  ] = useState(false);

  const [
    errorMessage,
    setErrorMessage,
  ] = useState<string | null>(
    null,
  );


  useEffect(() => {
    let cancelled = false;

    async function loadLessonContext() {
      if (
        !token ||
        !lessonId
      ) {
        setLessonContext(null);
        setLessonContextError(null);
        return;
      }

      setIsLoadingLessonContext(true);
      setLessonContextError(null);

      try {
        const lesson =
          await getLearningLesson(
            lessonId,
            token,
          );

        if (!cancelled) {
          setLessonContext(
            lesson,
          );
        }
      } catch (error) {
        if (cancelled) {
          return;
        }

        setLessonContext(null);

        if (error instanceof ApiError) {
          setLessonContextError(
            error.detail,
          );
        } else {
          setLessonContextError(
            "Unable to load the selected lesson context.",
          );
        }
      } finally {
        if (!cancelled) {
          setIsLoadingLessonContext(false);
        }
      }
    }

    void loadLessonContext();

    return () => {
      cancelled = true;
    };
  }, [
    lessonId,
    token,
  ]);


  async function handleSubmit(
    event: FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault();

    const normalizedQuestion =
      question.trim();

    if (
      normalizedQuestion.length < 3
    ) {
      setErrorMessage(
        "Please enter a question with at least 3 characters.",
      );

      return;
    }

    if (!token) {
      setErrorMessage(
        "Your session is not available. Please sign in again.",
      );

      return;
    }

    setIsSubmitting(true);
    setErrorMessage(null);
    setResult(null);

    try {
      const response =
        await askTutor(
          normalizedQuestion,
          token,
          lessonContext?.id,
        );

      setResult(response);
    } catch (error) {
      if (error instanceof ApiError) {
        setErrorMessage(
          error.detail,
        );
      } else {
        setErrorMessage(
          "The AI Tutor is currently unavailable. Please try again.",
        );
      }
    } finally {
      setIsSubmitting(false);
    }
  }


  return (
    <section
      className="page-container page-section"
      aria-labelledby="tutor-heading"
    >
      <div className="page-heading">
        <p className="eyebrow">
          AI Tutor
        </p>

        <h1 id="tutor-heading">
          Ask about your learning material
        </h1>

        <p>
          The AI Tutor uses approved
          learning content to provide
          grounded answers. When the
          available evidence is not
          sufficient, your question can
          be sent for teacher review.
        </p>
      </div>

      {isLoadingLessonContext && (
        <div
          className="status-message"
          role="status"
          aria-live="polite"
        >
          Loading lesson context...
        </div>
      )}

      {lessonContextError && (
        <div
          className="status-message status-message--error"
          role="alert"
        >
          <strong>
            Lesson context unavailable.
          </strong>

          <p>
            {lessonContextError}
          </p>

          <p>
            You can still ask the AI Tutor
            a general learning question.
          </p>
        </div>
      )}

      {lessonContext && (
        <section
          className="placeholder-panel"
          aria-labelledby="tutor-context-heading"
        >
          <p className="eyebrow">
            Current lesson
          </p>

          <h2 id="tutor-context-heading">
            You're asking about:{" "}
            {lessonContext.curriculum_id}
            {" — "}
            {lessonContext.title}
          </h2>

          <p>
            <strong>Course:</strong>{" "}
            {lessonContext.course}
          </p>

          <p>
            <strong>Level:</strong>{" "}
            {lessonContext.level}
            {" · "}
            <strong>Estimated time:</strong>{" "}
            {lessonContext.estimated_minutes}
            {" min"}
          </p>

          <p>
            {lessonContext.description}
          </p>

          <Link
            to="/learn"
            className="button button--secondary"
          >
            Choose another lesson
          </Link>
        </section>
      )}

      <div className="placeholder-panel">
        <h2>
          Ask a question
        </h2>

        {lessonContext && (
          <p className="form-help">
            Your question will be asked
            while you are viewing{" "}
            <strong>
              {lessonContext.curriculum_id}
              {" — "}
              {lessonContext.title}
            </strong>
            .
          </p>
        )}

        <form
          onSubmit={handleSubmit}
        >
          <label htmlFor="tutor-question">
            Your question
          </label>

          <textarea
            id="tutor-question"
            rows={5}
            value={question}
            maxLength={1000}
            placeholder={
              lessonContext
                ? "Ask a question about this lesson..."
                : "Type your learning question here..."
            }
            disabled={isSubmitting}
            onChange={(event) =>
              setQuestion(
                event.target.value,
              )
            }
          />

          <p className="form-help">
            {question.length}/1000
            {" "}characters
          </p>

          <button
            type="submit"
            className="button button--primary"
            disabled={
              isSubmitting ||
              question.trim().length < 3
            }
          >
            {isSubmitting
              ? "Checking learning materials..."
              : "Ask AI Tutor"}
          </button>
        </form>
      </div>

      {errorMessage && (
        <div
          className="status-message status-message--error"
          role="alert"
        >
          {errorMessage}
        </div>
      )}

      {isSubmitting && (
        <p
          role="status"
          aria-live="polite"
        >
          The AI Tutor is checking available
          learning evidence.
        </p>
      )}

      {result && (
        <section
          className="placeholder-panel"
          aria-labelledby="tutor-answer-heading"
          aria-live="polite"
        >
          <p className="eyebrow">
            {!result.grounded
              ? "Insufficient evidence"
              : result.sources.some(
                    (source) =>
                      source.source_type === "web",
                  )
                ? "Grounded in approved external evidence"
                : "Grounded in A4A Learn curriculum"}
          </p>

          <h2 id="tutor-answer-heading">
            AI Tutor response
          </h2>

          <p>
            {result.answer}
          </p>

          {result.grounded &&
            result.sources.length > 0 && (
              <div>
                <h3>
                  Sources
                </h3>

                <ul>
                  {result.sources.map(
                    (
                      source,
                      index,
                    ) => (
                      <li
                        key={`${source.title}-${index}`}
                      >
                        <strong>
                          {source.title}
                        </strong>

                        <div className="form-help">
                          {source.source_type ===
                          "web"
                            ? "External web source"
                            : "A4A Learn curriculum"}
                        </div>

                        {source.source && (
                          <div>
                            {source.source_type ===
                            "web" ? (
                              <a
                                href={
                                  source.source
                                }
                                target="_blank"
                                rel="noopener noreferrer"
                              >
                                View external source
                              </a>
                            ) : (
                              <span>
                                {
                                  source.source
                                }
                              </span>
                            )}
                          </div>
                        )}
                      </li>
                    ),
                  )}
                </ul>
              </div>
            )}

          {result.requires_human_review && (
            <div
              className="status-message"
              role="status"
            >
              <h3>
                Teacher review requested
              </h3>

              <p>
                The available learning
                material was not
                sufficient for a reliable
                answer. Your question has
                been routed for teacher
                review.
              </p>

              {result.review_id && (
                <p>
                  Review reference:{" "}
                  <code>
                    {result.review_id}
                  </code>
                </p>
              )}
            </div>
          )}

          {!result.requires_human_review &&
            result.grounded && (
              <p className="form-help">
                {result.sources.some(
                  (source) =>
                    source.source_type ===
                    "web",
                )
                  ? "This response uses supplementary evidence from approved external sources."
                  : "This response was generated from retrieved A4A Learn curriculum material."}
              </p>
            )}

          <div className="lesson-actions">
            <button
              type="button"
              className="button button--secondary"
              onClick={() => {
                setQuestion("");
                setResult(null);
                setErrorMessage(null);
              }}
            >
              Ask another question
            </button>

            <Link
              to="/learn"
              className="button button--secondary"
            >
              Back to lessons
            </Link>
          </div>
        </section>
      )}
    </section>
  );
}
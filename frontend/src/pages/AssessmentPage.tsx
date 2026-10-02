import {
  useEffect,
  useState,
} from "react";

import {
  useNavigate,
  useParams,
} from "react-router-dom";

import {
  getAssessment,
  submitAssessment,
} from "../services/assessmentService";

import type {
  Assessment,
  AssessmentResult,
} from "../types/assessment";

import {
  useAuth,
} from "../contexts/AuthContext";


export default function AssessmentPage() {
  const {
    lessonId,
  } = useParams<{
    lessonId: string;
  }>();

  const navigate = useNavigate();

  const {
    token,
  } = useAuth();

  const [
    assessment,
    setAssessment,
  ] = useState<Assessment | null>(
    null,
  );

  const [
    selectedAnswers,
    setSelectedAnswers,
  ] = useState<
    Record<string, number>
  >({});

  const [
    result,
    setResult,
  ] = useState<AssessmentResult | null>(
    null,
  );

  const [
    isLoading,
    setIsLoading,
  ] = useState(true);

  const [
    isSubmitting,
    setIsSubmitting,
  ] = useState(false);

  const [
    error,
    setError,
  ] = useState<string | null>(
    null,
  );


  useEffect(() => {
    let cancelled = false;

    async function loadAssessment() {
      if (!token || !lessonId) {
        setError(
          "Assessment information is unavailable.",
        );
        setIsLoading(false);
        return;
      }

      try {
        setIsLoading(true);
        setError(null);

        const data =
          await getAssessment(
            lessonId,
            token,
          );

        if (cancelled) {
          return;
        }

        setAssessment(data);
      } catch {
        if (!cancelled) {
          setError(
            "Unable to load this assessment. Please try again.",
          );
        }
      } finally {
        if (!cancelled) {
          setIsLoading(false);
        }
      }
    }

    void loadAssessment();

    return () => {
      cancelled = true;
    };
  }, [
    lessonId,
    token,
  ]);


  function handleAnswerChange(
    questionId: string,
    selectedOption: number,
  ) {
    setSelectedAnswers(
      (current) => ({
        ...current,
        [questionId]:
          selectedOption,
      }),
    );
  }


  async function handleSubmit() {
    if (
      !token ||
      !lessonId ||
      !assessment
    ) {
      return;
    }

    if (
      Object.keys(
        selectedAnswers,
      ).length !==
      assessment.questions.length
    ) {
      setError(
        "Please answer all questions before submitting.",
      );
      return;
    }

    try {
      setIsSubmitting(true);
      setError(null);

      const submission = {
        answers:
          assessment.questions.map(
            (question) => ({
              question_id:
                question.id,
              selected_option:
                selectedAnswers[
                  question.id
                ],
            }),
          ),
      };

      const response =
        await submitAssessment(
          lessonId,
          submission,
          token,
        );

      setResult(response);
    } catch {
      setError(
        "Unable to submit the assessment. Please try again.",
      );
    } finally {
      setIsSubmitting(false);
    }
  }


  function handleRetake() {
    setSelectedAnswers({});
    setResult(null);
    setError(null);
  }


  if (isLoading) {
    return (
      <main className="page-container">
        <section className="page-card">
          <h1>Assessment</h1>
          <p>
            Loading assessment...
          </p>
        </section>
      </main>
    );
  }


  if (error && !assessment) {
    return (
      <main className="page-container">
        <section className="page-card">
          <h1>Assessment</h1>

          <p role="alert">
            {error}
          </p>

          <button
            type="button"
            onClick={() =>
              navigate("/learn")
            }
          >
            Back to Learning
          </button>
        </section>
      </main>
    );
  }


  if (!assessment) {
    return (
      <main className="page-container">
        <section className="page-card">
          <h1>Assessment</h1>

          <p>
            Assessment information is
            unavailable.
          </p>

          <button
            type="button"
            onClick={() =>
              navigate("/learn")
            }
          >
            Back to Learning
          </button>
        </section>
      </main>
    );
  }


  if (result) {
    return (
      <main className="page-container">
        <section className="page-card">
          <h1>
            Assessment Result
          </h1>

          <p>
            {assessment.title}
          </p>

          <div
            aria-label="Assessment score"
          >
            <strong>
              {result.score_percent}%
            </strong>
          </div>

          <p>
            You answered{" "}
            <strong>
              {result.correct_answers}
            </strong>{" "}
            of{" "}
            <strong>
              {result.total_questions}
            </strong>{" "}
            questions correctly.
          </p>

          <p>
            Recommendation:{" "}
            <strong>
              {result.recommendation}
            </strong>
          </p>

          <div>
            <h2>
              Question Results
            </h2>

            <ol>
              {result.question_results.map(
                (
                  questionResult,
                  index,
                ) => (
                  <li
                    key={
                      questionResult.question_id
                    }
                  >
                    <span>
                      Question{" "}
                      {index + 1}:{" "}
                    </span>

                    <strong>
                      {questionResult.is_correct
                        ? "Correct"
                        : "Needs practice"}
                    </strong>
                  </li>
                ),
              )}
            </ol>
          </div>

          <div>
            <button
              type="button"
              onClick={
                handleRetake
              }
            >
              Retake Assessment
            </button>

            <button
              type="button"
              onClick={() =>
                navigate(
                  "/progress",
                )
              }
            >
              View Progress
            </button>

            <button
              type="button"
              onClick={() =>
                navigate(
                  `/learn`,
                )
              }
            >
              Back to Learning
            </button>
          </div>
        </section>
      </main>
    );
  }


  return (
    <main className="page-container">
      <section className="page-card">
        <header>
          <h1>
            {assessment.title}
          </h1>

          <p>
            Assessment for lesson{" "}
            <strong>
              {assessment.lesson_id}
            </strong>
          </p>

          <p>
            Curriculum:{" "}
            <strong>
              {assessment.curriculum_id}
            </strong>
          </p>
        </header>

        {error && (
          <p
            role="alert"
          >
            {error}
          </p>
        )}

        <form
          onSubmit={(event) => {
            event.preventDefault();
            void handleSubmit();
          }}
        >
          {assessment.questions.map(
            (
              question,
              questionIndex,
            ) => (
              <fieldset
                key={
                  question.id
                }
              >
                <legend>
                  <strong>
                    {questionIndex +
                      1}
                    .{" "}
                    {question.question}
                  </strong>
                </legend>

                {question.options.map(
                  (
                    option,
                    optionIndex,
                  ) => {
                    const selected =
                      selectedAnswers[
                        question.id
                      ] ===
                      optionIndex;

                    return (
                      <label
                        key={`${question.id}-${optionIndex}`}
                        style={{
                          display:
                            "block",
                          cursor:
                            "pointer",
                        }}
                      >
                        <input
                          type="radio"
                          name={
                            question.id
                          }
                          value={
                            optionIndex
                          }
                          checked={
                            selected
                          }
                          onChange={() =>
                            handleAnswerChange(
                              question.id,
                              optionIndex,
                            )
                          }
                        />

                        {" "}

                        {option}
                      </label>
                    );
                  },
                )}
              </fieldset>
            ),
          )}

          <div>
            <button
              type="submit"
              disabled={
                isSubmitting
              }
            >
              {isSubmitting
                ? "Submitting..."
                : "Submit Assessment"}
            </button>

            <button
              type="button"
              onClick={() =>
                navigate(
                  "/learn",
                )
              }
              disabled={
                isSubmitting
              }
            >
              Cancel
            </button>
          </div>
        </form>
      </section>
    </main>
  );
}
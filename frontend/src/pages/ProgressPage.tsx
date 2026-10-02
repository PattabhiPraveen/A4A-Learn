import {
  useEffect,
  useMemo,
  useState,
} from "react";

import {
  useAuth,
} from "../contexts/AuthContext";

import {
  getLearningLessons,
} from "../services/learningService";

import {
  getLessonProgress,
  getMyProgressAnalytics,
} from "../services/progressService";

import type {
  LearningLessonSummary,
} from "../types/learning";

import type {
  LessonProgress,
  ProgressAnalytics,
} from "../types/progress";


function formatDate(
  value: string | null,
): string {
  if (!value) {
    return "—";
  }

  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return "—";
  }

  return date.toLocaleString();
}


function formatScore(
  value: number | null,
): string {
  if (value === null) {
    return "—";
  }

  return `${value}%`;
}


function formatRecommendation(
  value: string | null,
): string {
  if (!value) {
    return "—";
  }

  return value.charAt(0).toUpperCase()
    + value.slice(1);
}


export default function ProgressPage() {
  const {
    token,
  } = useAuth();

  const [
    analytics,
    setAnalytics,
  ] = useState<ProgressAnalytics | null>(
    null,
  );

  const [
    lessons,
    setLessons,
  ] = useState<LearningLessonSummary[]>(
    [],
  );

  const [
    lessonProgress,
    setLessonProgress,
  ] = useState<LessonProgress[]>(
    [],
  );

  const [
    isLoading,
    setIsLoading,
  ] = useState(true);

  const [
    error,
    setError,
  ] = useState<string | null>(
    null,
  );


  useEffect(() => {
    let cancelled = false;

    async function loadProgress() {
      if (!token) {
        setAnalytics(null);
        setLessons([]);
        setLessonProgress([]);
        setIsLoading(false);

        return;
      }

      setIsLoading(true);
      setError(null);

      try {
        const [
          analyticsResult,
          lessonsResult,
        ] = await Promise.all([
          getMyProgressAnalytics(
            token,
            10,
          ),
          getLearningLessons(
            token,
          ),
        ]);

        if (cancelled) {
          return;
        }

        setAnalytics(
          analyticsResult,
        );

        setLessons(
          lessonsResult,
        );

        const progressResults =
          await Promise.all(
            lessonsResult.map(
              (lesson) =>
                getLessonProgress(
                  lesson.id,
                  token,
                ),
            ),
          );

        if (cancelled) {
          return;
        }

        setLessonProgress(
          progressResults,
        );
      } catch (err) {
        if (cancelled) {
          return;
        }

        setError(
          err instanceof Error
            ? err.message
            : "Unable to load learning progress.",
        );
      } finally {
        if (!cancelled) {
          setIsLoading(false);
        }
      }
    }

    void loadProgress();

    return () => {
      cancelled = true;
    };
  }, [token]);


  const assessmentSummary =
    useMemo(() => {
      const attempts =
        lessonProgress.reduce(
          (
            total,
            progress,
          ) =>
            total
            + progress.assessment_attempts,
          0,
        );

      const completedLessons =
        lessonProgress.filter(
          (progress) =>
            progress.completed,
        ).length;

      const scores =
        lessonProgress
          .map(
            (progress) =>
              progress.latest_score_percent,
          )
          .filter(
            (
              score,
            ): score is number =>
              score !== null,
          );

      const bestScore =
        lessonProgress.reduce<
          number | null
        >(
          (
            best,
            progress,
          ) => {
            if (
              progress.best_score_percent
              === null
            ) {
              return best;
            }

            if (best === null) {
              return progress.best_score_percent;
            }

            return Math.max(
              best,
              progress.best_score_percent,
            );
          },
          null,
        );

      const averageLatestScore =
        scores.length > 0
          ? Math.round(
              scores.reduce(
                (
                  total,
                  score,
                ) =>
                  total + score,
                0,
              ) / scores.length,
            )
          : null;

      return {
        attempts,
        completedLessons,
        bestScore,
        averageLatestScore,
      };
    }, [
      lessonProgress,
    ]);


  if (isLoading) {
    return (
      <section
        className="page-container page-section"
        aria-labelledby="progress-heading"
      >
        <div className="page-heading">
          <p className="eyebrow">
            Progress
          </p>

          <h1 id="progress-heading">
            Your learning progress
          </h1>

          <p>
            Loading your learning activity...
          </p>
        </div>
      </section>
    );
  }


  if (error) {
    return (
      <section
        className="page-container page-section"
        aria-labelledby="progress-heading"
      >
        <div className="page-heading">
          <p className="eyebrow">
            Progress
          </p>

          <h1 id="progress-heading">
            Your learning progress
          </h1>

          <p>
            We could not load your learning
            progress.
          </p>
        </div>

        <div className="placeholder-panel">
          <h2>
            Progress unavailable
          </h2>

          <p>
            {error}
          </p>
        </div>
      </section>
    );
  }


  return (
    <section
      className="page-container page-section"
      aria-labelledby="progress-heading"
    >
      <div className="page-heading">
        <p className="eyebrow">
          Progress
        </p>

        <h1 id="progress-heading">
          Your learning progress
        </h1>

        <p>
          Review your ISL practice performance
          and assessment learning activity.
        </p>
      </div>


      <div className="metric-grid">
        <article className="metric-card">
          <span>
            ISL practice attempts
          </span>

          <strong>
            {analytics?.overall.total_attempts ?? 0}
          </strong>
        </article>

        <article className="metric-card">
          <span>
            ISL correct attempts
          </span>

          <strong>
            {analytics?.overall.correct_attempts ?? 0}
          </strong>
        </article>

        <article className="metric-card">
          <span>
            ISL practice accuracy
          </span>

          <strong>
            {analytics
              ? `${analytics.overall.accuracy_percent}%`
              : "0%"}
          </strong>
        </article>

        <article className="metric-card">
          <span>
            Assessment attempts
          </span>

          <strong>
            {assessmentSummary.attempts}
          </strong>
        </article>

        <article className="metric-card">
          <span>
            Lessons assessed
          </span>

          <strong>
            {assessmentSummary.completedLessons}
          </strong>
        </article>

        <article className="metric-card">
          <span>
            Best assessment score
          </span>

          <strong>
            {formatScore(
              assessmentSummary.bestScore,
            )}
          </strong>
        </article>
      </div>


      <div className="placeholder-panel">
        <h2>
          Assessment progress
        </h2>

        <p>
          Assessment results are calculated
          and persisted by the backend.
          The information below is scoped to
          your authenticated learner account.
        </p>

        {lessonProgress.length === 0 ? (
          <p>
            No assessment attempts have been
            recorded yet. Open a lesson and
            complete its assessment to start
            building assessment progress.
          </p>
        ) : (
          <div>
            <p>
              Average latest lesson score:{" "}
              <strong>
                {formatScore(
                  assessmentSummary.averageLatestScore,
                )}
              </strong>
            </p>

            <p>
              Best lesson score:{" "}
              <strong>
                {formatScore(
                  assessmentSummary.bestScore,
                )}
              </strong>
            </p>
          </div>
        )}
      </div>


      <div className="placeholder-panel">
        <h2>
          Lesson assessment progress
        </h2>

        {lessons.length === 0 ? (
          <p>
            No governed lessons are currently
            available.
          </p>
        ) : (
          <div>
            {lessons.map(
              (lesson) => {
                const progress =
                  lessonProgress.find(
                    (item) =>
                      item.lesson_id
                      === lesson.id,
                  );

                return (
                  <article
                    key={lesson.id}
                    className="metric-card"
                  >
                    <span>
                      {lesson.title}
                    </span>

                    <p>
                      Attempts:{" "}
                      {progress
                        ?.assessment_attempts
                        ?? 0}
                    </p>

                    <p>
                      Latest score:{" "}
                      {formatScore(
                        progress
                          ?.latest_score_percent
                          ?? null,
                      )}
                    </p>

                    <p>
                      Best score:{" "}
                      {formatScore(
                        progress
                          ?.best_score_percent
                          ?? null,
                      )}
                    </p>

                    <p>
                      Recommendation:{" "}
                      {formatRecommendation(
                        progress
                          ?.latest_recommendation
                          ?? null,
                      )}
                    </p>

                    <p>
                      Status:{" "}
                      {progress?.completed
                        ? "Completed"
                        : "Not attempted"}
                    </p>

                    {progress?.latest_attempt_at && (
                      <p>
                        Latest attempt:{" "}
                        {formatDate(
                          progress.latest_attempt_at,
                        )}
                      </p>
                    )}
                  </article>
                );
              },
            )}
          </div>
        )}
      </div>


      <div className="placeholder-panel">
        <h2>
          ISL learning analytics
        </h2>

        {analytics ? (
          <>
            <p>
              Letters attempted:{" "}
              <strong>
                {analytics.letters_attempted}
              </strong>
            </p>

            <p>
              Weak-letter candidates:{" "}
              <strong>
                {analytics.weak_letter_count}
              </strong>
            </p>

            <p>
              Low-confidence attempts:{" "}
              <strong>
                {analytics.low_confidence_attempts}
              </strong>
            </p>

            {analytics.weak_letters.length > 0 && (
              <div>
                <h3>
                  Areas requiring more practice
                </h3>

                {analytics.weak_letters.map(
                  (letter) => (
                    <article
                      key={letter.target_letter}
                      className="metric-card"
                    >
                      <span>
                        Letter{" "}
                        {letter.target_letter}
                      </span>

                      <p>
                        Accuracy:{" "}
                        {letter.accuracy_percent}%
                      </p>

                      <p>
                        Attempts:{" "}
                        {letter.total_attempts}
                      </p>

                      <p>
                        {letter.reason}
                      </p>
                    </article>
                  ),
                )}
              </div>
            )}
          </>
        ) : (
          <p>
            No ISL analytics are available yet.
          </p>
        )}
      </div>


      <div className="placeholder-panel">
        <h2>
          Recent ISL practice
        </h2>

        {!analytics ||
        analytics.recent_attempts.length === 0 ? (
          <p>
            No recent ISL practice attempts
            are available.
          </p>
        ) : (
          <div>
            {analytics.recent_attempts.map(
              (attempt) => (
                <article
                  key={attempt.id}
                  className="metric-card"
                >
                  <span>
                    Target:{" "}
                    {attempt.target_letter}
                  </span>

                  <p>
                    Predicted:{" "}
                    {attempt.predicted_letter
                      ?? "—"}
                  </p>

                  <p>
                    Result:{" "}
                    {attempt.is_correct
                      ? "Correct"
                      : "Incorrect"}
                  </p>

                  <p>
                    Confidence:{" "}
                    {attempt.confidence === null
                      ? "—"
                      : `${Math.round(
                          attempt.confidence
                          * 100,
                        )}%`}
                  </p>

                  <p>
                    {formatDate(
                      attempt.created_at,
                    )}
                  </p>
                </article>
              ),
            )}
          </div>
        )}
      </div>
    </section>
  );
}
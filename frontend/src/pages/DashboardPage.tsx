import {
  useEffect,
  useMemo,
  useState,
} from "react";

import {
  Link,
} from "react-router-dom";

import {
  useAuth,
} from "../contexts/AuthContext";

import {
  ApiError,
} from "../services/apiClient";

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


export default function DashboardPage() {
  const {
    user,
    token,
  } = useAuth();

  const [
    analytics,
    setAnalytics,
  ] = useState<
    ProgressAnalytics | null
  >(null);

  const [
    lessons,
    setLessons,
  ] = useState<
    LearningLessonSummary[]
  >([]);

  const [
    lessonProgress,
    setLessonProgress,
  ] = useState<
    LessonProgress[]
  >([]);

  const [
    isLoadingSnapshot,
    setIsLoadingSnapshot,
  ] = useState(true);

  const [
    snapshotError,
    setSnapshotError,
  ] = useState<string | null>(
    null,
  );


  useEffect(() => {
    let cancelled = false;

    async function loadLearnerSnapshot() {
      if (!token) {
        if (!cancelled) {
          setAnalytics(null);
          setLessons([]);
          setLessonProgress([]);
          setIsLoadingSnapshot(false);
        }

        return;
      }

      setIsLoadingSnapshot(true);
      setSnapshotError(null);

      try {
        const [
          analyticsResult,
          lessonsResult,
        ] = await Promise.all([
          getMyProgressAnalytics(token),
          getLearningLessons(token),
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
      } catch (error) {
        if (cancelled) {
          return;
        }

        if (error instanceof ApiError) {
          setSnapshotError(
            error.detail,
          );
        } else {
          setSnapshotError(
            "Unable to load your learning snapshot.",
          );
        }
      } finally {
        if (!cancelled) {
          setIsLoadingSnapshot(false);
        }
      }
    }

    void loadLearnerSnapshot();

    return () => {
      cancelled = true;
    };
  }, [token]);


  const assessmentSummary =
    useMemo(() => {
      const assessedLessons =
        lessonProgress.filter(
          (progress) =>
            progress.assessment_attempts > 0,
        );

      const assessmentAttempts =
        assessedLessons.reduce(
          (
            total,
            progress,
          ) =>
            total +
            progress.assessment_attempts,
          0,
        );

      const bestScore =
        assessedLessons.reduce<
          number | null
        >(
          (
            best,
            progress,
          ) => {
            if (
              progress.best_score_percent ===
              null
            ) {
              return best;
            }

            if (
              best === null ||
              progress.best_score_percent >
                best
            ) {
              return (
                progress.best_score_percent
              );
            }

            return best;
          },
          null,
        );

      const completedLessons =
        assessedLessons.filter(
          (progress) =>
            progress.completed,
        ).length;

      return {
        assessedLessons:
          assessedLessons.length,

        assessmentAttempts,

        bestScore,

        completedLessons,
      };
    }, [lessonProgress]);


  const nextLesson =
    useMemo(() => {
      const completedLessonIds =
        new Set(
          lessonProgress
            .filter(
              (progress) =>
                progress.completed,
            )
            .map(
              (progress) =>
                progress.lesson_id,
            ),
        );

      return (
        lessons
          .slice()
          .sort(
            (a, b) =>
              a.sequence -
              b.sequence,
          )
          .find(
            (lesson) =>
              !completedLessonIds.has(
                lesson.id,
              ),
          ) ??
        lessons[0] ??
        null
      );
    }, [
      lessons,
      lessonProgress,
    ]);


  return (
    <section
      className="page-container page-section"
      aria-labelledby="dashboard-heading"
    >
      <div className="page-heading">
        <p className="eyebrow">
          Learner dashboard
        </p>

        <h1 id="dashboard-heading">
          Welcome
          {user?.full_name
            ? `, ${user.full_name}`
            : ""}
        </h1>

        <p>
          Continue learning, ask questions,
          practise Indian Sign Language,
          and track your progress.
        </p>
      </div>


      <div
        className="dashboard-summary"
        aria-label="Learner account summary"
      >
        <div>
          <span className="summary-label">
            Signed in as
          </span>

          <strong>
            {user?.email ?? "Learner"}
          </strong>
        </div>

        <div>
          <span className="summary-label">
            Role
          </span>

          <strong>
            {user?.role ?? "student"}
          </strong>
        </div>

        <div>
          <span className="summary-label">
            Account
          </span>

          <strong>
            {user?.is_active
              ? "Active"
              : "Inactive"}
          </strong>
        </div>
      </div>


      <section
        className="dashboard-progress"
        aria-labelledby="dashboard-progress-heading"
      >
        <div className="page-heading">
          <p className="eyebrow">
            Learning snapshot
          </p>

          <h2 id="dashboard-progress-heading">
            Your current progress
          </h2>

          <p>
            A quick view of your recent
            learning activity.
          </p>
        </div>

        {isLoadingSnapshot ? (
          <p
            role="status"
            aria-live="polite"
          >
            Loading your learning snapshot...
          </p>
        ) : snapshotError ? (
          <div
            className="status-message"
            role="status"
          >
            <p>
              {snapshotError}
            </p>

            <Link
              to="/progress"
              className="button button--secondary"
            >
              View progress
            </Link>
          </div>
        ) : (
          <>
            <div
              className="metric-grid"
              aria-label="Learner progress summary"
            >
              <article className="metric-card">
                <span>
                  ISL practice accuracy
                </span>

                <strong>
                  {analytics
                    ? `${analytics.overall.accuracy_percent}%`
                    : "—"}
                </strong>
              </article>

              <article className="metric-card">
                <span>
                  ISL practice attempts
                </span>

                <strong>
                  {analytics
                    ? analytics.overall.total_attempts
                    : "—"}
                </strong>
              </article>

              <article className="metric-card">
                <span>
                  Assessment attempts
                </span>

                <strong>
                  {
                    assessmentSummary
                      .assessmentAttempts
                  }
                </strong>
              </article>

              <article className="metric-card">
                <span>
                  Lessons assessed
                </span>

                <strong>
                  {
                    assessmentSummary
                      .assessedLessons
                  }
                </strong>
              </article>

              <article className="metric-card">
                <span>
                  Best assessment score
                </span>

                <strong>
                  {
                    assessmentSummary
                      .bestScore !== null
                      ? `${assessmentSummary.bestScore}%`
                      : "—"
                  }
                </strong>
              </article>

              <article className="metric-card">
                <span>
                  Correct ISL attempts
                </span>

                <strong>
                  {analytics
                    ? analytics.overall.correct_attempts
                    : "—"}
                </strong>
              </article>
            </div>


            <div className="dashboard-progress-actions">
              <div>
                <p className="eyebrow">
                  Continue learning
                </p>

                <h3>
                  {nextLesson
                    ? nextLesson.title
                    : "No lesson available"}
                </h3>

                <p>
                  {nextLesson
                    ? nextLesson.description
                    : "Learning content is not currently available."}
                </p>
              </div>

              <div className="lesson-actions">
                {nextLesson && (
                  <Link
                    to="/learn"
                    className="button button--primary"
                  >
                    Continue learning
                  </Link>
                )}

                {user?.isl_enabled && (
                  <Link
                    to="/isl"
                    className="button button--secondary"
                  >
                    Practice ISL
                  </Link>
                )}

                <Link
                  to="/progress"
                  className="button button--secondary"
                >
                  View full progress
                </Link>
              </div>
            </div>
          </>
        )}
      </section>


      <div
        className="dashboard-grid"
        aria-label="Learning options"
      >
        <article className="dashboard-card">
          <div
            className="dashboard-card-icon"
            aria-hidden="true"
          >
            1
          </div>

          <h2>
            Learn
          </h2>

          <p>
            Study accessible,
            curriculum-aligned learning
            material.
          </p>

          <Link
            to="/learn"
            className="button button--primary"
          >
            Start learning
          </Link>
        </article>


        <article className="dashboard-card">
          <div
            className="dashboard-card-icon"
            aria-hidden="true"
          >
            2
          </div>

          <h2>
            Ask AI Tutor
          </h2>

          <p>
            Ask questions and receive answers
            grounded in approved learning
            material.
          </p>

          <Link
            to="/tutor"
            className="button button--primary"
          >
            Ask a question
          </Link>
        </article>


        <article className="dashboard-card">
          <div
            className="dashboard-card-icon"
            aria-hidden="true"
          >
            3
          </div>

          <h2>
            Practice ISL
          </h2>

          <p>
            Practise Indian Sign Language
            alphabet signs and receive
            feedback.
          </p>

          <Link
            to="/isl"
            className="button button--primary"
          >
            Start practice
          </Link>
        </article>


        <article className="dashboard-card">
          <div
            className="dashboard-card-icon"
            aria-hidden="true"
          >
            4
          </div>

          <h2>
            Track Progress
          </h2>

          <p>
            Review your learning activity,
            practice results, and areas that
            need more attention.
          </p>

          <Link
            to="/progress"
            className="button button--primary"
          >
            View progress
          </Link>
        </article>
      </div>


      <section
        className="dashboard-journey"
        aria-labelledby="journey-heading"
      >
        <div>
          <p className="eyebrow">
            Your learning journey
          </p>

          <h2 id="journey-heading">
            Learn → Ask → Practice → Progress
          </h2>

          <p>
            A4A Learn keeps the learner flow
            simple while keeping teacher
            support available when extra help
            is needed.
          </p>
        </div>

        <Link
          to="/reviews"
          className="button button--secondary"
        >
          View teacher support
        </Link>
      </section>
    </section>
  );
}
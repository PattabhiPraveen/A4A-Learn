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
  getLearningLesson,
  getLearningLessonISL,
  getLearningLessons,
} from "../services/learningService";

import type {
  ISLLessonManifest,
} from "../types/islContent";

import type {
  LearningLessonDetail,
  LearningLessonSummary,
} from "../types/learning";


const COURSE_ORDER = [
  "Python",
  "Artificial Intelligence",
];


export default function LearnPage() {
  const {
    token,
    user,
  } = useAuth();

  const [
    lessons,
    setLessons,
  ] = useState<
    LearningLessonSummary[]
  >([]);

  const [
    selectedLessonId,
    setSelectedLessonId,
  ] = useState("");

  const [
    selectedLesson,
    setSelectedLesson,
  ] = useState<
    LearningLessonDetail | null
  >(null);

  const [
    islManifest,
    setIslManifest,
  ] = useState<
    ISLLessonManifest | null
  >(null);

  const [
    isLoadingLessons,
    setIsLoadingLessons,
  ] = useState(true);

  const [
    isLoadingLesson,
    setIsLoadingLesson,
  ] = useState(false);

  const [
    isLoadingISL,
    setIsLoadingISL,
  ] = useState(false);

  const [
    errorMessage,
    setErrorMessage,
  ] = useState<string | null>(
    null,
  );

  const [
    islErrorMessage,
    setIslErrorMessage,
  ] = useState<string | null>(
    null,
  );


  useEffect(() => {
    let cancelled = false;

    async function loadLessons() {
      if (!token) {
        return;
      }

      setIsLoadingLessons(true);
      setErrorMessage(null);

      try {
        const result =
          await getLearningLessons(
            token,
          );

        if (cancelled) {
          return;
        }

        setLessons(result);

        if (result.length > 0) {
          setSelectedLessonId(
            result[0].id,
          );
        }
      } catch (error) {
        if (cancelled) {
          return;
        }

        if (error instanceof ApiError) {
          setErrorMessage(
            error.detail,
          );
        } else {
          setErrorMessage(
            "Unable to load learning lessons.",
          );
        }
      } finally {
        if (!cancelled) {
          setIsLoadingLessons(false);
        }
      }
    }

    void loadLessons();

    return () => {
      cancelled = true;
    };
  }, [token]);


  useEffect(() => {
    let cancelled = false;

    async function loadLesson() {
      if (
        !token ||
        !selectedLessonId
      ) {
        setSelectedLesson(null);
        return;
      }

      setIsLoadingLesson(true);
      setErrorMessage(null);

      try {
        const result =
          await getLearningLesson(
            selectedLessonId,
            token,
          );

        if (!cancelled) {
          setSelectedLesson(
            result,
          );
        }
      } catch (error) {
        if (cancelled) {
          return;
        }

        setSelectedLesson(null);

        if (error instanceof ApiError) {
          setErrorMessage(
            error.detail,
          );
        } else {
          setErrorMessage(
            "Unable to load this lesson.",
          );
        }
      } finally {
        if (!cancelled) {
          setIsLoadingLesson(false);
        }
      }
    }

    void loadLesson();

    return () => {
      cancelled = true;
    };
  }, [
    selectedLessonId,
    token,
  ]);


  useEffect(() => {
    let cancelled = false;

    async function loadISLContent() {
      setIslManifest(null);
      setIslErrorMessage(null);

      if (
        !token ||
        !selectedLessonId ||
        !user?.isl_enabled
      ) {
        setIsLoadingISL(false);
        return;
      }

      setIsLoadingISL(true);

      try {
        const result =
          await getLearningLessonISL(
            selectedLessonId,
            token,
          );

        if (!cancelled) {
          setIslManifest(result);
        }
      } catch (error) {
        if (cancelled) {
          return;
        }

        /*
         * ISL content is an additional accessible
         * teaching modality. Failure to retrieve an
         * ISL manifest must never remove the approved
         * written and visual lesson.
         */
        if (
          error instanceof ApiError &&
          error.status === 404
        ) {
          setIslErrorMessage(
            "Validated ISL learning content is not yet registered for this lesson. The written and visual lesson remains available.",
          );
        } else {
          setIslErrorMessage(
            "ISL learning content could not be loaded. The written and visual lesson remains available.",
          );
        }
      } finally {
        if (!cancelled) {
          setIsLoadingISL(false);
        }
      }
    }

    void loadISLContent();

    return () => {
      cancelled = true;
    };
  }, [
    selectedLessonId,
    token,
    user?.isl_enabled,
  ]);


  const groupedLessons =
    useMemo(() => {
      return COURSE_ORDER.map(
        (course) => ({
          course,
          lessons: lessons
            .filter(
              (lesson) =>
                lesson.course === course,
            )
            .sort(
              (a, b) =>
                a.sequence -
                b.sequence,
            ),
        }),
      ).filter(
        (group) =>
          group.lessons.length > 0,
      );
    }, [lessons]);


  function renderLessonContent(
    content: string,
  ) {
    const blocks =
      content
        .split(/\n\s*\n/)
        .map(
          (block) =>
            block.trim(),
        )
        .filter(Boolean);

    return blocks.map(
      (block, index) => {
        const lines =
          block.split("\n");

        const firstLine =
          lines[0]?.trim() ?? "";

        if (
          firstLine.startsWith("## ")
        ) {
          const heading =
            firstLine
              .replace(/^##\s+/, "")
              .trim();

          const remainingContent =
            lines
              .slice(1)
              .join("\n")
              .trim();

          return (
            <section
              key={index}
              className="lesson-section"
            >
              <h3>{heading}</h3>

              {remainingContent && (
                <p>
                  {remainingContent}
                </p>
              )}
            </section>
          );
        }

        if (
          firstLine.startsWith("### ")
        ) {
          const heading =
            firstLine
              .replace(/^###\s+/, "")
              .trim();

          const remainingContent =
            lines
              .slice(1)
              .join("\n")
              .trim();

          return (
            <section
              key={index}
              className="lesson-section"
            >
              <h4>{heading}</h4>

              {remainingContent && (
                <p>
                  {remainingContent}
                </p>
              )}
            </section>
          );
        }

        return (
          <p key={index}>
            {block}
          </p>
        );
      },
    );
  }


  function renderISLStatus() {
    if (!user?.isl_enabled) {
      return null;
    }

    if (isLoadingISL) {
      return (
        <p
          role="status"
          aria-live="polite"
        >
          Loading ISL learning support...
        </p>
      );
    }

    if (islErrorMessage) {
      return (
        <div
          className="status-message"
          role="status"
        >
          <p>
            {islErrorMessage}
          </p>

          <Link
            to="/isl"
            className="button button--secondary"
          >
            Open ISL Practice
          </Link>
        </div>
      );
    }

    if (!islManifest) {
      return null;
    }

    return (
      <>
        <p>
          {islManifest.message}
        </p>

        <p>
          <strong>
            Validated ISL segments:
          </strong>{" "}
          {islManifest.available_segments}
          {" / "}
          {islManifest.total_segments}
        </p>

        {islManifest.segments.some(
          (segment) =>
            segment.status ===
            "available",
        ) && (
          <div
            className="isl-segment-list"
            aria-label="Available ISL lesson segments"
          >
            {islManifest.segments
              .filter(
                (segment) =>
                  segment.status ===
                  "available",
              )
              .map(
                (segment) => (
                  <section
                    key={
                      segment.segment_id
                    }
                    className="isl-segment"
                  >
                    <h4>
                      {segment.heading}
                    </h4>

                    {segment.caption && (
                      <p>
                        {segment.caption}
                      </p>
                    )}

                    <p>
                      Validated ISL learning
                      asset available.
                    </p>
                  </section>
                ),
              )}
          </div>
        )}

        {islManifest.status ===
          "pending_review" && (
          <p>
            ISL teaching assets are shown
            only after validation. A4A Learn
            does not generate or invent ISL
            signs for unavailable segments.
          </p>
        )}

        <div className="lesson-actions">
          <Link
            to="/isl"
            className="button button--secondary"
          >
            Open ISL Practice
          </Link>
        </div>
      </>
    );
  }


  return (
    <section
      className="page-container page-section"
      aria-labelledby="learn-heading"
    >
      <div className="page-heading">
        <p className="eyebrow">
          Learning
        </p>

        <h1 id="learn-heading">
          Learn Python and AI
        </h1>

        <p>
          Build your technical skills
          step by step with accessible
          lessons in Python and
          Artificial Intelligence.
          Ask the AI Tutor whenever you
          need another explanation.
        </p>
      </div>

      {errorMessage && (
        <div
          className="status-message status-message--error"
          role="alert"
        >
          {errorMessage}
        </div>
      )}

      <div className="learning-layout">
        <nav
          className="lesson-list"
          aria-label="Learning curriculum"
        >
          <h2>
            Your learning path
          </h2>

          {isLoadingLessons ? (
            <p
              role="status"
              aria-live="polite"
            >
              Loading lessons...
            </p>
          ) : lessons.length === 0 ? (
            <p>
              No learning lessons are
              currently available.
            </p>
          ) : (
            groupedLessons.map(
              (group) => (
                <section
                  key={group.course}
                  className="lesson-course"
                  aria-labelledby={
                    `course-${group.course
                      .toLowerCase()
                      .replace(/\s+/g, "-")}`
                  }
                >
                  <h3
                    id={
                      `course-${group.course
                        .toLowerCase()
                        .replace(/\s+/g, "-")}`
                    }
                  >
                    {group.course}
                  </h3>

                  <div className="lesson-course-list">
                    {group.lessons.map(
                      (lesson) => {
                        const isActive =
                          selectedLessonId ===
                          lesson.id;

                        return (
                          <button
                            key={
                              lesson.id
                            }
                            type="button"
                            className={
                              isActive
                                ? "lesson-button lesson-button--active"
                                : "lesson-button"
                            }
                            aria-pressed={
                              isActive
                            }
                            onClick={() =>
                              setSelectedLessonId(
                                lesson.id,
                              )
                            }
                          >
                            <span className="lesson-button__id">
                              {
                                lesson.curriculum_id
                              }
                            </span>

                            <strong>
                              {
                                lesson.title
                              }
                            </strong>

                            <span className="lesson-button__meta">
                              {
                                lesson.level
                              }
                              {" · "}
                              {
                                lesson.estimated_minutes
                              }
                              {" min"}
                            </span>
                          </button>
                        );
                      },
                    )}
                  </div>
                </section>
              ),
            )
          )}
        </nav>

        <article
          className="lesson-content"
          aria-live="polite"
          aria-busy={
            isLoadingLesson
          }
        >
          {isLoadingLesson ? (
            <p role="status">
              Loading lesson...
            </p>
          ) : selectedLesson ? (
            <>
              <div className="lesson-header">
                <p className="eyebrow">
                  {
                    selectedLesson.course
                  }
                </p>

                <p className="lesson-curriculum-id">
                  {
                    selectedLesson.curriculum_id
                  }
                </p>

                <h2>
                  {
                    selectedLesson.title
                  }
                </h2>

                <div
                  className="lesson-meta"
                  aria-label="Lesson information"
                >
                  <span>
                    {
                      selectedLesson.level
                    }
                  </span>

                  <span
                    aria-hidden="true"
                  >
                    ·
                  </span>

                  <span>
                    {
                      selectedLesson.estimated_minutes
                    }{" "}
                    min
                  </span>
                </div>

                <p className="lesson-description">
                  {
                    selectedLesson.description
                  }
                </p>
              </div>

              <div className="lesson-body">
                {renderLessonContent(
                  selectedLesson.content,
                )}
              </div>

              {user?.isl_enabled && (
                <aside
                  className="lesson-help"
                  aria-labelledby="isl-learning-heading"
                >
                  <p className="eyebrow">
                    Accessible learning
                  </p>

                  <h3
                    id="isl-learning-heading"
                  >
                    ISL Learning
                  </h3>

                  <p>
                    Learn this topic with
                    governed Indian Sign
                    Language support when
                    validated teaching assets
                    are available.
                  </p>

                  {renderISLStatus()}
                </aside>
              )}

              <aside
                className="lesson-help"
                aria-labelledby="lesson-help-heading"
              >
                <h3
                  id="lesson-help-heading"
                >
                  Need another explanation?
                </h3>

                <p>
                  Ask the AI Tutor about
                  this lesson. It can
                  explain the topic in
                  simpler steps or give
                  you another example.
                </p>

                <Link
                  to={`/tutor?lesson_id=${encodeURIComponent(
                    selectedLesson.id,
                  )}`}
                  className="button button--primary"
                >
                  Ask AI Tutor about this lesson
                </Link>
              </aside>

              <div className="lesson-actions">
                <Link
                  to="/dashboard"
                  className="button button--secondary"
                >
                  Back to dashboard
                </Link>
              </div>
            </>
          ) : selectedLessonId ? (
            <p>
              Select another lesson or
              try again.
            </p>
          ) : (
            <p>
              Select a lesson to begin.
            </p>
          )}
        </article>
      </div>
    </section>
  );
}
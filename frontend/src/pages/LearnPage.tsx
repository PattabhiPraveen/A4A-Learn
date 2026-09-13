import {
  useState,
} from "react";

import {
  Link,
} from "react-router-dom";

import {
  getLearningLessons,
} from "../services/learningService";

export default function LearnPage() {
  const lessons =
    getLearningLessons();

  const [
    selectedLessonId,
    setSelectedLessonId,
  ] = useState(
    lessons[0]?.id ?? "",
  );

  const selectedLesson =
    lessons.find(
      (lesson) =>
        lesson.id === selectedLessonId,
    );

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
          Explore your lessons
        </h1>

        <p>
          Choose a topic and study it at
          your own pace. You can ask the
          AI Tutor when you need help.
        </p>
      </div>

      <div className="learning-layout">
        <nav
          className="lesson-list"
          aria-label="Available lessons"
        >
          <h2>Lessons</h2>

          {lessons.map((lesson) => (
            <button
              key={lesson.id}
              type="button"
              className={
                selectedLessonId === lesson.id
                  ? "lesson-button lesson-button--active"
                  : "lesson-button"
              }
              aria-pressed={
                selectedLessonId === lesson.id
              }
              onClick={() =>
                setSelectedLessonId(
                  lesson.id,
                )
              }
            >
              <strong>
                {lesson.title}
              </strong>

              <span>
                {lesson.topic}
              </span>
            </button>
          ))}
        </nav>

        <article
          className="lesson-content"
          aria-live="polite"
        >
          {selectedLesson ? (
            <>
              <p className="eyebrow">
                {selectedLesson.topic}
              </p>

              <h2>
                {selectedLesson.title}
              </h2>

              <p className="lesson-description">
                {
                  selectedLesson.description
                }
              </p>

              <div className="lesson-body">
                <p>
                  {selectedLesson.content}
                </p>
              </div>

              <div className="lesson-actions">
                <Link
                  to="/tutor"
                  className="button button--primary"
                >
                  Ask AI Tutor
                </Link>

                <Link
                  to="/dashboard"
                  className="button button--secondary"
                >
                  Back to dashboard
                </Link>
              </div>
            </>
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
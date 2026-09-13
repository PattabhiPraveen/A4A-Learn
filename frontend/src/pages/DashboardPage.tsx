import {
  Link,
} from "react-router-dom";

import {
  useAuth,
} from "../contexts/AuthContext";

export default function DashboardPage() {
  const {
    user,
  } = useAuth();

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
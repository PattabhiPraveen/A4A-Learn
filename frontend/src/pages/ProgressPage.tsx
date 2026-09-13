export default function ProgressPage() {
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
          Review your ISL practice performance and
          learning activity.
        </p>
      </div>

      <div className="metric-grid">
        <article className="metric-card">
          <span>
            Practice attempts
          </span>

          <strong>
            —
          </strong>
        </article>

        <article className="metric-card">
          <span>
            Correct attempts
          </span>

          <strong>
            —
          </strong>
        </article>

        <article className="metric-card">
          <span>
            Practice accuracy
          </span>

          <strong>
            —
          </strong>
        </article>
      </div>

      <div className="placeholder-panel">
        <h2>
          Progress analytics
        </h2>

        <p>
          Validated backend progress data will be
          connected here during Sprint 5.7.
        </p>
      </div>
    </section>
  );
}

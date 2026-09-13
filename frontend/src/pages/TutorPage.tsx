export default function TutorPage() {
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
          The AI Tutor will use approved learning
          content to provide grounded answers.
        </p>
      </div>

      <div className="placeholder-panel">
        <h2>
          Ask a question
        </h2>

        <label htmlFor="tutor-question">
          Your question
        </label>

        <textarea
          id="tutor-question"
          rows={5}
          placeholder="Type your learning question here..."
          disabled
        />

        <button
          type="button"
          className="button button--primary"
          disabled
        >
          Ask AI Tutor
        </button>

        <p className="form-help">
          AI Tutor integration will be enabled in
          Sprint 5.5.
        </p>
      </div>
    </section>
  );
}

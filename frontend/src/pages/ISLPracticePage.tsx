export default function ISLPracticePage() {
  return (
    <section
      className="page-container page-section"
      aria-labelledby="isl-heading"
    >
      <div className="page-heading">
        <p className="eyebrow">
          Indian Sign Language
        </p>

        <h1 id="isl-heading">
          Practice ISL alphabet
        </h1>

        <p>
          Practice one letter at a time and receive
          model-assisted feedback.
        </p>
      </div>

      <div className="placeholder-panel">
        <h2>
          ISL practice activity
        </h2>

        <p>
          Camera or image-based practice will be
          connected to the validated ISL prediction
          API during Sprint 5.6.
        </p>

        <button
          className="button button--primary"
          type="button"
          disabled
        >
          Start practice
        </button>
      </div>
    </section>
  );
}

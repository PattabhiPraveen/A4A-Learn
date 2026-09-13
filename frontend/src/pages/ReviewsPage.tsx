export default function ReviewsPage() {
  return (
    <section
      className="page-container page-section"
      aria-labelledby="reviews-heading"
    >
      <div className="page-heading">
        <p className="eyebrow">
          Learning support
        </p>

        <h1 id="reviews-heading">
          Teacher help and reviews
        </h1>

        <p>
          Questions or practice activities that need
          additional support will appear here.
        </p>
      </div>

      <div className="placeholder-panel">
        <h2>
          No review information loaded yet
        </h2>

        <p>
          The existing teacher-review backend workflow
          will be connected during Sprint 5.8.
        </p>
      </div>
    </section>
  );
}

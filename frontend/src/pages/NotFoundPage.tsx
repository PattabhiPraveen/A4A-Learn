import { Link } from "react-router-dom";

export default function NotFoundPage() {
  return (
    <section
      className="page-container page-section"
      aria-labelledby="not-found-heading"
    >
      <div className="placeholder-panel">
        <p className="eyebrow">
          404
        </p>

        <h1 id="not-found-heading">
          Page not found
        </h1>

        <p>
          The page you requested does not exist.
        </p>

        <Link
          to="/"
          className="button button--primary"
        >
          Return home
        </Link>
      </div>
    </section>
  );
}

import { Link } from "react-router-dom";

const features = [
  {
    title: "Curriculum-aligned learning",
    description:
      "Explore clear and reliable explanations grounded in approved learning material.",
    symbol: "01",
  },
  {
    title: "AI Tutor",
    description:
      "Ask questions and receive curriculum-grounded assistance with source awareness.",
    symbol: "02",
  },
  {
    title: "Indian Sign Language practice",
    description:
      "Practice ISL alphabet signs with guided feedback and confidence-aware support.",
    symbol: "03",
  },
  {
    title: "Track your progress",
    description:
      "Understand learning activity, practice accuracy and areas that need more attention.",
    symbol: "04",
  },
];

export default function HomePage() {
  return (
    <>
      <section
        className="hero page-container"
        aria-labelledby="home-heading"
      >
        <div className="hero__content">
          <p className="eyebrow">
            Accessible Learning for Everyone
          </p>

          <h1 id="home-heading">
            Learn with confidence.
            <span className="hero__highlight">
              {" "}
              Learn without barriers.
            </span>
          </h1>

          <p className="hero__description">
            A4A Learn combines accessible learning,
            curriculum-grounded AI assistance and
            Indian Sign Language practice in one
            learner-focused experience.
          </p>

          <div className="hero__actions">
            <Link
              to="/login"
              className="button button--primary button--large"
            >
              Get started
            </Link>

            <Link
              to="/learn"
              className="button button--secondary button--large"
            >
              Explore learning
            </Link>
          </div>
        </div>

        <div
          className="hero-panel"
          aria-label="A4A Learn learner journey"
        >
          <div className="hero-panel__badge">
            Your learning journey
          </div>

          <div className="journey">
            <div className="journey__step">
              <span aria-hidden="true">1</span>
              <strong>Learn</strong>
              <small>
                Build understanding
              </small>
            </div>

            <div className="journey__step">
              <span aria-hidden="true">2</span>
              <strong>Ask</strong>
              <small>
                Use the AI Tutor
              </small>
            </div>

            <div className="journey__step">
              <span aria-hidden="true">3</span>
              <strong>Practice</strong>
              <small>
                Improve ISL skills
              </small>
            </div>

            <div className="journey__step">
              <span aria-hidden="true">4</span>
              <strong>Progress</strong>
              <small>
                See your growth
              </small>
            </div>
          </div>

          <p className="hero-panel__message">
            Accessible. Grounded. Learner focused.
          </p>
        </div>
      </section>

      <section
        className="features-section page-container"
        aria-labelledby="features-heading"
      >
        <div className="section-heading">
          <p className="eyebrow">
            Designed for learning
          </p>

          <h2 id="features-heading">
            Everything you need in one place
          </h2>

          <p>
            A simple interface keeps the focus on
            learning rather than technology.
          </p>
        </div>

        <div className="feature-grid">
          {features.map((feature) => (
            <article
              key={feature.title}
              className="feature-card"
            >
              <span
                className="feature-card__symbol"
                aria-hidden="true"
              >
                {feature.symbol}
              </span>

              <h3>
                {feature.title}
              </h3>

              <p>
                {feature.description}
              </p>
            </article>
          ))}
        </div>
      </section>

      <section
        className="support-section page-container"
        aria-labelledby="support-heading"
      >
        <div>
          <p className="eyebrow">
            Human support when it matters
          </p>

          <h2 id="support-heading">
            AI assists. Teachers remain part of the
            learning journey.
          </h2>

          <p>
            When the learning assistant does not have
            enough evidence, or when repeated practice
            indicates that additional help may be
            useful, A4A Learn can route the interaction
            for teacher review.
          </p>
        </div>

        <Link
          to="/reviews"
          className="button button--secondary"
        >
          View help and reviews
        </Link>
      </section>
    </>
  );
}

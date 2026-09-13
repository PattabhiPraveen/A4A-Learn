import { Link } from "react-router-dom";

export default function Footer() {
  return (
    <footer className="site-footer">
      <div className="site-footer__inner">
        <div>
          <strong className="footer-brand">
            A4A Learn
          </strong>

          <p className="footer-copy">
            Accessible learning without barriers.
          </p>
        </div>

        <nav
          className="footer-links"
          aria-label="Footer navigation"
        >
          <Link to="/">
            About
          </Link>

          <Link to="/">
            Accessibility
          </Link>

          <Link to="/">
            Privacy
          </Link>

          <Link to="/">
            Help
          </Link>
        </nav>

        <p className="footer-copyright">
          © 2026 A4A Learn
        </p>
      </div>
    </footer>
  );
}

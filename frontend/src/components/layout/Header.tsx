import {
  NavLink,
  useNavigate,
} from "react-router-dom";

import {
  useAuth,
} from "../../contexts/AuthContext";

import type {
  AccessibilityProfile,
} from "../../types/auth";

interface AccessibilityLabel {
  shortLabel: string;
  ariaLabel: string;
}

function getAccessibilityLabel(
  profile: AccessibilityProfile,
): AccessibilityLabel | null {
  switch (profile) {
    case "deaf":
      return {
        shortLabel: "Deaf Learner",
        ariaLabel:
          "Accessibility profile: Deaf learner",
      };

    case "hard_of_hearing":
      return {
        shortLabel: "Hard of Hearing Learner",
        ariaLabel:
          "Accessibility profile: Hard of Hearing learner",
      };

    case "non_speaking":
      return {
        shortLabel: "Non-speaking Learner",
        ariaLabel:
          "Accessibility profile: Non-speaking learner",
      };

    case "standard":
    default:
      return null;
  }
}

export default function Header() {
  const {
    user,
    isAuthenticated,
    logout,
  } = useAuth();

  const navigate = useNavigate();

  const accessibilityLabel = user
    ? getAccessibilityLabel(
        user.accessibility_profile,
      )
    : null;

  function handleLogout() {
    logout();

    navigate("/", {
      replace: true,
    });
  }

  return (
    <header className="site-header">
      <div className="page-container header-inner">
        <NavLink
          to="/"
          className="brand"
          aria-label="A4A Learn home"
        >
          <span
            className="brand-mark"
            aria-hidden="true"
          >
            A
          </span>

          <span>
            A4A Learn
          </span>
        </NavLink>

        <nav
          className="desktop-navigation"
          aria-label="Primary navigation"
        >
          <NavLink to="/">
            Home
          </NavLink>

          {isAuthenticated && (
            <>
              <NavLink to="/dashboard">
                Dashboard
              </NavLink>

              <NavLink to="/learn">
                Learn
              </NavLink>

              <NavLink to="/tutor">
                AI Tutor
              </NavLink>

              <NavLink to="/isl">
                ISL Practice
              </NavLink>

              <NavLink to="/progress">
                Progress
              </NavLink>

              <NavLink to="/accessibility">
                Accessibility
              </NavLink>
            </>
          )}
        </nav>

        <div className="header-actions">
          {isAuthenticated && user ? (
            <>
              <div
                className="header-user"
                aria-label="Signed in user"
              >
                <span className="header-user-name">
                  {user.full_name}
                </span>

                <div className="header-user-meta">
                  <span className="header-user-role">
                    {user.role}
                  </span>

                  {user.isl_enabled && (
                    <span
                      className="accessibility-profile-icon"
                      aria-label="Indian Sign Language support enabled"
                    >
                      ISL
                    </span>
                  )}

                  {accessibilityLabel && (
                    <span
                      className="accessibility-profile-badge"
                      aria-label={
                        accessibilityLabel.ariaLabel
                      }
                    >
                      {
                        accessibilityLabel.shortLabel
                      }
                    </span>
                  )}
                </div>
              </div>

              <button
                type="button"
                className="button button--secondary"
                onClick={handleLogout}
              >
                Sign out
              </button>
            </>
          ) : (
            <>
              <NavLink
                to="/login"
                className="button button--secondary"
              >
                Sign in
              </NavLink>

              <NavLink
                to="/login"
                className="button button--primary"
              >
                Get started
              </NavLink>
            </>
          )}
        </div>
      </div>
    </header>
  );
}
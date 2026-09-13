import {
  NavLink,
  useNavigate,
} from "react-router-dom";

import {
  useAuth,
} from "../../contexts/AuthContext";

export default function Header() {
  const {
    user,
    isAuthenticated,
    logout,
  } = useAuth();

  const navigate = useNavigate();

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

                <span className="header-user-role">
                  {user.role}
                </span>
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
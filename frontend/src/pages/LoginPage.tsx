import {
  type FormEvent,
  useEffect,
  useState,
} from "react";

import {
  Navigate,
  useLocation,
  useNavigate,
} from "react-router-dom";

import {
  useAuth,
} from "../contexts/AuthContext";

import {
  ApiError,
} from "../services/apiClient";

interface LocationState {
  from?: string;
}

export default function LoginPage() {
  const {
    isAuthenticated,
    isLoading,
    login,
  } = useAuth();

  const navigate = useNavigate();
  const location = useLocation();

  const [email, setEmail] =
    useState("");

  const [password, setPassword] =
    useState("");

  const [error, setError] =
    useState<string | null>(null);

  const [isSubmitting, setIsSubmitting] =
    useState(false);

  const state =
    location.state as LocationState | null;

  const destination =
    state?.from ?? "/dashboard";

  useEffect(() => {
    setError(null);
  }, [email, password]);

  if (
    !isLoading &&
    isAuthenticated
  ) {
    return (
      <Navigate
        to="/dashboard"
        replace
      />
    );
  }

  async function handleSubmit(
    event: FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault();

    if (isSubmitting) {
      return;
    }

    const normalizedEmail =
      email.trim().toLowerCase();

    if (
      !normalizedEmail ||
      !password
    ) {
      setError(
        "Enter your email address and password.",
      );

      return;
    }

    setError(null);
    setIsSubmitting(true);

    try {
      await login(
        normalizedEmail,
        password,
      );

      navigate(
        destination,
        {
          replace: true,
        },
      );
    } catch (caughtError) {
      if (
        caughtError instanceof ApiError
      ) {
        if (
          caughtError.status === 401
        ) {
          setError(
            "The email address or password is incorrect.",
          );
        } else {
          setError(
            caughtError.detail,
          );
        }
      } else if (
        caughtError instanceof Error
      ) {
        setError(
          caughtError.message,
        );
      } else {
        setError(
          "Unable to sign in. Please try again.",
        );
      }
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <section
      className="auth-page page-container"
      aria-labelledby="login-heading"
    >
      <div className="auth-card">
        <p className="eyebrow">
          Welcome back
        </p>

        <h1 id="login-heading">
          Sign in to A4A Learn
        </h1>

        <p>
          Continue your learning journey.
        </p>

        {error && (
          <div
            className="form-error"
            role="alert"
          >
            {error}
          </div>
        )}

        <form
          onSubmit={handleSubmit}
          noValidate
        >
          <div className="form-field">
            <label htmlFor="email">
              Email address
            </label>

            <input
              id="email"
              name="email"
              type="email"
              autoComplete="email"
              value={email}
              onChange={(event) =>
                setEmail(
                  event.target.value,
                )
              }
              required
              disabled={isSubmitting}
            />
          </div>

          <div className="form-field">
            <label htmlFor="password">
              Password
            </label>

            <input
              id="password"
              name="password"
              type="password"
              autoComplete="current-password"
              value={password}
              onChange={(event) =>
                setPassword(
                  event.target.value,
                )
              }
              required
              disabled={isSubmitting}
            />
          </div>

          <button
            type="submit"
            className="button button--primary button--full"
            disabled={isSubmitting}
          >
            {isSubmitting
              ? "Signing in..."
              : "Sign in"}
          </button>
        </form>

        <p className="form-help">
          Your session is protected by the
          A4A Learn authentication service.
        </p>
      </div>
    </section>
  );
}
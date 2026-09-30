import {
  useEffect,
  useState,
} from "react";

import {
  Link,
} from "react-router-dom";

import {
  useAuth,
} from "../contexts/AuthContext";

import type {
  AccessibilityProfile,
  AccessibilityProfileUpdate,
} from "../types/auth";

interface ProfileOption {
  value: AccessibilityProfile;
  label: string;
  description: string;
}

const PROFILE_OPTIONS: ProfileOption[] = [
  {
    value: "standard",
    label: "Standard",
    description:
      "Use the standard learning experience without additional accessibility defaults.",
  },
  {
    value: "deaf",
    label: "Deaf",
    description:
      "Prioritize visual learning and Indian Sign Language support where available.",
  },
  {
    value: "hard_of_hearing",
    label: "Hard of Hearing",
    description:
      "Prioritize captions, readable transcripts, and visual learning support.",
  },
  {
    value: "non_speaking",
    label: "Non-speaking",
    description:
      "Prioritize text and visual interaction without requiring spoken responses.",
  },
];

export default function AccessibilityPreferencesPage() {
  const {
    user,
    updateAccessibilityProfile,
  } = useAuth();

  const [
    accessibilityProfile,
    setAccessibilityProfile,
  ] = useState<AccessibilityProfile>(
    user?.accessibility_profile ??
      "standard",
  );

  const [
    preferredLanguage,
    setPreferredLanguage,
  ] = useState(
    user?.preferred_language ??
      "english",
  );

  const [
    islEnabled,
    setIslEnabled,
  ] = useState(
    user?.isl_enabled ??
      false,
  );

  const [
    captionsEnabled,
    setCaptionsEnabled,
  ] = useState(
    user?.captions_enabled ??
      false,
  );

  const [
    isSaving,
    setIsSaving,
  ] = useState(false);

  const [
    successMessage,
    setSuccessMessage,
  ] = useState("");

  const [
    errorMessage,
    setErrorMessage,
  ] = useState("");

  useEffect(() => {
    if (!user) {
      return;
    }

    setAccessibilityProfile(
      user.accessibility_profile,
    );

    setPreferredLanguage(
      user.preferred_language,
    );

    setIslEnabled(
      user.isl_enabled,
    );

    setCaptionsEnabled(
      user.captions_enabled,
    );
  }, [user]);

  async function handleSubmit(
    event: React.FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault();

    setSuccessMessage("");
    setErrorMessage("");
    setIsSaving(true);

    const request:
      AccessibilityProfileUpdate = {
        accessibility_profile:
          accessibilityProfile,
        preferred_language:
          preferredLanguage,
        isl_enabled:
          islEnabled,
        captions_enabled:
          captionsEnabled,
      };

    try {
      await updateAccessibilityProfile(
        request,
      );

      setSuccessMessage(
        "Accessibility preferences saved successfully.",
      );
    } catch (error) {
      setErrorMessage(
        error instanceof Error
          ? error.message
          : "Unable to save accessibility preferences.",
      );
    } finally {
      setIsSaving(false);
    }
  }

  return (
    <main className="page-container page-section">
      <div className="accessibility-page">
        <div className="accessibility-page-heading">
          <div>
            <p className="eyebrow">
              Personalize your learning
            </p>

            <h1>
              Accessibility Preferences
            </h1>

            <p className="page-introduction">
              Choose the learning support that
              works best for you. You can change
              these preferences at any time.
            </p>
          </div>

          <Link
            to="/dashboard"
            className="button button--secondary"
          >
            Back to dashboard
          </Link>
        </div>

        <form
          className="accessibility-form"
          onSubmit={handleSubmit}
        >
          <fieldset className="accessibility-fieldset">
            <legend>
              Accessibility profile
            </legend>

            <p className="form-help-text">
              This setting personalizes your
              learning experience. It does not
              change your account permissions.
            </p>

            <div className="accessibility-profile-options">
              {PROFILE_OPTIONS.map(
                (option) => (
                  <label
                    key={option.value}
                    className={
                      accessibilityProfile ===
                      option.value
                        ? "accessibility-option accessibility-option--selected"
                        : "accessibility-option"
                    }
                  >
                    <input
                      type="radio"
                      name="accessibility-profile"
                      value={option.value}
                      checked={
                        accessibilityProfile ===
                        option.value
                      }
                      onChange={() =>
                        setAccessibilityProfile(
                          option.value,
                        )
                      }
                    />

                    <span className="accessibility-option-content">
                      <strong>
                        {option.label}
                      </strong>

                      <span>
                        {
                          option.description
                        }
                      </span>
                    </span>
                  </label>
                ),
              )}
            </div>
          </fieldset>

          <div className="form-field">
            <label htmlFor="preferred-language">
              Preferred language
            </label>

            <select
              id="preferred-language"
              value={preferredLanguage}
              onChange={(event) =>
                setPreferredLanguage(
                  event.target.value,
                )
              }
            >
              <option value="english">
                English
              </option>
            </select>

            <p className="form-help-text">
              English is currently available in
              the MVP. Additional languages can
              be introduced later.
            </p>
          </div>

          <fieldset className="accessibility-fieldset">
            <legend>
              Learning support
            </legend>

            <label className="accessibility-toggle">
              <input
                type="checkbox"
                checked={islEnabled}
                onChange={(event) =>
                  setIslEnabled(
                    event.target.checked,
                  )
                }
              />

              <span>
                <strong>
                  Indian Sign Language support
                </strong>

                <span>
                  Show ISL-supported learning
                  options where available.
                </span>
              </span>
            </label>

            <label className="accessibility-toggle">
              <input
                type="checkbox"
                checked={captionsEnabled}
                onChange={(event) =>
                  setCaptionsEnabled(
                    event.target.checked,
                  )
                }
              />

              <span>
                <strong>
                  Captions and transcripts
                </strong>

                <span>
                  Prefer captions and readable
                  transcripts for supported
                  learning media.
                </span>
              </span>
            </label>
          </fieldset>

          {successMessage && (
            <div
              className="form-message form-message--success"
              role="status"
              aria-live="polite"
            >
              {successMessage}
            </div>
          )}

          {errorMessage && (
            <div
              className="form-message form-message--error"
              role="alert"
            >
              {errorMessage}
            </div>
          )}

          <div className="accessibility-form-actions">
            <button
              type="submit"
              className="button button--primary"
              disabled={isSaving}
            >
              {isSaving
                ? "Saving..."
                : "Save preferences"}
            </button>

            <Link
              to="/dashboard"
              className="button button--secondary"
            >
              Cancel
            </Link>
          </div>
        </form>
      </div>
    </main>
  );
}
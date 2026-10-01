import {
  useEffect,
  useState,
} from "react";

import {
  useAuth,
} from "../contexts/AuthContext";

import {
  predictISLAlphabet,
} from "../services/islService";

import type {
  ISLPredictionResponse,
} from "../types/isl";


const ISL_LETTERS =
  "ABCDEFGHIJKLMNOPQRSTUVWXYZ".split("");


export default function ISLPracticePage() {
  const {
    token,
  } = useAuth();

  const [
    selectedLetter,
    setSelectedLetter,
  ] = useState("A");

  const [
    selectedFile,
    setSelectedFile,
  ] = useState<File | null>(null);

  const [
    previewUrl,
    setPreviewUrl,
  ] = useState<string | null>(null);

  const [
    result,
    setResult,
  ] = useState<ISLPredictionResponse | null>(
    null,
  );

  const [
    isSubmitting,
    setIsSubmitting,
  ] = useState(false);

  const [
    error,
    setError,
  ] = useState<string | null>(null);


  useEffect(() => {
    return () => {
      if (previewUrl) {
        URL.revokeObjectURL(
          previewUrl,
        );
      }
    };
  }, [previewUrl]);


  function handleLetterChange(
    letter: string,
  ) {
    setSelectedLetter(letter);
    setResult(null);
    setError(null);
  }


  function handleFileChange(
    event: React.ChangeEvent<HTMLInputElement>,
  ) {
    const file =
      event.target.files?.[0] ?? null;

    if (previewUrl) {
      URL.revokeObjectURL(
        previewUrl,
      );
    }

    setResult(null);
    setError(null);
    setSelectedFile(file);

    if (file) {
      setPreviewUrl(
        URL.createObjectURL(file),
      );
    } else {
      setPreviewUrl(null);
    }
  }


  async function handleSubmit(
    event: React.FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault();

    if (
      !token ||
      !selectedFile
    ) {
      setError(
        "Choose an image before submitting your ISL practice attempt.",
      );
      return;
    }

    setIsSubmitting(true);
    setError(null);
    setResult(null);

    try {
      const prediction =
        await predictISLAlphabet(
          selectedLetter,
          selectedFile,
          token,
        );

      setResult(prediction);
    } catch (requestError) {
      setError(
        requestError instanceof Error
          ? requestError.message
          : "Unable to evaluate the ISL practice attempt.",
      );
    } finally {
      setIsSubmitting(false);
    }
  }


  function resultHeading() {
    if (!result) {
      return "";
    }

    if (result.requires_human_review) {
      return "Teacher support requested";
    }

    if (!result.hand_detected) {
      return "Hand not detected";
    }

    if (result.is_correct) {
      return "Correct";
    }

    if (
      result.workflow_decision ===
      "retry"
    ) {
      return "Try again";
    }

    return "Practice feedback";
  }


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
          Select a letter, upload a clear image
          of your hand sign, and receive
          model-assisted feedback.
        </p>
      </div>


      <div className="content-card">
        <h2>
          Choose a letter
        </h2>

        <p>
          Practice one ISL alphabet letter at
          a time.
        </p>

        <div
          className="isl-letter-grid"
          role="group"
          aria-label="Choose an ISL alphabet letter"
        >
          {ISL_LETTERS.map(
            (letter) => (
              <button
                key={letter}
                type="button"
                className={
                  selectedLetter === letter
                    ? "button button--primary"
                    : "button button--secondary"
                }
                aria-pressed={
                  selectedLetter === letter
                }
                onClick={() =>
                  handleLetterChange(
                    letter,
                  )
                }
              >
                {letter}
              </button>
            ),
          )}
        </div>
      </div>


      <form
        className="content-card"
        onSubmit={handleSubmit}
      >
        <h2>
          Practice letter {selectedLetter}
        </h2>

        <p>
          Upload a JPEG or PNG image containing
          one clearly visible hand.
        </p>

        <div className="form-field">
          <label htmlFor="isl-image">
            Practice image
          </label>

          <input
            id="isl-image"
            type="file"
            accept="image/jpeg,image/png"
            onChange={handleFileChange}
          />
        </div>


        {previewUrl && (
          <div className="isl-image-preview">
            <p>
              Selected image preview
            </p>

            <img
              src={previewUrl}
              alt={
                `Preview of the image selected ` +
                `for ISL letter ${selectedLetter}`
              }
            />
          </div>
        )}


        <button
          className="button button--primary"
          type="submit"
          disabled={
            !selectedFile ||
            isSubmitting
          }
        >
          {isSubmitting
            ? "Checking sign..."
            : `Check letter ${selectedLetter}`}
        </button>
      </form>


      {error && (
        <div
          className="status-message status-message--error"
          role="alert"
        >
          <h2>
            Unable to check this attempt
          </h2>

          <p>
            {error}
          </p>
        </div>
      )}


      {result && (
        <div
          className="content-card"
          aria-live="polite"
        >
          <h2>
            {resultHeading()}
          </h2>

          <p>
            {result.message}
          </p>

          <dl className="metadata-list">
            <div>
              <dt>
                Target letter
              </dt>

              <dd>
                {result.target_letter ??
                  selectedLetter}
              </dd>
            </div>

            <div>
              <dt>
                Detected letter
              </dt>

              <dd>
                {result.predicted_label ??
                  "No usable prediction"}
              </dd>
            </div>

            <div>
              <dt>
                Confidence
              </dt>

              <dd>
                {Math.round(
                  result.confidence * 100,
                )}
                %
              </dd>
            </div>

            <div>
              <dt>
                Result
              </dt>

              <dd>
                {result.is_correct
                  ? "Correct"
                  : "Needs more practice"}
              </dd>
            </div>
          </dl>


          {result.requires_human_review && (
            <div
              className="status-message"
              role="status"
            >
              <strong>
                Teacher support
              </strong>

              <p>
                Your practice history indicates
                repeated difficulty with this
                letter. A teacher review has
                been requested.
              </p>
            </div>
          )}


          {!result.requires_human_review &&
            result.workflow_decision ===
              "retry" && (
              <p>
                Adjust your hand position and
                lighting, then upload another
                image and try again.
              </p>
            )}
        </div>
      )}


      <div className="content-card">
        <h2>
          About this activity
        </h2>

        <p>
          This activity recognizes ISL alphabet
          practice from a hand image. It does
          not translate sentences or generate
          new ISL signs.
        </p>

        <p>
          Model feedback supports practice.
          Teacher review remains available when
          repeated difficulty is detected.
        </p>
      </div>
    </section>
  );
}

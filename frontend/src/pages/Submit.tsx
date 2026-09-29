import { useState, type FormEvent } from "react";

import { ApiError, createComplaint } from "../api/client";
import type { Complaint } from "../types/domain";
import { validateComplaintDraft } from "../validation";

type SubmitPhase = "idle" | "triaging" | "done" | "error";

export function Submit() {
  const [text, setText] = useState("");
  const [location, setLocation] = useState("");
  const [reporterContact, setReporterContact] = useState("");
  const [clientErrors, setClientErrors] = useState<{ text?: string; location?: string }>({});
  const [phase, setPhase] = useState<SubmitPhase>("idle");
  const [result, setResult] = useState<Complaint | null>(null);
  const [serverError, setServerError] = useState<string | null>(null);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    const errors = validateComplaintDraft(text, location);
    setClientErrors(errors);
    if (Object.keys(errors).length > 0) {
      return;
    }

    setPhase("triaging"); // AI calls take seconds - render that honestly, no fake instant success.
    setServerError(null);

    try {
      const complaint = await createComplaint({
        text,
        location,
        reporter_contact: reporterContact || undefined,
      });
      setResult(complaint);
      setPhase("done");
    } catch (err) {
      setPhase("error");
      if (err instanceof ApiError) {
        setServerError(err.message);
      } else {
        setServerError("Something went wrong submitting your complaint. Please try again.");
      }
    }
  }

  function handleSubmitAnother() {
    setText("");
    setLocation("");
    setReporterContact("");
    setResult(null);
    setPhase("idle");
    setServerError(null);
  }

  if (phase === "done" && result) {
    return (
      <section aria-labelledby="submit-result-heading">
        <h2 id="submit-result-heading">Complaint submitted</h2>
        <p>Thank you - here is how it was triaged:</p>
        <dl className="triage-result">
          <dt>Category</dt>
          <dd data-testid="result-category">{result.category}</dd>
          <dt>Priority</dt>
          <dd data-testid="result-priority">{result.priority}</dd>
          <dt>AI summary</dt>
          <dd data-testid="result-summary">{result.ai_summary}</dd>
          <dt>Triaged by</dt>
          <dd data-testid="result-provider">{result.triaged_by}</dd>
        </dl>
        <button onClick={handleSubmitAnother}>Submit another complaint</button>
      </section>
    );
  }

  return (
    <section aria-labelledby="submit-heading">
      <h2 id="submit-heading">Report a complaint</h2>
      <form onSubmit={handleSubmit} noValidate>
        <div className="field">
          <label htmlFor="text">What's the problem?</label>
          <textarea
            id="text"
            value={text}
            onChange={(e) => setText(e.target.value)}
            disabled={phase === "triaging"}
            rows={5}
            aria-invalid={Boolean(clientErrors.text)}
            aria-describedby={clientErrors.text ? "text-error" : undefined}
          />
          {clientErrors.text && (
            <p id="text-error" role="alert" className="field-error">
              {clientErrors.text}
            </p>
          )}
        </div>

        <div className="field">
          <label htmlFor="location">Location</label>
          <input
            id="location"
            type="text"
            value={location}
            onChange={(e) => setLocation(e.target.value)}
            disabled={phase === "triaging"}
            aria-invalid={Boolean(clientErrors.location)}
            aria-describedby={clientErrors.location ? "location-error" : undefined}
          />
          {clientErrors.location && (
            <p id="location-error" role="alert" className="field-error">
              {clientErrors.location}
            </p>
          )}
        </div>

        <div className="field">
          <label htmlFor="reporter_contact">Contact (optional)</label>
          <input
            id="reporter_contact"
            type="text"
            value={reporterContact}
            onChange={(e) => setReporterContact(e.target.value)}
            disabled={phase === "triaging"}
          />
        </div>

        {serverError && (
          <p role="alert" className="server-error" data-testid="submit-server-error">
            {serverError}
          </p>
        )}

        <button type="submit" disabled={phase === "triaging"}>
          {phase === "triaging" ? "Triaging with AI…" : "Submit complaint"}
        </button>

        {phase === "triaging" && (
          <p aria-live="polite" data-testid="triaging-indicator">
            Classifying your complaint - this can take a few seconds…
          </p>
        )}
      </form>
    </section>
  );
}

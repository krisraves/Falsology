"use client";

import { FormEvent, useState } from "react";

export function ReviewDialog({
  levelLabel,
  correct,
  answered,
  onClose,
}: {
  levelLabel: string;
  correct: number;
  answered: number;
  onClose: () => void;
}) {
  const [status, setStatus] = useState<"idle" | "sending" | "sent" | "error">("idle");

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setStatus("sending");
    const form = new FormData(event.currentTarget);
    const payload = {
      rating: Number(form.get("rating") || 0),
      details: String(form.get("details") || ""),
      difficulty: levelLabel,
      sectionScore: `${correct}/${answered}`,
      page: window.location.href,
    };

    try {
      const response = await fetch("/api/review", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify(payload),
      });
      if (!response.ok) throw new Error("Review failed");
      const local = JSON.parse(localStorage.getItem("falsology-reviews") || "[]") as unknown[];
      localStorage.setItem(
        "falsology-reviews",
        JSON.stringify([...local, { ...payload, submittedAt: new Date().toISOString() }]),
      );
      setStatus("sent");
    } catch {
      setStatus("error");
    }
  }

  return (
    <div className="dialog-backdrop" role="presentation" onMouseDown={onClose}>
      <div className="dialog" role="dialog" aria-modal="true" aria-labelledby="review-title" onMouseDown={(event) => event.stopPropagation()}>
        <button className="dialog-close" onClick={onClose} aria-label="Close review dialog">×</button>
        {status === "sent" ? (
          <div className="dialog-success">
            <span className="success-icon" aria-hidden="true">✓</span>
            <h2 id="review-title">Review received</h2>
            <p>Thank you. Your feedback has been recorded.</p>
            <button className="button button-dark" onClick={onClose}>Close</button>
          </div>
        ) : (
          <form onSubmit={submit}>
            <p className="eyebrow">Review Falsology</p>
            <h2 id="review-title">How was this section?</h2>
            <p className="muted">You scored {correct} out of {answered} on {levelLabel}.</p>
            <label>
              Rating
              <select name="rating" required defaultValue="5">
                <option value="5">5 — Excellent</option>
                <option value="4">4 — Good</option>
                <option value="3">3 — Fair</option>
                <option value="2">2 — Needs work</option>
                <option value="1">1 — Poor</option>
              </select>
            </label>
            <label>
              Review
              <textarea name="details" rows={5} maxLength={1200} placeholder="What worked? What should change?" />
            </label>
            {status === "error" ? <p className="form-error">The server could not save the review. Try again.</p> : null}
            <button className="button button-dark button-full" disabled={status === "sending"}>
              {status === "sending" ? "Submitting…" : "Submit review"}
            </button>
          </form>
        )}
      </div>
    </div>
  );
}

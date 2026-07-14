"use client";

import { FormEvent, useState } from "react";

const reasons = [
  "Broken media",
  "Incorrect verdict",
  "Missing context",
  "Bad source",
  "Copyright concern",
  "Offensive content",
  "Technical problem",
  "Other",
];

export function ReportDialog({ claimId, onClose }: { claimId: string; onClose: () => void }) {
  const [status, setStatus] = useState<"idle" | "sending" | "sent" | "error">("idle");

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setStatus("sending");
    const form = new FormData(event.currentTarget);
    const payload = {
      claimId,
      reason: String(form.get("reason") || "Other"),
      details: String(form.get("details") || ""),
      page: window.location.href,
    };
    try {
      const response = await fetch("/api/report", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify(payload),
      });
      if (!response.ok) throw new Error("Report failed");
      const local = JSON.parse(localStorage.getItem("falsology-reports") || "[]") as unknown[];
      localStorage.setItem("falsology-reports", JSON.stringify([...local, { ...payload, submittedAt: new Date().toISOString() }]));
      setStatus("sent");
    } catch {
      setStatus("error");
    }
  }

  return (
    <div className="dialog-backdrop" role="presentation" onMouseDown={onClose}>
      <div className="dialog" role="dialog" aria-modal="true" aria-labelledby="report-title" onMouseDown={(event) => event.stopPropagation()}>
        <button className="dialog-close" onClick={onClose} aria-label="Close report dialog">×</button>
        {status === "sent" ? (
          <div className="dialog-success">
            <span className="success-icon" aria-hidden="true">✓</span>
            <h2 id="report-title">Report received</h2>
            <p>Thank you. The issue has been recorded for editorial review.</p>
            <button className="button button-dark" onClick={onClose}>Close</button>
          </div>
        ) : (
          <form onSubmit={submit}>
            <p className="eyebrow">Editorial review</p>
            <h2 id="report-title">Report a problem</h2>
            <p className="muted">Reports do not automatically change a verdict. They create a review record.</p>
            <label>
              Issue type
              <select name="reason" required defaultValue="Broken media">
                {reasons.map((reason) => <option key={reason}>{reason}</option>)}
              </select>
            </label>
            <label>
              What should we examine?
              <textarea name="details" rows={5} maxLength={1200} placeholder="Include the missing context, corrected source, or technical details." />
            </label>
            {status === "error" ? <p className="form-error">The server could not save the report. Try again.</p> : null}
            <button className="button button-dark button-full" disabled={status === "sending"}>
              {status === "sending" ? "Submitting…" : "Submit report"}
            </button>
          </form>
        )}
      </div>
    </div>
  );
}

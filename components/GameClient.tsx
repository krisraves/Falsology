"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import type { Claim, PlayerState, Verdict } from "@/lib/types";
import { AdSlot } from "@/components/AdSlot";
import { MediaPanel } from "@/components/MediaPanel";
import { ReportDialog } from "@/components/ReportDialog";

const EMPTY_STATE: PlayerState = {
  score: 0,
  streak: 0,
  bestStreak: 0,
  answered: 0,
  correct: 0,
  history: [],
  saved: [],
};

function readState(): PlayerState {
  try {
    const raw = localStorage.getItem("falsology-player");
    if (!raw) return EMPTY_STATE;
    return { ...EMPTY_STATE, ...(JSON.parse(raw) as Partial<PlayerState>) };
  } catch {
    return EMPTY_STATE;
  }
}

export function GameClient({
  initialClaims,
  mode = "random",
}: {
  initialClaims: Claim[];
  mode?: "random" | "daily" | "category";
}) {
  const [queue, setQueue] = useState(initialClaims);
  const [index, setIndex] = useState(0);
  const [answer, setAnswer] = useState<Verdict | null>(null);
  const [player, setPlayer] = useState<PlayerState>(EMPTY_STATE);
  const [expanded, setExpanded] = useState(false);
  const [reporting, setReporting] = useState(false);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    const timer = window.setTimeout(() => {
      setPlayer(readState());
      if (mode === "random") {
        setQueue((items) => [...items].sort(() => Math.random() - 0.5));
      }
    }, 0);
    return () => window.clearTimeout(timer);
  }, [mode]);

  const claim = queue[index % queue.length];
  const correct = answer === claim.verdict;
  const accuracy = player.answered ? Math.round((player.correct / player.answered) * 100) : 0;
  const saved = player.saved.includes(claim.id);

  const sessionLabel = useMemo(() => {
    if (mode === "daily") return `Daily challenge · ${Math.min(index + 1, queue.length)} of ${queue.length}`;
    if (mode === "category") return `Category round · ${Math.min(index + 1, queue.length)} of ${queue.length}`;
    return `Endless round · ${index + 1}`;
  }, [index, mode, queue.length]);

  function persist(next: PlayerState) {
    setPlayer(next);
    localStorage.setItem("falsology-player", JSON.stringify(next));
  }

  function choose(value: Verdict) {
    if (answer) return;
    const isCorrect = value === claim.verdict;
    const nextStreak = isCorrect ? player.streak + 1 : 0;
    const points = isCorrect ? 100 + Math.min(player.streak, 5) * 20 : 0;
    const next: PlayerState = {
      ...player,
      score: player.score + points,
      streak: nextStreak,
      bestStreak: Math.max(player.bestStreak, nextStreak),
      answered: player.answered + 1,
      correct: player.correct + (isCorrect ? 1 : 0),
      history: [
        { claimId: claim.id, answer: value, correct: isCorrect, answeredAt: new Date().toISOString() },
        ...player.history,
      ].slice(0, 100),
    };
    persist(next);
    setAnswer(value);
  }

  function nextClaim() {
    if (mode !== "random" && index >= queue.length - 1) {
      setIndex(0);
    } else {
      setIndex((value) => value + 1);
    }
    setAnswer(null);
    setExpanded(false);
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  function toggleSaved() {
    const nextSaved = saved
      ? player.saved.filter((id) => id !== claim.id)
      : [...player.saved, claim.id];
    persist({ ...player, saved: nextSaved });
  }

  async function share() {
    const url = `${window.location.origin}/claim/${claim.slug}`;
    const text = `Truth or lie? “${claim.claim}” — inspect the evidence on Falsology.`;
    try {
      if (navigator.share) await navigator.share({ title: "Falsology", text, url });
      else await navigator.clipboard.writeText(`${text} ${url}`);
      setCopied(true);
      setTimeout(() => setCopied(false), 1800);
    } catch {
      // Sharing was cancelled.
    }
  }

  return (
    <>
      <div className="game-page">
        <div className="game-topbar site-shell">
          <div>
            <p className="eyebrow">{sessionLabel}</p>
            <p className="game-topic">{claim.category} · {claim.difficulty}</p>
          </div>
          <div className="score-strip" aria-label="Player statistics">
            <span><small>Score</small><strong>{player.score}</strong></span>
            <span><small>Streak</small><strong>{player.streak}</strong></span>
            <span><small>Accuracy</small><strong>{accuracy}%</strong></span>
          </div>
        </div>

        <div className="site-shell game-layout">
          <section className="game-card">
            <div className="game-media-wrap">
              <MediaPanel claim={claim} />
              <button className="report-link" onClick={() => setReporting(true)}>⚑ Report</button>
            </div>

            <div className="game-body">
              <div className="claim-meta-row">
                <Link href={`/person/${claim.personSlug}`} className="person-link">{claim.person}</Link>
                <span>{claim.personRole}</span>
                <span>{new Date(`${claim.date}T00:00:00`).toLocaleDateString("en-US", { year: "numeric", month: "short", day: "numeric" })}</span>
              </div>
              <h1>{claim.prompt}</h1>
              <p className="claim-quote">“{claim.claim}”</p>

              {!answer ? (
                <div className="answer-grid" aria-label="Choose your answer">
                  <button className="answer-button answer-truth" onClick={() => choose("truth")}>
                    <span className="answer-symbol" aria-hidden="true">✓</span>
                    <span><strong>Truth</strong><small>The claim holds up</small></span>
                  </button>
                  <button className="answer-button answer-lie" onClick={() => choose("lie")}>
                    <span className="answer-symbol" aria-hidden="true">×</span>
                    <span><strong>Lie</strong><small>The claim falls apart</small></span>
                  </button>
                </div>
              ) : (
                <div className={`reveal reveal-${correct ? "correct" : "wrong"}`} aria-live="polite">
                  <div className="reveal-heading">
                    <span className="reveal-icon" aria-hidden="true">{correct ? "✓" : "×"}</span>
                    <div>
                      <p className="eyebrow">{correct ? "You got it" : "Not this time"}</p>
                      <h2>Verdict: {claim.verdict === "truth" ? "Truth" : "Lie"}</h2>
                    </div>
                    <span className="classification">{claim.classification}</span>
                  </div>
                  <p className="reveal-summary">{claim.shortExplanation}</p>
                  <div className="truth-box">
                    <p className="eyebrow">The fuller truth</p>
                    <p>{claim.fullTruth}</p>
                  </div>

                  <button className="expand-button" onClick={() => setExpanded((value) => !value)}>
                    {expanded ? "Hide deeper context" : "Open evidence and context"}
                    <span aria-hidden="true">{expanded ? "−" : "+"}</span>
                  </button>

                  {expanded ? (
                    <div className="deep-context">
                      <section>
                        <h3>Historical context</h3>
                        <p>{claim.context}</p>
                      </section>
                      <section>
                        <h3>Transcript excerpt</h3>
                        <blockquote>“{claim.transcript}”</blockquote>
                      </section>
                      <section className="boundary-note">
                        <h3>Editorial boundary</h3>
                        <p>{claim.editorialBoundary}</p>
                      </section>
                      <section>
                        <h3>Evidence</h3>
                        <div className="source-list">
                          {claim.sources.map((source, sourceIndex) => (
                            <a href={source.url} target="_blank" rel="noreferrer" key={source.url}>
                              <span className="source-number">{String(sourceIndex + 1).padStart(2, "0")}</span>
                              <span><strong>{source.title}</strong><small>{source.publisher} · {source.type}</small></span>
                              <span aria-hidden="true">↗</span>
                            </a>
                          ))}
                        </div>
                      </section>
                    </div>
                  ) : null}

                  <div className="reveal-actions">
                    <button className="button button-dark" onClick={nextClaim}>Next claim <span aria-hidden="true">→</span></button>
                    <button className="button button-outline" onClick={toggleSaved}>{saved ? "Saved" : "Save evidence"}</button>
                    <button className="button button-outline" onClick={share}>{copied ? "Copied" : "Share"}</button>
                  </div>
                </div>
              )}
            </div>
          </section>

          <aside className="game-sidebar">
            <AdSlot compact />
            <div className="sidebar-card">
              <p className="eyebrow">Your run</p>
              <h2>{player.correct} correct from {player.answered}</h2>
              <div className="mini-meter"><i style={{ width: `${accuracy}%` }} /></div>
              <p className="muted">Best streak: {player.bestStreak}. Saved evidence: {player.saved.length}.</p>
            </div>
            <div className="sidebar-card standards-card">
              <p className="eyebrow">Why trust a verdict?</p>
              <ul>
                <li>Full context is reviewed.</li>
                <li>Primary evidence is preferred.</li>
                <li>Uncertainty narrows the label.</li>
              </ul>
              <Link href="/methodology" className="text-link">Read the standard →</Link>
            </div>
          </aside>
        </div>
      </div>
      {reporting ? <ReportDialog claimId={claim.id} onClose={() => setReporting(false)} /> : null}
    </>
  );
}

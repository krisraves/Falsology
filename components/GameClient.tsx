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
    const raw = localStorage.getItem("falsology-detective");
    if (!raw) return EMPTY_STATE;
    return { ...EMPTY_STATE, ...(JSON.parse(raw) as Partial<PlayerState>) };
  } catch {
    return EMPTY_STATE;
  }
}

function shuffle<T>(items: T[]) {
  return [...items].sort(() => Math.random() - 0.5);
}

function balancedQueue(items: Claim[]) {
  const truths = shuffle(items.filter((item) => item.verdict === "truth"));
  const lies = shuffle(items.filter((item) => item.verdict === "lie"));
  const result: Claim[] = [];
  const truthFirst = Math.random() > 0.5;
  for (let index = 0; index < Math.max(truths.length, lies.length); index += 1) {
    const first = truthFirst ? truths[index] : lies[index];
    const second = truthFirst ? lies[index] : truths[index];
    if (first) result.push(first);
    if (second) result.push(second);
  }
  return result;
}

function rank(answered: number, accuracy: number) {
  if (answered < 5) return "Rookie Observer";
  if (accuracy >= 90) return "Master Investigator";
  if (accuracy >= 75) return "Senior Detective";
  if (accuracy >= 60) return "Case Analyst";
  return "Evidence Trainee";
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
  const [confidence, setConfidence] = useState(65);
  const [player, setPlayer] = useState<PlayerState>(EMPTY_STATE);
  const [expanded, setExpanded] = useState(false);
  const [reporting, setReporting] = useState(false);
  const [copied, setCopied] = useState(false);
  const [adBreak, setAdBreak] = useState(false);

  useEffect(() => {
    const timer = window.setTimeout(() => {
      setPlayer(readState());
      if (mode === "random") setQueue(balancedQueue(initialClaims));
    }, 0);
    return () => window.clearTimeout(timer);
  }, [initialClaims, mode]);

  const claim = queue[index % queue.length];
  const correct = answer === claim.verdict;
  const accuracy = player.answered ? Math.round((player.correct / player.answered) * 100) : 0;
  const saved = player.saved.includes(claim.id);
  const investigatorRank = rank(player.answered, accuracy);

  const sessionLabel = useMemo(() => {
    if (mode === "daily") return `Daily case · ${Math.min(index + 1, queue.length)} / ${queue.length}`;
    if (mode === "category") return `Case file · ${Math.min(index + 1, queue.length)} / ${queue.length}`;
    return `Open case · ${String(index + 1).padStart(2, "0")}`;
  }, [index, mode, queue.length]);

  function persist(next: PlayerState) {
    setPlayer(next);
    localStorage.setItem("falsology-detective", JSON.stringify(next));
  }

  function choose(value: Verdict) {
    if (answer) return;
    const isCorrect = value === claim.verdict;
    const nextStreak = isCorrect ? player.streak + 1 : 0;
    const points = isCorrect ? 100 + confidence + Math.min(player.streak, 5) * 20 : 0;
    const next: PlayerState = {
      ...player,
      score: player.score + points,
      streak: nextStreak,
      bestStreak: Math.max(player.bestStreak, nextStreak),
      answered: player.answered + 1,
      correct: player.correct + (isCorrect ? 1 : 0),
      history: [
        { claimId: claim.id, answer: value, confidence, correct: isCorrect, answeredAt: new Date().toISOString() },
        ...player.history,
      ].slice(0, 100),
    };
    persist(next);
    setAnswer(value);
  }

  function advance() {
    if (mode !== "random" && index >= queue.length - 1) setIndex(0);
    else setIndex((value) => value + 1);
    setAnswer(null);
    setExpanded(false);
    setConfidence(65);
    setAdBreak(false);
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  function nextClaim() {
    if (player.answered > 0 && player.answered % 4 === 0) setAdBreak(true);
    else advance();
  }

  function toggleSaved() {
    const nextSaved = saved
      ? player.saved.filter((id) => id !== claim.id)
      : [...player.saved, claim.id];
    persist({ ...player, saved: nextSaved });
  }

  async function share() {
    const url = `${window.location.origin}/claim/${claim.slug}`;
    const text = `Can you read this case? “${claim.claim}” — Falsology`;
    try {
      if (navigator.share) await navigator.share({ title: "Falsology", text, url });
      else await navigator.clipboard.writeText(`${text} ${url}`);
      setCopied(true);
      setTimeout(() => setCopied(false), 1800);
    } catch {
      // Sharing was cancelled.
    }
  }

  if (adBreak) {
    return (
      <main className="detective-game detective-ad-break">
        <section className="case-break-card">
          <p className="case-kicker">Evidence room break</p>
          <h1>Four cases cleared.</h1>
          <p>Take a breath. Keep your confidence lower than your evidence.</p>
          <AdSlot placement="interstitial" label="Sponsored break" />
          <button className="detective-primary" onClick={advance}>Open next case →</button>
        </section>
      </main>
    );
  }

  return (
    <>
      <main className="detective-game">
        <div className="site-shell detective-top-ad"><AdSlot placement="leaderboard" /></div>
        <div className="site-shell case-toolbar">
          <div>
            <p className="case-kicker">{sessionLabel}</p>
            <p className="case-category">{claim.caseNumber} · {claim.category} · {claim.setting}</p>
          </div>
          <div className="detective-stats" aria-label="Investigator statistics">
            <span><small>Rank</small><strong>{investigatorRank}</strong></span>
            <span><small>Streak</small><strong>{player.streak}</strong></span>
            <span><small>Accuracy</small><strong>{accuracy}%</strong></span>
          </div>
        </div>

        <div className="site-shell detective-layout">
          <section className="case-file-card">
            <div className="case-video-shell">
              <div className="case-tape-label">EVIDENCE VIDEO · {claim.media.endSeconds - claim.media.startSeconds}s</div>
              <MediaPanel key={claim.id} claim={claim} />
              <button className="report-link" onClick={() => setReporting(true)}>⚑ Report evidence</button>
            </div>

            <div className="case-file-body">
              <div className="case-person-row">
                <div className="case-avatar" aria-hidden="true">{claim.person.split(" ").map((part) => part[0]).slice(0, 2).join("")}</div>
                <div>
                  <Link href={`/person/${claim.personSlug}`}>{claim.person}</Link>
                  <span>{claim.personRole}</span>
                </div>
                <span className="case-difficulty">{claim.difficulty}</span>
              </div>

              <p className="case-instruction">Watch the statement. Ignore charisma. Test the evidence.</p>
              <blockquote className="case-statement">“{claim.claim}”</blockquote>

              {!answer ? (
                <div className="decision-panel">
                  <div className="confidence-control">
                    <label htmlFor="confidence">Confidence <strong>{confidence}%</strong></label>
                    <input id="confidence" type="range" min="50" max="95" step="5" value={confidence} onChange={(event) => setConfidence(Number(event.target.value))} />
                    <div><span>Unsure</span><span>Locked in</span></div>
                  </div>
                  <div className="detective-actions" aria-label="Choose your verdict">
                    <button className="verdict-button verdict-holds" onClick={() => choose("truth")}>
                      <span>✓</span><strong>Statement holds</strong><small>Evidence supports it</small>
                    </button>
                    <button className="verdict-button verdict-breaks" onClick={() => choose("lie")}>
                      <span>×</span><strong>Statement breaks</strong><small>Evidence contradicts it</small>
                    </button>
                  </div>
                </div>
              ) : (
                <div className={`case-reveal ${correct ? "case-correct" : "case-wrong"}`} aria-live="polite">
                  <div className="reveal-verdict-row">
                    <span className="reveal-stamp">{claim.verdict === "truth" ? "SUPPORTED" : "FALSE"}</span>
                    <div><p>{correct ? "Good read" : "Evidence missed"}</p><h2>{claim.classification}</h2></div>
                  </div>
                  <p className="reveal-summary">{claim.shortExplanation}</p>

                  <div className="signal-grid">
                    {claim.signals.slice(0, 3).map((signal, signalIndex) => (
                      <div key={signal}><span>{String(signalIndex + 1).padStart(2, "0")}</span><strong>{signal}</strong></div>
                    ))}
                  </div>

                  <div className="discernment-note"><span>Detective lesson</span><p>{claim.lesson}</p></div>
                  <AdSlot placement="verdict" label="Sponsored evidence break" />

                  <button className="evidence-toggle" onClick={() => setExpanded((value) => !value)}>
                    {expanded ? "Close case notes" : "Open case notes"}<span>{expanded ? "−" : "+"}</span>
                  </button>
                  {expanded ? (
                    <div className="case-notes">
                      <p>{claim.fullTruth}</p>
                      <p className="editorial-boundary">{claim.editorialBoundary}</p>
                      <div className="source-list">
                        {claim.sources.map((source) => (
                          <a href={source.url} target="_blank" rel="noreferrer" key={source.url}>
                            <span><strong>{source.title}</strong><small>{source.publisher} · {source.type}</small></span><b>↗</b>
                          </a>
                        ))}
                      </div>
                    </div>
                  ) : null}

                  <div className="reveal-actions">
                    <button className="detective-primary" onClick={nextClaim}>Next case →</button>
                    <button className="detective-secondary" onClick={toggleSaved}>{saved ? "Saved" : "Save case"}</button>
                    <button className="detective-secondary" onClick={share}>{copied ? "Copied" : "Share"}</button>
                  </div>
                </div>
              )}
            </div>
          </section>

          <aside className="detective-sidebar">
            <AdSlot placement="sidebar" compact />
            <section className="investigator-card">
              <p className="case-kicker">Your case board</p>
              <strong>{player.correct} / {player.answered}</strong>
              <span>correct calls</span>
              <div className="case-progress"><i style={{ width: `${accuracy}%` }} /></div>
              <small>Score {player.score} · Best streak {player.bestStreak}</small>
            </section>
            <section className="investigator-card rules-card">
              <p className="case-kicker">Discernment protocol</p>
              <ol><li>Define the exact claim.</li><li>Check the timeline.</li><li>Demand corroboration.</li><li>Separate confidence from proof.</li></ol>
              <Link href="/methodology">How verdicts work →</Link>
            </section>
          </aside>
        </div>
      </main>
      {reporting ? <ReportDialog claimId={claim.id} onClose={() => setReporting(false)} /> : null}
    </>
  );
}

"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import type { Claim, PlayerState, Verdict } from "@/lib/types";
import { AdSlot } from "@/components/AdSlot";
import { MediaPanel } from "@/components/MediaPanel";
import { ReportDialog } from "@/components/ReportDialog";
import { ReviewDialog } from "@/components/ReviewDialog";
import { lyingFacts } from "@/data/lying-facts";

const SECTION_SIZE = 4;
const EMPTY_STATE: PlayerState = {
  score: 0,
  streak: 0,
  bestStreak: 0,
  answered: 0,
  correct: 0,
  history: [],
  saved: [],
};

type SectionResult = { correct: boolean; points: number };

function readState(): PlayerState {
  try {
    const raw = localStorage.getItem("falsology-detective");
    return raw ? { ...EMPTY_STATE, ...(JSON.parse(raw) as Partial<PlayerState>) } : EMPTY_STATE;
  } catch {
    return EMPTY_STATE;
  }
}

function shuffle<T>(items: T[]) {
  const shuffled = [...items];
  for (let index = shuffled.length - 1; index > 0; index -= 1) {
    const randomIndex = Math.floor(Math.random() * (index + 1));
    [shuffled[index], shuffled[randomIndex]] = [shuffled[randomIndex], shuffled[index]];
  }
  return shuffled;
}

export function GameClient({
  initialClaims,
  mode = "random",
  levelLabel = "500 claims",
}: {
  initialClaims: Claim[];
  mode?: "random" | "daily" | "category";
  levelLabel?: string;
}) {
  const [queue, setQueue] = useState(initialClaims);
  const [index, setIndex] = useState(0);
  const [answer, setAnswer] = useState<Verdict | null>(null);
  const [player, setPlayer] = useState<PlayerState>(EMPTY_STATE);
  const [expanded, setExpanded] = useState(false);
  const [reporting, setReporting] = useState(false);
  const [reviewing, setReviewing] = useState(false);
  const [copied, setCopied] = useState(false);
  const [adBreak, setAdBreak] = useState(false);
  const [sectionResults, setSectionResults] = useState<SectionResult[]>([]);
  const [factIndex, setFactIndex] = useState(() => Math.floor(Math.random() * lyingFacts.length));

  useEffect(() => {
    const timer = window.setTimeout(() => {
      setPlayer(readState());
      if (mode === "random") setQueue(shuffle(initialClaims));
    }, 0);
    return () => window.clearTimeout(timer);
  }, [initialClaims, mode]);

  const claim = queue[index % queue.length];
  const correct = answer === claim.verdict;
  const accuracy = player.answered ? Math.round((player.correct / player.answered) * 100) : 0;
  const saved = player.saved.includes(claim.id);
  const sectionCorrect = sectionResults.filter((result) => result.correct).length;
  const sectionPoints = sectionResults.reduce((total, result) => total + result.points, 0);
  const sectionAccuracy = sectionResults.length ? Math.round((sectionCorrect / sectionResults.length) * 100) : 0;
  const fact = lyingFacts[factIndex % lyingFacts.length];

  const sessionLabel = useMemo(() => {
    if (mode === "daily") return `Daily case ${Math.min(index + 1, queue.length)} / ${queue.length}`;
    if (mode === "category") return `Case ${Math.min(index + 1, queue.length)} / ${queue.length}`;
    return `${levelLabel} · Case ${String((index % queue.length) + 1).padStart(3, "0")} / ${queue.length}`;
  }, [index, levelLabel, mode, queue.length]);

  function persist(next: PlayerState) {
    setPlayer(next);
    localStorage.setItem("falsology-detective", JSON.stringify(next));
  }

  function choose(value: Verdict) {
    if (answer) return;
    const isCorrect = value === claim.verdict;
    const nextStreak = isCorrect ? player.streak + 1 : 0;
    const points = isCorrect ? 100 + Math.min(player.streak, 5) * 20 : 0;
    persist({
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
    });
    setSectionResults((current) => [...current, { correct: isCorrect, points }]);
    setAnswer(value);
  }

  function advance() {
    if (mode !== "random" && index >= queue.length - 1) setIndex(0);
    else setIndex((value) => value + 1);
    setAnswer(null);
    setExpanded(false);
    setAdBreak(false);
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  function nextClaim() {
    if (sectionResults.length >= SECTION_SIZE) setAdBreak(true);
    else advance();
  }

  function continueDeck() {
    setSectionResults([]);
    setFactIndex((current) => (current + 1 + Math.floor(Math.random() * Math.max(1, lyingFacts.length - 1))) % lyingFacts.length);
    advance();
  }

  function reshuffleDeck() {
    setQueue(shuffle(initialClaims));
    setIndex(0);
    setAnswer(null);
    setExpanded(false);
    setAdBreak(false);
    setSectionResults([]);
    setFactIndex((current) => (current + 1) % lyingFacts.length);
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  function skipUnavailableClaim() {
    if (queue.length <= 1) return false;
    const remainingCount = queue.length - 1;
    setQueue((current) => current.filter((item) => item.id !== claim.id));
    setIndex((current) => current % remainingCount);
    setAnswer(null);
    setExpanded(false);
    setAdBreak(false);
    return true;
  }

  function toggleSaved() {
    const nextSaved = saved ? player.saved.filter((id) => id !== claim.id) : [...player.saved, claim.id];
    persist({ ...player, saved: nextSaved });
  }

  async function share() {
    const url = `${window.location.origin}/claim/${claim.slug}`;
    const text = `Truth or lie? “${claim.claim}” — Falsology`;
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
      <>
        <main className="detective-game detective-ad-break">
          <section className="case-break-card">
            <p className="case-kicker">Case break · History of deception</p>
            <h1>{fact.fact}</h1>
            <a className="text-link" href={fact.sourceUrl} target="_blank" rel="noreferrer">Source: {fact.sourceTitle} ↗</a>
            <div className="section-scorecard" aria-label="Section scorecard">
              <p className="case-kicker">Section scorecard</p>
              <div className="section-score-grid">
                <span><small>Correct</small><strong>{sectionCorrect} / {sectionResults.length}</strong></span>
                <span><small>Accuracy</small><strong>{sectionAccuracy}%</strong></span>
                <span><small>Points</small><strong>{sectionPoints}</strong></span>
                <span><small>Best streak</small><strong>{player.bestStreak}</strong></span>
              </div>
            </div>
            <AdSlot placement="interstitial" label="Sponsored break" />
            <div className="section-break-actions">
              <button className="detective-primary" onClick={continueDeck}>Continue 500-case deck →</button>
              <button className="detective-secondary" onClick={reshuffleDeck}>Reshuffle all cases</button>
              <Link className="detective-secondary" href="/archive">Browse case archive</Link>
              <button className="detective-secondary" onClick={() => setReviewing(true)}>Leave a review</button>
            </div>
          </section>
        </main>
        {reviewing ? <ReviewDialog levelLabel={levelLabel} correct={sectionCorrect} answered={sectionResults.length} onClose={() => setReviewing(false)} /> : null}
      </>
    );
  }

  return (
    <>
      <main className="detective-game simple-game">
        <div className="site-shell detective-top-ad"><AdSlot placement="leaderboard" /></div>
        <div className="site-shell case-toolbar simple-toolbar">
          <div>
            <p className="case-kicker">{sessionLabel}</p>
            <p className="case-category">{claim.category} · {claim.setting}</p>
          </div>
          <div className="detective-stats" aria-label="Game statistics">
            <span><small>Streak</small><strong>{player.streak}</strong></span>
            <span><small>Accuracy</small><strong>{accuracy}%</strong></span>
          </div>
        </div>

        <div className="site-shell detective-layout">
          <section className="case-file-card">
            <div className="case-video-shell">
              <div className="case-tape-label">ORIGINAL NARRATED CLAIM</div>
              <MediaPanel key={claim.id} claim={claim} onUnavailable={skipUnavailableClaim} />
              <button className="report-link" onClick={() => setReporting(true)}>⚑ Report</button>
            </div>

            <div className="case-file-body simple-case-body">
              <div className="case-person-row">
                <div className="case-avatar" aria-hidden="true">{claim.verdict === "truth" ? "T" : "L"}</div>
                <div>
                  <Link href={`/person/${claim.personSlug}`}>{claim.person}</Link>
                  <span>{claim.personRole}</span>
                </div>
                <span className="case-difficulty">Research deck</span>
              </div>

              {claim.contentWarning ? <p className="editorial-boundary">Content note: {claim.contentWarning}</p> : null}
              <p className="case-instruction">Listen. Decide. Check the evidence.</p>
              <blockquote className="case-statement">“{claim.claim}”</blockquote>

              {!answer ? (
                <>
                  <p className="case-instruction">Truth or lie?</p>
                  <div className="detective-actions simple-verdicts" aria-label="Choose truth or lie">
                    <button className="verdict-button verdict-breaks" onClick={() => choose("lie")}><span aria-hidden="true">L</span><strong>Lie</strong></button>
                    <button className="verdict-button verdict-holds" onClick={() => choose("truth")}><span aria-hidden="true">T</span><strong>True</strong></button>
                  </div>
                </>
              ) : (
                <div className={`case-reveal ${correct ? "case-correct" : "case-wrong"}`} aria-live="polite">
                  <div className="reveal-verdict-row">
                    <span className="reveal-stamp">{claim.verdict === "truth" ? "TRUE" : "LIE"}</span>
                    <div><p>{correct ? "Correct" : "Incorrect"}</p><h2>{claim.classification}</h2></div>
                  </div>
                  <p className="reveal-summary">{claim.shortExplanation}</p>
                  <div className="signal-grid">
                    {claim.signals.slice(0, 3).map((signal, signalIndex) => (
                      <div key={signal}><span>{String(signalIndex + 1).padStart(2, "0")}</span><strong>{signal}</strong></div>
                    ))}
                  </div>
                  <div className="discernment-note"><span>What to notice</span><p>{claim.lesson}</p></div>
                  <AdSlot placement="verdict" label="Advertisement" />
                  <button className="evidence-toggle" onClick={() => setExpanded((value) => !value)}>
                    {expanded ? "Hide evidence" : "Show evidence"}<span>{expanded ? "−" : "+"}</span>
                  </button>
                  {expanded ? (
                    <div className="case-notes">
                      <p>{claim.fullTruth}</p>
                      <p className="editorial-boundary">{claim.editorialBoundary}</p>
                      <div className="source-list">
                        {claim.sources.map((source, sourceIndex) => (
                          <a href={source.url} target="_blank" rel="noreferrer" key={`${source.url}-${sourceIndex}`}>
                            <span><strong>{source.title}</strong><small>{source.publisher}</small></span><b>↗</b>
                          </a>
                        ))}
                      </div>
                    </div>
                  ) : null}
                  <div className="reveal-actions">
                    <button className="detective-primary" onClick={nextClaim}>Next →</button>
                    <button className="detective-secondary" onClick={toggleSaved}>{saved ? "Saved" : "Save"}</button>
                    <button className="detective-secondary" onClick={share}>{copied ? "Copied" : "Share"}</button>
                  </div>
                </div>
              )}
            </div>
          </section>

          <aside className="detective-sidebar simple-sidebar">
            <AdSlot placement="sidebar" compact />
            <section className="investigator-card">
              <p className="case-kicker">Your score</p>
              <strong>{player.correct} / {player.answered}</strong>
              <span>correct</span>
              <small>{player.score} points · Best streak {player.bestStreak}</small>
            </section>
            <Link className="detective-secondary level-switch" href="/">Deck home</Link>
          </aside>
        </div>
      </main>
      {reporting ? <ReportDialog claimId={claim.id} onClose={() => setReporting(false)} /> : null}
    </>
  );
}

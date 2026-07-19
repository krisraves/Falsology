import Link from "next/link";
import { AdSlot } from "@/components/AdSlot";
import { claims } from "@/lib/claims";

const levels = [
  {
    name: "Easy",
    value: "easy",
    internal: "easy",
    label: "Start here",
    description: "Famous cases, recognizable faces, and clearer contradictions.",
    note: "Fast instincts",
  },
  {
    name: "Hard",
    value: "hard",
    internal: "medium",
    label: "Read the room",
    description: "Less familiar footage where context matters as much as the quote.",
    note: "More context",
  },
  {
    name: "Expert",
    value: "expert",
    internal: "hard",
    label: "Trust nothing",
    description: "Obscure interrogations, strange testimony, and unbelievable truths.",
    note: "Deep cuts",
  },
] as const;

export default function HomePage() {
  const featured = claims[0];
  const previews = claims.slice(1, 4);
  const truthCount = claims.filter((claim) => claim.verdict === "truth").length;
  const lieCount = claims.filter((claim) => claim.verdict === "lie").length;

  return (
    <main className="rebuild-home">
      <section className="rebuild-hero">
        <div className="site-shell rebuild-hero-grid">
          <div className="rebuild-hero-copy">
            <p className="rebuild-overline"><span /> The credibility game</p>
            <h1>Would you<br /><em>believe</em> them?</h1>
            <p className="rebuild-intro">
              Watch real interviews, interrogations, and testimony. Call truth or lie—then see what the evidence actually says.
            </p>
            <div className="rebuild-hero-actions">
              <Link href="/play?difficulty=easy" className="rebuild-primary">Play the easy deck <b>→</b></Link>
              <Link href="/play" className="rebuild-secondary">Surprise me</Link>
            </div>
            <div className="rebuild-proof-row" aria-label="Game standards">
              <span><strong>{claims.length}</strong> verified cases</span>
              <span><strong>{truthCount}/{lieCount}</strong> truth / lie</span>
              <span><strong>Sources</strong> after every answer</span>
            </div>
          </div>

          <Link href={`/claim/${featured.slug}`} className="rebuild-featured-case" aria-label={`Play the featured case about ${featured.person}`}>
            <div className="rebuild-monitor-top">
              <span>FEATURED CASE</span>
              <span>REC ●</span>
            </div>
            <div className="rebuild-monitor-screen">
              <div className="rebuild-scanlines" />
              <div className="rebuild-person-stamp">{featured.person.split(" ").map((part) => part[0]).slice(0, 2).join("")}</div>
              <blockquote>“{featured.claim}”</blockquote>
              <div className="rebuild-play-orbit"><span>▶</span></div>
            </div>
            <div className="rebuild-monitor-bottom">
              <span><strong>{featured.person}</strong><small>{featured.personRole}</small></span>
              <b>Make the call →</b>
            </div>
          </Link>
        </div>
      </section>

      <section className="rebuild-ticker" aria-label="How the game works">
        <div>
          <span>REAL FOOTAGE</span><i />
          <span>EXACT STATEMENTS</span><i />
          <span>TRUTH OR LIE</span><i />
          <span>CHECK THE RECORD</span><i />
          <span>NO BODY-LANGUAGE GIMMICKS</span><i />
          <span>REAL FOOTAGE</span>
        </div>
      </section>

      <section className="site-shell rebuild-levels" id="difficulty">
        <header className="rebuild-section-heading">
          <div>
            <p className="rebuild-overline dark"><span /> Choose your difficulty</p>
            <h2>How suspicious<br />are you feeling?</h2>
          </div>
          <p>Each deck is shuffled. Truths and lies are balanced so a pattern cannot save you.</p>
        </header>

        <div className="rebuild-level-grid">
          {levels.map((level, index) => {
            const levelClaims = claims.filter((claim) => claim.difficulty === level.internal);
            return (
              <Link href={`/play?difficulty=${level.value}`} className={`rebuild-level-card rebuild-level-${level.value}`} key={level.value}>
                <div className="rebuild-level-top">
                  <span>0{index + 1}</span>
                  <small>{level.label}</small>
                </div>
                <h3>{level.name}</h3>
                <p>{level.description}</p>
                <div className="rebuild-level-footer">
                  <span><strong>{levelClaims.length}</strong> playable now</span>
                  <span>{level.note}</span>
                  <b>Play →</b>
                </div>
              </Link>
            );
          })}
        </div>
        <p className="rebuild-review-note">New clips enter these decks only after the source, speaker, statement, timestamp, and verdict are reviewed.</p>
      </section>

      <section className="site-shell rebuild-ad-band"><AdSlot placement="leaderboard" /></section>

      <section className="rebuild-case-section">
        <div className="site-shell">
          <header className="rebuild-section-heading compact">
            <div>
              <p className="rebuild-overline"><span /> Cases on deck</p>
              <h2>One sentence can change everything.</h2>
            </div>
            <Link href="/archive">Browse the case archive →</Link>
          </header>

          <div className="rebuild-case-grid">
            {previews.map((claim, index) => (
              <Link href={`/claim/${claim.slug}`} className="rebuild-case-preview" key={claim.id}>
                <div className="rebuild-preview-index">0{index + 1}</div>
                <div className="rebuild-preview-person">
                  <span>{claim.person.split(" ").map((part) => part[0]).slice(0, 2).join("")}</span>
                  <div><strong>{claim.person}</strong><small>{claim.category}</small></div>
                </div>
                <blockquote>“{claim.claim}”</blockquote>
                <div className="rebuild-preview-footer"><span>Truth or lie?</span><b>Open case →</b></div>
              </Link>
            ))}
          </div>
        </div>
      </section>

      <section className="site-shell rebuild-process">
        <div className="rebuild-process-intro">
          <p className="rebuild-overline dark"><span /> The game</p>
          <h2>Watch.<br />Commit.<br />Find out.</h2>
          <p>No confidence slider. No hedging. Make the call before the evidence appears.</p>
        </div>
        <div className="rebuild-process-steps">
          <article><span>01</span><div><h3>Watch the exact moment</h3><p>Each clip is cut around the statement—not from the beginning of a long video.</p></div></article>
          <article><span>02</span><div><h3>Choose yes or no</h3><p>Are they lying? Your answer locks before the verdict is revealed.</p></div></article>
          <article><span>03</span><div><h3>Check what holds up</h3><p>See the timeline, corroborating records, missing context, and source links.</p></div></article>
        </div>
      </section>

      <section className="rebuild-standard">
        <div className="site-shell rebuild-standard-grid">
          <div className="rebuild-standard-mark">F</div>
          <div>
            <p className="rebuild-overline"><span /> The rule</p>
            <h2>Evidence beats vibes.</h2>
            <p>Falsology does not score facial expressions, eye contact, nervousness, or “tells.” Verdicts are based on records, timelines, admissions, physical evidence, and corroboration.</p>
          </div>
          <Link href="/methodology">Read the methodology <b>↗</b></Link>
        </div>
      </section>

      <section className="rebuild-final-cta">
        <div className="site-shell">
          <p>Think you can tell?</p>
          <h2>There is only one way to find out.</h2>
          <div>
            <Link href="/play?difficulty=easy" className="rebuild-primary">Start playing <b>→</b></Link>
            <Link href="/play?difficulty=expert" className="rebuild-secondary light">Skip to expert</Link>
          </div>
        </div>
      </section>
    </main>
  );
}

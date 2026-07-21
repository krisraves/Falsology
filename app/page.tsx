import Link from "next/link";
import { AdSlot } from "@/components/AdSlot";
import { claims } from "@/lib/claims";

export default function HomePage() {
  const featured = claims[0];
  const previews = claims.slice(1, 4);

  return (
    <main className="rebuild-home">
      <section className="rebuild-hero">
        <div className="site-shell rebuild-hero-grid">
          <div className="rebuild-hero-copy">
            <p className="rebuild-overline"><span /> The credibility game</p>
            <h1>Would you<br /><em>believe</em> them?</h1>
            <p className="rebuild-intro">
              Watch documented false statements from the ranked Falsology source. Make the call, then see what the evidence actually says.
            </p>
            <div className="rebuild-hero-actions">
              <Link href="/play" className="rebuild-primary">Play the ranked deck <b>→</b></Link>
              <Link href="/archive" className="rebuild-secondary">Browse the archive</Link>
            </div>
            <div className="rebuild-proof-row" aria-label="Game standards">
              <span><strong>{claims.length}</strong> verified ranked clips</span>
              <span><strong>One</strong> shuffled deck</span>
              <span><strong>Sources</strong> after every answer</span>
            </div>
          </div>

          <Link href={`/claim/${featured.slug}`} className="rebuild-featured-case" aria-label={`Play the featured case about ${featured.person}`}>
            <div className="rebuild-monitor-top">
              <span>FEATURED RANKED LIE</span>
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
              <b>Open case →</b>
            </div>
          </Link>
        </div>
      </section>

      <section className="rebuild-ticker" aria-label="How the game works">
        <div>
          <span>REAL FOOTAGE</span><i />
          <span>EXACT STATEMENTS</span><i />
          <span>RANKED HISTORICAL LIES</span><i />
          <span>CHECK THE RECORD</span><i />
          <span>NO BODY-LANGUAGE GIMMICKS</span><i />
          <span>REAL FOOTAGE</span>
        </div>
      </section>

      <section className="site-shell rebuild-levels" id="deck">
        <header className="rebuild-section-heading">
          <div>
            <p className="rebuild-overline dark"><span /> One unified deck</p>
            <h2>No difficulty tiers.<br />No separate queues.</h2>
          </div>
          <p>Every reviewed clip from the ranked source enters the same shuffled deck after the speaker, statement, timestamps, and evidence are verified.</p>
        </header>

        <div className="rebuild-level-grid">
          <Link href="/play" className="rebuild-level-card rebuild-level-expert">
            <div className="rebuild-level-top">
              <span>01</span>
              <small>All reviewed ranks</small>
            </div>
            <h3>Ranked Lies</h3>
            <p>One continuous deck containing every currently verified video from the 250-lie research source.</p>
            <div className="rebuild-level-footer">
              <span><strong>{claims.length}</strong> playable now</span>
              <span>Shuffled together</span>
              <b>Play →</b>
            </div>
          </Link>
        </div>
        <p className="rebuild-review-note">A ranked item is not published merely because a related video exists. The actual statement and its context window must be timestamped and reviewed.</p>
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
                <div className="rebuild-preview-footer"><span>Check the record</span><b>Open case →</b></div>
              </Link>
            ))}
          </div>
        </div>
      </section>

      <section className="site-shell rebuild-process">
        <div className="rebuild-process-intro">
          <p className="rebuild-overline dark"><span /> The game</p>
          <h2>Watch.<br />Commit.<br />Find out.</h2>
          <p>No confidence slider. No body-language scoring. Make the call before the evidence appears.</p>
        </div>
        <div className="rebuild-process-steps">
          <article><span>01</span><div><h3>Watch the exact moment</h3><p>Each clip begins ten seconds before the statement and ends ten seconds after it, limited only by the source boundaries.</p></div></article>
          <article><span>02</span><div><h3>Make the call</h3><p>Your answer locks before the evidence and historical record are revealed.</p></div></article>
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
          <h2>Open the unified ranked deck.</h2>
          <div>
            <Link href="/play" className="rebuild-primary">Start playing <b>→</b></Link>
            <Link href="/archive" className="rebuild-secondary light">Browse cases</Link>
          </div>
        </div>
      </section>
    </main>
  );
}

import Link from "next/link";
import { AdSlot } from "@/components/AdSlot";
import { claims } from "@/lib/claims";

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
            <h1>Would you<br /><em>believe</em> it?</h1>
            <p className="rebuild-intro">
              Hear 500 original narrated claims drawn from the ranked lists of important lies and unbelievable truths. Make the call, then check the evidence.
            </p>
            <div className="rebuild-hero-actions">
              <Link href="/play" className="rebuild-primary">Play all 500 <b>→</b></Link>
              <Link href="/archive" className="rebuild-secondary">Browse the archive</Link>
            </div>
            <div className="rebuild-proof-row" aria-label="Game standards">
              <span><strong>{claims.length}</strong> narrated clips</span>
              <span><strong>{truthCount}/{lieCount}</strong> truth / lie</span>
              <span><strong>Sources</strong> after every answer</span>
            </div>
          </div>

          <Link href={`/claim/${featured.slug}`} className="rebuild-featured-case" aria-label={`Play the featured claim: ${featured.claim}`}>
            <div className="rebuild-monitor-top"><span>FEATURED CLAIM</span><span>REC ●</span></div>
            <div className="rebuild-monitor-screen">
              <div className="rebuild-scanlines" />
              <div className="rebuild-person-stamp">?</div>
              <blockquote>“{featured.claim}”</blockquote>
              <div className="rebuild-play-orbit"><span>▶</span></div>
            </div>
            <div className="rebuild-monitor-bottom">
              <span><strong>Truth or lie?</strong><small>{featured.category}</small></span>
              <b>Open case →</b>
            </div>
          </Link>
        </div>
      </section>

      <section className="rebuild-ticker" aria-label="How the game works">
        <div>
          <span>500 ORIGINAL CLIPS</span><i />
          <span>250 TRUTHS</span><i />
          <span>250 LIES</span><i />
          <span>TEN-SECOND CONTEXT</span><i />
          <span>CHECK THE SOURCES</span><i />
          <span>500 ORIGINAL CLIPS</span>
        </div>
      </section>

      <section className="site-shell rebuild-levels" id="deck">
        <header className="rebuild-section-heading">
          <div>
            <p className="rebuild-overline dark"><span /> One balanced deck</p>
            <h2>All 500 claims.<br />One shuffled queue.</h2>
          </div>
          <p>The deck alternates source ranks during construction, then shuffles all 250 truths and 250 lies together for play.</p>
        </header>

        <div className="rebuild-level-grid">
          <Link href="/play" className="rebuild-level-card rebuild-level-expert">
            <div className="rebuild-level-top"><span>500</span><small>Complete research deck</small></div>
            <h3>Truth or Lie</h3>
            <p>Original Falsology narration reads every ranked claim aloud with ten seconds before and after the statement.</p>
            <div className="rebuild-level-footer">
              <span><strong>250 + 250</strong> balanced</span>
              <span>Endless shuffle</span>
              <b>Play →</b>
            </div>
          </Link>
        </div>
        <p className="rebuild-review-note">This is a playable research deck. Generated narration preserves the exact seed wording; source quality, quantitative limits, and historical nuance remain open to reports and editorial correction.</p>
      </section>

      <section className="site-shell rebuild-ad-band"><AdSlot placement="leaderboard" /></section>

      <section className="rebuild-case-section">
        <div className="site-shell">
          <header className="rebuild-section-heading compact">
            <div><p className="rebuild-overline"><span /> Cases on deck</p><h2>Some true claims sound impossible.</h2></div>
            <Link href="/archive">Browse all 500 →</Link>
          </header>
          <div className="rebuild-case-grid">
            {previews.map((claim, index) => (
              <Link href={`/claim/${claim.slug}`} className="rebuild-case-preview" key={claim.id}>
                <div className="rebuild-preview-index">{String(index + 1).padStart(2, "0")}</div>
                <div className="rebuild-preview-person">
                  <span>?</span><div><strong>{claim.category}</strong><small>{claim.setting}</small></div>
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
          <h2>Listen.<br />Commit.<br />Find out.</h2>
          <p>No confidence slider. No body-language scoring. Make the call before the evidence appears.</p>
        </div>
        <div className="rebuild-process-steps">
          <article><span>01</span><div><h3>Hear the claim</h3><p>Every generated clip reserves ten seconds before the narration, a twelve-second spoken slot, and ten seconds afterward.</p></div></article>
          <article><span>02</span><div><h3>Choose truth or lie</h3><p>The queue contains exactly 250 of each, but the order is shuffled.</p></div></article>
          <article><span>03</span><div><h3>Check what holds up</h3><p>Read the explanation, evidence confidence, and linked source records.</p></div></article>
        </div>
      </section>

      <section className="rebuild-standard">
        <div className="site-shell rebuild-standard-grid">
          <div className="rebuild-standard-mark">F</div>
          <div>
            <p className="rebuild-overline"><span /> The rule</p>
            <h2>Evidence beats plausibility.</h2>
            <p>The game is designed around claims that exploit intuition. A statement sounding ridiculous does not make it false, and sounding familiar does not make it true.</p>
          </div>
          <Link href="/methodology">Read the methodology <b>↗</b></Link>
        </div>
      </section>

      <section className="rebuild-final-cta">
        <div className="site-shell">
          <p>Think you can tell?</p>
          <h2>Five hundred chances to prove it.</h2>
          <div><Link href="/play" className="rebuild-primary">Start playing <b>→</b></Link><Link href="/archive" className="rebuild-secondary light">Browse cases</Link></div>
        </div>
      </section>
    </main>
  );
}

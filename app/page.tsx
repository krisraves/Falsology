import Link from "next/link";
import { AdSlot } from "@/components/AdSlot";
import { claims } from "@/lib/claims";

const featured = [claims.find((claim) => claim.caseNumber === "L01"), claims.find((claim) => claim.caseNumber === "T10"), claims.find((claim) => claim.caseNumber === "L23")].filter(Boolean);

export default function HomePage() {
  return (
    <main className="detective-home">
      <section className="detective-hero">
        <div className="site-shell detective-hero-grid">
          <div className="detective-hero-copy">
            <p className="case-kicker">Interactive discernment training</p>
            <h1>Everybody sounds believable <em>until the evidence arrives.</em></h1>
            <p>Watch real statements from suspects, criminals, witnesses, survivors, and public figures. Make the call. Learn what actually exposes a lie.</p>
            <div className="detective-hero-actions">
              <Link href="/play" className="detective-primary">Open your first case →</Link>
              <Link href="/methodology" className="detective-secondary">View the protocol</Link>
            </div>
            <div className="detective-proof">
              <span><strong>50</strong><small>video cases</small></span>
              <span><strong>25 / 25</strong><small>truth and lie</small></span>
              <span><strong>≤ 2 min</strong><small>per evidence clip</small></span>
            </div>
          </div>
          <div className="detective-hero-file" aria-label="Example detective case">
            <div className="file-tabs"><span>CASE 013</span><span>INTERVIEW</span><i>ACTIVE</i></div>
            <div className="file-portrait"><span>?</span><div className="scan-bar" /></div>
            <blockquote>“I have never doped.”</blockquote>
            <div className="file-checks"><span>Timeline</span><span>Corroboration</span><span>Records</span></div>
            <div className="file-verdicts"><b>STATEMENT HOLDS</b><b>STATEMENT BREAKS</b></div>
          </div>
        </div>
      </section>

      <div className="site-shell home-leaderboard"><AdSlot placement="leaderboard" /></div>

      <section className="detective-process site-shell">
        <header><p className="case-kicker">The protocol</p><h2>Do not “read body language.” Read the case.</h2></header>
        <div className="process-grid">
          <article><span>01</span><h3>Define</h3><p>Pin down the exact sentence.</p></article>
          <article><span>02</span><h3>Check</h3><p>Test the timeline and records.</p></article>
          <article><span>03</span><h3>Corroborate</h3><p>Find evidence outside the speaker.</p></article>
          <article><span>04</span><h3>Calibrate</h3><p>Match confidence to proof.</p></article>
        </div>
      </section>

      <section className="detective-cases site-shell">
        <div className="detective-section-heading">
          <div><p className="case-kicker">Inside the case board</p><h2>Real people. Narrow statements. Verifiable outcomes.</h2></div>
          <Link href="/archive">Browse all cases →</Link>
        </div>
        <div className="detective-preview-grid">
          {featured.map((claim) => claim ? (
            <Link href={`/claim/${claim.slug}`} key={claim.id} className="detective-preview-card">
              <span>{claim.caseNumber}</span>
              <small>{claim.category}</small>
              <h3>{claim.person}</h3>
              <blockquote>“{claim.claim}”</blockquote>
              <b>Open evidence →</b>
            </Link>
          ) : null)}
        </div>
      </section>

      <section className="site-shell home-inline-ad"><AdSlot placement="inline" /></section>

      <section className="discernment-mission">
        <div className="site-shell mission-grid">
          <div><p className="case-kicker">Why this exists</p><h2>The next fake will look more real than the last one.</h2></div>
          <div><p>Falsology trains habits that survive deepfakes, clipped interviews, false certainty, and manufactured outrage.</p><Link href="/play" className="detective-primary">Start training →</Link></div>
        </div>
      </section>
    </main>
  );
}

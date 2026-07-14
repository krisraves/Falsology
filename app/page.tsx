import Link from "next/link";
import { AdSlot } from "@/components/AdSlot";
import { ClaimCard } from "@/components/ClaimCard";
import { claims, categories } from "@/lib/claims";

export default function HomePage() {
  return (
    <main>
      <section className="hero">
        <div className="site-shell hero-grid">
          <div className="hero-copy">
            <p className="eyebrow eyebrow-light">An evidence-first truth game</p>
            <h1>People sound certain.<br /><em>The record is less polite.</em></h1>
            <p className="hero-lede">
              Watch a real claim, commit to <strong>Truth</strong> or <strong>Lie</strong>, then open the evidence that settles—or complicates—the answer.
            </p>
            <div className="hero-actions">
              <Link href="/play" className="button button-accent">Play a random round <span aria-hidden="true">→</span></Link>
              <Link href="/archive" className="button button-ghost">Browse the evidence</Link>
            </div>
            <div className="hero-proof">
              <span><strong>{claims.length}</strong> reviewed pilot claims</span>
              <span><strong>2+</strong> sources per verdict</span>
              <span><strong>0</strong> sign-up walls</span>
            </div>
          </div>
          <div className="hero-demo" aria-label="Example Falsology round">
            <div className="demo-topline"><span>ROUND 01</span><span>SPORTS SCANDALS</span></div>
            <div className="demo-scanlines" aria-hidden="true" />
            <div className="demo-quote">
              <span className="quote-mark">“</span>
              <p>I have never doped.</p>
              <small>Lance Armstrong · 2005</small>
            </div>
            <div className="demo-question">Truth or lie?</div>
            <div className="demo-buttons">
              <span className="demo-truth">✓ TRUTH</span>
              <span className="demo-lie">× LIE</span>
            </div>
            <div className="demo-footer"><span>Score 400</span><span>Streak 3</span></div>
          </div>
        </div>
      </section>

      <section className="ticker" aria-label="How Falsology works">
        <div className="site-shell ticker-inner">
          <span>01 WATCH THE CLAIM</span><i />
          <span>02 MAKE THE CALL</span><i />
          <span>03 OPEN THE RECORD</span><i />
          <span>04 KEEP YOUR STREAK</span>
        </div>
      </section>

      <section className="section site-shell">
        <div className="section-heading split-heading">
          <div><p className="eyebrow">Start with the record</p><h2>Claims worth checking twice</h2></div>
          <Link href="/archive" className="text-link">View all evidence →</Link>
        </div>
        <div className="claim-grid">
          {claims.slice(0, 6).map((claim) => <ClaimCard claim={claim} key={claim.id} />)}
        </div>
      </section>

      <section className="dark-section">
        <div className="site-shell category-showcase">
          <div className="category-intro">
            <p className="eyebrow eyebrow-light">Choose your blind spot</p>
            <h2>Every category teaches a different way to mislead.</h2>
            <p>Direct denials are easy. Half-truths, technical definitions and historical myths are where confidence gets expensive.</p>
            <Link href="/play" className="button button-light">Test yourself</Link>
          </div>
          <div className="category-list">
            {categories.map((category, index) => (
              <Link href={`/category/${category.slug}`} key={category.slug}>
                <span>{String(index + 1).padStart(2, "0")}</span>
                <strong>{category.name}</strong>
                <small>{claims.filter((claim) => claim.categorySlug === category.slug).length} claims</small>
                <b aria-hidden="true">↗</b>
              </Link>
            ))}
          </div>
        </div>
      </section>

      <section className="section site-shell trust-grid">
        <div className="trust-copy">
          <p className="eyebrow">Not a gotcha machine</p>
          <h2>A lie is not the same thing as a mistake.</h2>
          <p>
            Every entry separates direct falsehoods from omissions, exaggerations, disputed claims and misleading technicalities. When evidence cannot support the word “lie,” the label gets narrower.
          </p>
          <Link href="/methodology" className="button button-dark">Read the editorial method</Link>
        </div>
        <div className="principles-grid">
          <article><span>01</span><h3>Context first</h3><p>The full surrounding statement matters more than a viral cut.</p></article>
          <article><span>02</span><h3>Primary evidence</h3><p>Court records, official transcripts and original media lead the source list.</p></article>
          <article><span>03</span><h3>Narrow verdicts</h3><p>We state exactly what the evidence proves—and what it does not.</p></article>
          <article><span>04</span><h3>Corrections stay visible</h3><p>Reports create a review trail instead of disappearing into an inbox.</p></article>
        </div>
      </section>

      <section className="site-shell home-ad"><AdSlot /></section>

      <section className="final-cta">
        <div className="site-shell final-cta-inner">
          <div><p className="eyebrow eyebrow-light">One question is enough to start</p><h2>Was that actually true?</h2></div>
          <Link href="/play" className="button button-accent">Make the call <span aria-hidden="true">→</span></Link>
        </div>
      </section>
    </main>
  );
}

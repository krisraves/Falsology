import Link from "next/link";

export function Footer() {
  return (
    <footer className="site-footer">
      <div className="site-shell footer-grid">
        <div>
          <div className="brand footer-brand">
            <span className="brand-mark" aria-hidden="true">F</span>
            <span><strong>Falsology</strong><small>Watch. Decide. Verify.</small></span>
          </div>
          <p className="muted footer-copy">
            An evidence-first media-literacy game. Verdicts are written narrowly and linked to the record.
          </p>
        </div>
        <div>
          <h3>Explore</h3>
          <Link href="/play">Random play</Link>
          <Link href="/archive">Evidence archive</Link>
          <Link href="/daily-challenge/2026-07-14">Daily challenge</Link>
        </div>
        <div>
          <h3>Standards</h3>
          <Link href="/methodology">Methodology</Link>
          <Link href="/privacy">Privacy</Link>
          <Link href="/terms">Terms</Link>
        </div>
      </div>
      <div className="site-shell footer-bottom">
        <span>© {new Date().getFullYear()} Falsology</span>
        <span>Claims can be corrected. Evidence must be inspectable.</span>
      </div>
    </footer>
  );
}

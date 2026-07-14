import Link from "next/link";

export function Header() {
  return (
    <header className="site-header">
      <div className="site-shell header-inner">
        <Link href="/" className="brand" aria-label="Falsology home">
          <span className="brand-mark" aria-hidden="true">F</span>
          <span>
            <strong>Falsology</strong>
            <small>Evidence before certainty</small>
          </span>
        </Link>
        <nav className="top-nav" aria-label="Primary navigation">
          <Link href="/play">Play</Link>
          <Link href="/archive">Archive</Link>
          <Link href="/methodology">Method</Link>
          <Link href="/about">About</Link>
        </nav>
        <Link href="/play" className="button button-small button-dark">Start round</Link>
      </div>
    </header>
  );
}

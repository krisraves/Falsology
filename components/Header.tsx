import Link from "next/link";
import { auth, authConfigured, signIn, signOut } from "@/auth";

export async function Header() {
  const session = authConfigured ? await auth() : null;
  const name = session?.user?.name || session?.user?.email || "Player";

  return (
    <header className="site-header detective-header">
      <div className="site-shell header-inner">
        <Link href="/" className="brand detective-brand" aria-label="Falsology home">
          <span className="brand-mark" aria-hidden="true">F</span>
          <span>
            <strong>Falsology</strong>
            <small>Truth or lie?</small>
          </span>
        </Link>
        <nav className="top-nav" aria-label="Primary navigation">
          <Link href="/play">Play</Link>
          <Link href="/archive">Archive</Link>
          <Link href="/methodology">Method</Link>
        </nav>
        <div className="auth-controls">
          {session?.user ? (
            <>
              <span className="user-chip" title={session.user.email || undefined}>
                <i>{name.slice(0, 1).toUpperCase()}</i><b>{name.split(" ")[0]}</b>
              </span>
              <form action={async () => { "use server"; await signOut({ redirectTo: "/" }); }}>
                <button className="header-auth-button" type="submit">Sign out</button>
              </form>
            </>
          ) : authConfigured ? (
            <form action={async () => { "use server"; await signIn("google", { redirectTo: "/" }); }}>
              <button className="header-auth-button google-button" type="submit"><span aria-hidden="true">G</span> Sign in</button>
            </form>
          ) : (
            <span className="guest-chip">Guest</span>
          )}
          <Link href="/play" className="header-case-button">Play</Link>
        </div>
      </div>
    </header>
  );
}

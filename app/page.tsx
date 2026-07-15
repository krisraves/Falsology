import Link from "next/link";
import { AdSlot } from "@/components/AdSlot";
import { claims } from "@/lib/claims";

const levels = [
  {
    name: "Easy",
    value: "easy",
    internal: "easy",
    description: "Recognizable cases. Clearer evidence.",
  },
  {
    name: "Hard",
    value: "hard",
    internal: "medium",
    description: "Less familiar footage. More context.",
  },
  {
    name: "Expert",
    value: "expert",
    internal: "hard",
    description: "Obscure interrogations and unbelievable truths.",
  },
] as const;

export default function HomePage() {
  return (
    <main className="simple-home">
      <section className="simple-hero site-shell">
        <p className="simple-kicker">Truth or lie?</p>
        <h1>One clip.<br />One call.</h1>
        <p className="simple-lede">Real interviews, interrogations, and testimony. Half true. Half false.</p>

        <div className="level-grid" aria-label="Choose a difficulty level">
          {levels.map((level, index) => {
            const levelClaims = claims.filter((claim) => claim.difficulty === level.internal);
            return (
              <Link className={`level-card level-${level.value}`} href={`/play?difficulty=${level.value}`} key={level.value}>
                <span>{String(index + 1).padStart(2, "0")}</span>
                <h2>{level.name}</h2>
                <p>{level.description}</p>
                <small>{levelClaims.length} randomized cases</small>
                <b>Play →</b>
              </Link>
            );
          })}
        </div>

        <Link href="/play" className="mix-link">Mix all 50 cases</Link>
      </section>

      <section className="simple-stats site-shell" aria-label="Game facts">
        <span><strong>50</strong><small>video cases</small></span>
        <span><strong>25</strong><small>truths</small></span>
        <span><strong>25</strong><small>lies</small></span>
        <span><strong>≤45s</strong><small>per clip</small></span>
      </section>

      <section className="site-shell simple-ad"><AdSlot placement="leaderboard" /></section>

      <section className="simple-how site-shell">
        <article><span>1</span><h3>Watch</h3></article>
        <article><span>2</span><h3>Decide</h3></article>
        <article><span>3</span><h3>Check the evidence</h3></article>
      </section>

      <section className="simple-rule site-shell">
        <p>No body-language tricks. Use timelines, records, and corroboration.</p>
        <Link href="/methodology">How verdicts work →</Link>
      </section>
    </main>
  );
}

import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = {
  title: "About",
  description: "Falsology is a truth-or-lie media literacy game built around inspectable evidence.",
};

export default function AboutPage() {
  return (
    <main className="page-shell site-shell prose-page">
      <p className="eyebrow">About Falsology</p>
      <h1>A trivia game with an audit trail.</h1>
      <p className="prose-lede">
        Falsology starts with a familiar impulse: hear a confident statement and decide whether you believe it. The difference is what happens next. Every verdict opens into a source trail, transcript excerpt, historical context and a precise explanation of the label.
      </p>
      <div className="prose-grid">
        <section>
          <h2>The purpose</h2>
          <p>Make media literacy entertaining enough to practice. The game is not meant to reward cynicism. It rewards checking whether confidence, repetition and familiarity are actually evidence.</p>
        </section>
        <section>
          <h2>The audience</h2>
          <p>Casual trivia players, history fans, true-crime audiences, teachers, students and anyone who has ever discovered that a famous quote was more complicated than the meme.</p>
        </section>
        <section>
          <h2>The pilot</h2>
          <p>The current archive is intentionally small. It proves the play loop and editorial structure before the project expands into larger collections, daily challenges and reviewed community submissions.</p>
        </section>
        <section>
          <h2>The business</h2>
          <p>Reserved ad placements support an eventual ad-funded model without placing ads over media or answer controls. Traffic, trust and return visits take priority over short-term ad density.</p>
        </section>
      </div>
      <div className="prose-cta">
        <div><p className="eyebrow">Ready?</p><h2>Make a call, then inspect the record.</h2></div>
        <Link href="/play" className="button button-dark">Start playing →</Link>
      </div>
    </main>
  );
}

import type { Metadata } from "next";
import { GameClient } from "@/components/GameClient";
import { claims } from "@/lib/claims";

function dailyClaims(date: string) {
  let seed = Array.from(date).reduce((value, character) => ((value * 31) + character.charCodeAt(0)) >>> 0, 2166136261);
  const shuffled = [...claims];
  for (let index = shuffled.length - 1; index > 0; index -= 1) {
    seed = (seed * 1664525 + 1013904223) >>> 0;
    const target = seed % (index + 1);
    [shuffled[index], shuffled[target]] = [shuffled[target], shuffled[index]];
  }
  return shuffled.slice(0, Math.min(5, shuffled.length));
}

export async function generateMetadata({ params }: { params: Promise<{ date: string }> }): Promise<Metadata> {
  const { date } = await params;
  return {
    title: `Daily Challenge — ${date}`,
    description: `Five sourced Truth-or-Lie claims selected for ${date}.`,
  };
}

export default async function DailyChallengePage({ params }: { params: Promise<{ date: string }> }) {
  const { date } = await params;
  const challengeDate = /^\d{4}-\d{2}-\d{2}$/.test(date) ? date : new Date().toISOString().slice(0, 10);
  return (
    <main>
      <section className="daily-banner">
        <div className="site-shell">
          <p className="eyebrow eyebrow-light">Daily challenge</p>
          <h1>{new Date(`${challengeDate}T12:00:00Z`).toLocaleDateString("en-US", { weekday: "long", year: "numeric", month: "long", day: "numeric", timeZone: "UTC" })}</h1>
          <p>Five claims. One shared sequence. No account required.</p>
        </div>
      </section>
      <GameClient initialClaims={dailyClaims(challengeDate)} mode="daily" />
    </main>
  );
}

import Link from "next/link";
import type { Claim } from "@/lib/types";

export function ClaimCard({ claim }: { claim: Claim }) {
  return (
    <article className="claim-card">
      <div className="claim-card-top">
        <span className={`verdict-dot verdict-${claim.verdict}`}>{claim.verdict.toUpperCase()}</span>
        <span className="difficulty">{claim.difficulty}</span>
      </div>
      <p className="eyebrow">{claim.category}</p>
      <h3>“{claim.claim}”</h3>
      <p className="muted">{claim.person} · {new Date(`${claim.date}T00:00:00`).getFullYear()}</p>
      <p>{claim.shortExplanation}</p>
      <div className="claim-card-links">
        <Link href={`/claim/${claim.slug}`} className="text-link">Inspect evidence →</Link>
        <Link href={`/person/${claim.personSlug}`} className="soft-link">More from {claim.person}</Link>
      </div>
    </article>
  );
}

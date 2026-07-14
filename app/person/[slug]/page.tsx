import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { ClaimCard } from "@/components/ClaimCard";
import { getClaimsByPerson, people } from "@/lib/claims";

export function generateStaticParams() {
  return people.map((person) => ({ slug: person.slug }));
}

export async function generateMetadata({ params }: { params: Promise<{ slug: string }> }): Promise<Metadata> {
  const { slug } = await params;
  const person = people.find((item) => item.slug === slug);
  return person ? { title: person.name, description: `Sourced claim records involving ${person.name}.` } : {};
}

export default async function PersonPage({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  const person = people.find((item) => item.slug === slug);
  const personClaims = getClaimsByPerson(slug);
  if (!person || !personClaims.length) notFound();
  const correctLabels = personClaims.reduce((sum, claim) => sum + (claim.verdict === "truth" ? 1 : 0), 0);
  return (
    <main className="page-shell site-shell">
      <header className="person-hero">
        <div className="person-monogram" aria-hidden="true">{person.name.split(" ").map((part) => part[0]).slice(0, 2).join("")}</div>
        <div>
          <p className="eyebrow">Person archive</p>
          <h1>{person.name}</h1>
          <p>{personClaims[0].personRole}</p>
        </div>
        <div className="person-stats">
          <span><strong>{personClaims.length}</strong><small>claims</small></span>
          <span><strong>{personClaims.length - correctLabels}</strong><small>false or misleading</small></span>
        </div>
      </header>
      <div className="section-heading split-heading">
        <div><p className="eyebrow">Reviewed record</p><h2>Claims involving {person.name}</h2></div>
        <Link href="/play" className="button button-dark button-small">Play random</Link>
      </div>
      <div className="claim-grid">{personClaims.map((claim) => <ClaimCard claim={claim} key={claim.id} />)}</div>
    </main>
  );
}

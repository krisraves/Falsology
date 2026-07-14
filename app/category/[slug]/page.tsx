import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { ClaimCard } from "@/components/ClaimCard";
import { GameClient } from "@/components/GameClient";
import { categories, getClaimsByCategory } from "@/lib/claims";

export function generateStaticParams() {
  return categories.map((category) => ({ slug: category.slug }));
}

export async function generateMetadata({ params }: { params: Promise<{ slug: string }> }): Promise<Metadata> {
  const { slug } = await params;
  const category = categories.find((item) => item.slug === slug);
  return category ? { title: category.name, description: `Play and inspect sourced claims in ${category.name}.` } : {};
}

export default async function CategoryPage({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  const category = categories.find((item) => item.slug === slug);
  const categoryClaims = getClaimsByCategory(slug);
  if (!category || !categoryClaims.length) notFound();
  return (
    <main>
      <section className="page-shell site-shell compact-page-hero">
        <p className="eyebrow">Category</p>
        <h1>{category.name}</h1>
        <p>{categoryClaims.length} reviewed claim{categoryClaims.length === 1 ? "" : "s"}. Play the collection or inspect each evidence record.</p>
        <div className="hero-actions hero-actions-dark">
          <Link href="#category-game" className="button button-dark">Play this category</Link>
          <Link href="/archive" className="button button-outline">Back to archive</Link>
        </div>
      </section>
      <div id="category-game"><GameClient initialClaims={categoryClaims} mode="category" /></div>
      <section className="section site-shell">
        <div className="section-heading"><p className="eyebrow">Evidence pages</p><h2>Every claim in this category</h2></div>
        <div className="claim-grid">{categoryClaims.map((claim) => <ClaimCard claim={claim} key={claim.id} />)}</div>
      </section>
    </main>
  );
}

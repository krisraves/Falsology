import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { AdSlot } from "@/components/AdSlot";
import { ClaimCard } from "@/components/ClaimCard";
import { ClaimReportButton } from "@/components/ClaimReportButton";
import { MediaPanel } from "@/components/MediaPanel";
import { claims, getClaim } from "@/lib/claims";
import { siteUrl } from "@/lib/site";

export function generateStaticParams() {
  return claims.map((claim) => ({ slug: claim.slug }));
}

export async function generateMetadata({ params }: { params: Promise<{ slug: string }> }): Promise<Metadata> {
  const { slug } = await params;
  const claim = getClaim(slug);
  if (!claim) return {};
  return {
    title: `${claim.person}: “${claim.claim}” — ${claim.verdict === "truth" ? "Truth" : "Lie"}`,
    description: claim.shortExplanation,
    alternates: { canonical: siteUrl(`/claim/${claim.slug}`) },
    openGraph: {
      title: `Verdict: ${claim.verdict.toUpperCase()} — ${claim.person}`,
      description: claim.shortExplanation,
      type: "article",
      url: siteUrl(`/claim/${claim.slug}`),
    },
  };
}

export default async function ClaimPage({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  const claim = getClaim(slug);
  if (!claim) notFound();
  const related = claims
    .filter((item) => item.id !== claim.id && (item.categorySlug === claim.categorySlug || item.personSlug === claim.personSlug))
    .slice(0, 3);

  const jsonLd = {
    "@context": "https://schema.org",
    "@type": "ClaimReview",
    url: siteUrl(`/claim/${claim.slug}`),
    datePublished: claim.reviewedAt,
    itemReviewed: {
      "@type": "Claim",
      author: { "@type": "Person", name: claim.person },
      datePublished: claim.date,
      appearance: { "@type": "CreativeWork", url: claim.media.url || siteUrl(`/claim/${claim.slug}`) },
    },
    claimReviewed: claim.claim,
    reviewRating: {
      "@type": "Rating",
      ratingValue: claim.verdict === "truth" ? 5 : 1,
      bestRating: 5,
      worstRating: 1,
      alternateName: claim.verdict === "truth" ? "True" : "False or materially misleading",
    },
    author: { "@type": "Organization", name: "Falsology" },
  };

  return (
    <main className="claim-page">
      <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }} />
      <div className="site-shell claim-page-grid">
        <article className="claim-article">
          <nav className="breadcrumbs" aria-label="Breadcrumb">
            <Link href="/archive">Archive</Link><span>/</span>
            <Link href={`/category/${claim.categorySlug}`}>{claim.category}</Link><span>/</span>
            <span>{claim.person}</span>
          </nav>

          <header className="claim-header">
            <div className="claim-header-meta">
              <span className={`verdict-pill verdict-${claim.verdict}`}>Verdict: {claim.verdict}</span>
              <span>{claim.classification}</span>
              <span>{claim.difficulty}</span>
            </div>
            <h1>“{claim.claim}”</h1>
            <p className="claim-byline">
              <Link href={`/person/${claim.personSlug}`}>{claim.person}</Link> · {claim.personRole} · {new Date(`${claim.date}T00:00:00`).toLocaleDateString("en-US", { year: "numeric", month: "long", day: "numeric" })}
            </p>
          </header>

          <MediaPanel claim={claim} />

          <section className="verdict-panel">
            <p className="eyebrow">The call</p>
            <h2>{claim.verdict === "truth" ? "The claim holds up." : "The claim does not hold up."}</h2>
            <p className="large-copy">{claim.shortExplanation}</p>
          </section>

          <section className="article-section">
            <h2>The fuller truth</h2>
            <p>{claim.fullTruth}</p>
          </section>

          <section className="article-section">
            <h2>Historical context</h2>
            <p>{claim.context}</p>
          </section>

          <section className="transcript-panel">
            <p className="eyebrow">Transcript excerpt</p>
            <blockquote>“{claim.transcript}”</blockquote>
          </section>

          <section className="article-section boundary-section">
            <h2>What this verdict does—and does not—say</h2>
            <p>{claim.editorialBoundary}</p>
          </section>

          <section className="article-section">
            <div className="split-heading">
              <div><p className="eyebrow">Source trail</p><h2>Evidence used</h2></div>
              <span className="reviewed-date">Reviewed {claim.reviewedAt}</span>
            </div>
            <div className="source-list source-list-large">
              {claim.sources.map((source, index) => (
                <a href={source.url} target="_blank" rel="noreferrer" key={source.url}>
                  <span className="source-number">{String(index + 1).padStart(2, "0")}</span>
                  <span>
                    <strong>{source.title}</strong>
                    <small>{source.publisher} · {source.type} source</small>
                    {source.note ? <p>{source.note}</p> : null}
                  </span>
                  <span aria-hidden="true">↗</span>
                </a>
              ))}
            </div>
          </section>

          <div className="claim-actions">
            <Link href="/play" className="button button-dark">Play another claim →</Link>
            <ClaimReportButton claimId={claim.id} />
          </div>
        </article>

        <aside className="claim-aside">
          <AdSlot compact />
          <div className="sidebar-card">
            <p className="eyebrow">Classification</p>
            <h3>{claim.classification}</h3>
            <p className="muted">Difficulty: {claim.difficulty}</p>
          </div>
          <div className="sidebar-card">
            <p className="eyebrow">Filed under</p>
            <div className="tag-list">
              {claim.tags.map((tag) => <span key={tag}>{tag}</span>)}
            </div>
          </div>
        </aside>
      </div>

      {related.length ? (
        <section className="related-section site-shell">
          <div className="section-heading split-heading">
            <div><p className="eyebrow">Keep checking</p><h2>Related evidence</h2></div>
          </div>
          <div className="claim-grid">{related.map((item) => <ClaimCard claim={item} key={item.id} />)}</div>
        </section>
      ) : null}
    </main>
  );
}

import type { Metadata } from "next";
import { ArchiveSearch } from "@/components/ArchiveSearch";
import { claims } from "@/lib/claims";

export const metadata: Metadata = {
  title: "Evidence Archive",
  description: "Search sourced historical claims, verdicts, transcripts and primary evidence.",
};

export default function ArchivePage() {
  return (
    <main className="page-shell site-shell">
      <header className="page-hero">
        <p className="eyebrow">Evidence archive</p>
        <h1>Search the claims.<br /><em>Open the receipts.</em></h1>
        <p>Every game question also exists as a permanent, indexable evidence page.</p>
      </header>
      <ArchiveSearch claims={claims} />
    </main>
  );
}

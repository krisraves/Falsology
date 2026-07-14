"use client";

import { useMemo, useState } from "react";
import type { Claim } from "@/lib/types";
import { ClaimCard } from "@/components/ClaimCard";

export function ArchiveSearch({ claims }: { claims: Claim[] }) {
  const [query, setQuery] = useState("");
  const [category, setCategory] = useState("all");
  const categories = useMemo(
    () => Array.from(new Set(claims.map((claim) => claim.category))).sort(),
    [claims],
  );
  const filtered = useMemo(() => {
    const needle = query.trim().toLowerCase();
    return claims.filter((claim) => {
      const categoryMatch = category === "all" || claim.category === category;
      const textMatch = !needle || [claim.person, claim.claim, claim.category, ...claim.tags]
        .join(" ")
        .toLowerCase()
        .includes(needle);
      return categoryMatch && textMatch;
    });
  }, [category, claims, query]);

  return (
    <>
      <div className="archive-controls">
        <label className="search-box">
          <span aria-hidden="true">⌕</span>
          <input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search people, claims, or topics" />
        </label>
        <label>
          <span className="sr-only">Filter by category</span>
          <select value={category} onChange={(event) => setCategory(event.target.value)}>
            <option value="all">All categories</option>
            {categories.map((item) => <option key={item}>{item}</option>)}
          </select>
        </label>
      </div>
      <p className="result-count">{filtered.length} evidence record{filtered.length === 1 ? "" : "s"}</p>
      <div className="claim-grid">
        {filtered.map((claim) => <ClaimCard claim={claim} key={claim.id} />)}
      </div>
      {!filtered.length ? <div className="empty-state"><h2>No matching evidence</h2><p>Try a broader person, topic, or category.</p></div> : null}
    </>
  );
}

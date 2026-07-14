import type { MetadataRoute } from "next";
import { categories, claims, people } from "@/lib/claims";
import { siteUrl } from "@/lib/site";

export default function sitemap(): MetadataRoute.Sitemap {
  const now = new Date();
  const staticPages = ["", "/play", "/archive", "/methodology", "/about", "/privacy", "/terms"].map((path) => ({
    url: siteUrl(path),
    lastModified: now,
    changeFrequency: path === "" || path === "/play" ? "weekly" as const : "monthly" as const,
    priority: path === "" ? 1 : path === "/play" ? 0.9 : 0.7,
  }));
  return [
    ...staticPages,
    ...claims.map((claim) => ({ url: siteUrl(`/claim/${claim.slug}`), lastModified: new Date(`${claim.reviewedAt}T12:00:00Z`), changeFrequency: "monthly" as const, priority: 0.8 })),
    ...categories.map((category) => ({ url: siteUrl(`/category/${category.slug}`), lastModified: now, changeFrequency: "monthly" as const, priority: 0.65 })),
    ...people.map((person) => ({ url: siteUrl(`/person/${person.slug}`), lastModified: now, changeFrequency: "monthly" as const, priority: 0.6 })),
  ];
}

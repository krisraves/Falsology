import rawAllCases from "@/data/all-500-cases.json";
import type { Claim } from "@/lib/types";

export const claims = rawAllCases as Claim[];

export function getClaim(slug: string) {
  return claims.find((claim) => claim.slug === slug);
}

export function getClaimsByCategory(slug: string) {
  return claims.filter((claim) => claim.categorySlug === slug);
}

export function getClaimsByPerson(slug: string) {
  return claims.filter((claim) => claim.personSlug === slug);
}

export const categories = Array.from(
  new Map(claims.map((claim) => [claim.categorySlug, claim.category])).entries(),
).map(([slug, name]) => ({ slug, name }));

export const people = Array.from(
  new Map(claims.map((claim) => [claim.personSlug, claim.person])).entries(),
).map(([slug, name]) => ({ slug, name }));

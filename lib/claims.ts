import part01 from "@/data/cases/part01.json";
import part02 from "@/data/cases/part02.json";
import part03 from "@/data/cases/part03.json";
import part04 from "@/data/cases/part04.json";
import part05 from "@/data/cases/part05.json";
import part06 from "@/data/cases/part06.json";
import part07 from "@/data/cases/part07.json";
import part08 from "@/data/cases/part08.json";
import part09 from "@/data/cases/part09.json";
import part10 from "@/data/cases/part10.json";
import type { Claim } from "@/lib/types";

export const claims = [
  ...part01,
  ...part02,
  ...part03,
  ...part04,
  ...part05,
  ...part06,
  ...part07,
  ...part08,
  ...part09,
  ...part10,
] as Claim[];

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

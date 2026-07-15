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
import rawOverrides from "@/data/case-overrides.json";
import rawFinalReplacements from "@/data/direct-footage-replacements.json";
import rawObscureReplacements from "@/data/obscure-case-replacements.json";
import rawDifficultyMap from "@/data/difficulty-map.json";
import type { Claim, ClaimMedia, Difficulty } from "@/lib/types";

type ClaimOverride = Partial<Omit<Claim, "media">> & { media?: Partial<ClaimMedia> };

const baseClaims = [
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

const overrides = rawOverrides as Record<string, ClaimOverride>;
const finalReplacements = rawFinalReplacements as Record<string, ClaimOverride>;
const obscureReplacements = rawObscureReplacements as Record<string, ClaimOverride>;
const difficultyMap = rawDifficultyMap as Record<string, Difficulty>;

function applyOverride(claim: Claim, override?: ClaimOverride): Claim {
  if (!override) return claim;
  return {
    ...claim,
    ...override,
    media: {
      ...claim.media,
      ...(override.media ?? {}),
    },
  } as Claim;
}

export const claims = baseClaims.map((claim) => {
  const reviewed = applyOverride(claim, overrides[claim.caseNumber]);
  const direct = applyOverride(reviewed, finalReplacements[claim.caseNumber]);
  const obscure = applyOverride(direct, obscureReplacements[claim.caseNumber]);
  return {
    ...obscure,
    difficulty: difficultyMap[claim.caseNumber] ?? obscure.difficulty,
  };
});

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

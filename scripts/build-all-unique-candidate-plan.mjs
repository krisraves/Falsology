import { readFileSync, readdirSync, writeFileSync } from "node:fs";
import { join, resolve } from "node:path";

const caseDir = resolve("data/cases");
const baseClaims = readdirSync(caseDir)
  .filter((name) => /^part\d{2}\.json$/.test(name))
  .sort()
  .flatMap((name) => JSON.parse(readFileSync(join(caseDir, name), "utf8")));
const layers = [
  "case-overrides.json",
  "direct-footage-replacements.json",
  "obscure-case-replacements.json",
  "english-weird-replacements.json",
].map((name) => JSON.parse(readFileSync(resolve("data", name), "utf8")));
const historical = JSON.parse(readFileSync("validation/historical-statement-candidates.json", "utf8"));

function apply(claim, override = {}) {
  return { ...claim, ...override, media: { ...(claim.media ?? {}), ...(override.media ?? {}) } };
}

const resolved = baseClaims.map((base) => layers.reduce((claim, layer) => apply(claim, layer[base.caseNumber]), base));
const cases = resolved.map((claim) => {
  const audit = historical.cases?.[claim.caseNumber];
  const candidates = Array.isArray(audit?.candidates) ? audit.candidates : [];
  return {
    caseNumber: claim.caseNumber,
    verdict: claim.verdict,
    person: claim.person,
    originalClaim: claim.claim,
    youtubeId: claim.media.youtubeId,
    videoDurationSeconds: claim.media.videoDurationSeconds,
    sourceKind: claim.media.sourceKind,
    candidateCount: candidates.length,
    bestCandidate: candidates[0] ?? null,
    alternateCandidates: candidates.slice(1, 5),
    auditFailure: historical.failures?.[claim.caseNumber] ?? null,
  };
});
const ids = cases.map((item) => item.youtubeId);
writeFileSync(
  "validation/all-unique-candidate-plan.json",
  JSON.stringify({
    total: cases.length,
    uniqueVideoCount: new Set(ids).size,
    withCandidates: cases.filter((item) => item.bestCandidate).length,
    withoutCandidates: cases.filter((item) => !item.bestCandidate).map((item) => item.caseNumber),
    cases,
  }, null, 2) + "\n",
);
console.log(`All-source plan: ${new Set(ids).size} unique videos; ${cases.filter((item) => item.bestCandidate).length}/${cases.length} cases have exact candidates.`);

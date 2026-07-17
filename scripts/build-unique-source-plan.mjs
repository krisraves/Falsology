import { readFileSync, readdirSync, writeFileSync, mkdirSync } from "node:fs";
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
const exact = JSON.parse(readFileSync(resolve("data/exact-statement-overrides.json"), "utf8"));

function apply(claim, override = {}) {
  return { ...claim, ...override, media: { ...(claim.media ?? {}), ...(override.media ?? {}) } };
}

const preExact = Object.fromEntries(baseClaims.map((base) => {
  const resolved = layers.reduce((claim, layer) => apply(claim, layer[base.caseNumber]), base);
  return [base.caseNumber, resolved];
}));

const grouped = new Map();
for (const [caseNumber, claim] of Object.entries(exact)) {
  const id = claim.media.youtubeId;
  if (!grouped.has(id)) grouped.set(id, []);
  grouped.get(id).push(caseNumber);
}

const replacements = [];
for (const [duplicateVideoId, cases] of grouped.entries()) {
  if (cases.length < 2) continue;
  for (const caseNumber of cases.slice(1)) {
    const original = preExact[caseNumber];
    replacements.push({
      caseNumber,
      verdict: original.verdict,
      originalPerson: original.person,
      originalClaim: original.claim,
      originalTranscript: original.transcript,
      youtubeId: original.media.youtubeId,
      startSeconds: original.media.startSeconds,
      endSeconds: original.media.endSeconds,
      videoDurationSeconds: original.media.videoDurationSeconds,
      sourceKind: original.media.sourceKind,
      duplicateVideoId,
    });
  }
}

const usedByKeptCases = new Set();
for (const cases of grouped.values()) {
  const kept = cases[0];
  usedByKeptCases.add(exact[kept].media.youtubeId);
}
for (const replacement of replacements) {
  replacement.conflictsWithKeptVideo = usedByKeptCases.has(replacement.youtubeId);
}

mkdirSync("validation", { recursive: true });
writeFileSync(
  "validation/unique-source-plan.json",
  JSON.stringify({ replacementCount: replacements.length, replacements }, null, 2) + "\n",
);
console.log(`Planned ${replacements.length} unique-source restorations.`);

import { readFileSync, readdirSync } from "node:fs";
import { join, resolve } from "node:path";

const directory = resolve("data/cases");
const filenames = readdirSync(directory).filter((name) => /^part\d{2}\.json$/.test(name)).sort();
const baseClaims = filenames.flatMap((name) => JSON.parse(readFileSync(join(directory, name), "utf8")));
const overrides = JSON.parse(readFileSync(resolve("data/case-overrides.json"), "utf8"));
const directReplacements = JSON.parse(readFileSync(resolve("data/direct-footage-replacements.json"), "utf8"));
const obscureReplacements = JSON.parse(readFileSync(resolve("data/obscure-case-replacements.json"), "utf8"));
const englishReplacements = JSON.parse(readFileSync(resolve("data/english-weird-replacements.json"), "utf8"));
const exactOverrides = JSON.parse(readFileSync(resolve("data/exact-statement-overrides.json"), "utf8"));
const activeCaseNumbers = JSON.parse(readFileSync(resolve("data/active-case-numbers.json"), "utf8"));
const difficultyMap = JSON.parse(readFileSync(resolve("data/difficulty-map.json"), "utf8"));
const activeSet = new Set(activeCaseNumbers);

function applyOverride(claim, override = {}) {
  return { ...claim, ...override, media: { ...(claim.media ?? {}), ...(override.media ?? {}) } };
}

const claims = baseClaims
  .map((claim) => {
    const reviewed = applyOverride(claim, overrides[claim.caseNumber]);
    const direct = applyOverride(reviewed, directReplacements[claim.caseNumber]);
    const obscure = applyOverride(direct, obscureReplacements[claim.caseNumber]);
    const english = applyOverride(obscure, englishReplacements[claim.caseNumber]);
    const exact = applyOverride(english, exactOverrides[claim.caseNumber]);
    return { ...exact, difficulty: difficultyMap[claim.caseNumber] ?? exact.difficulty };
  })
  .filter((claim) => activeSet.has(claim.caseNumber));

const failures = [];
const finite = (value) => typeof value === "number" && Number.isFinite(value);
const unique = (values) => new Set(values).size === values.length;
const normalize = (value) => String(value ?? "").toLowerCase().replace(/[^a-z0-9]+/g, " ").trim();
const allowedSourceKinds = new Set([
  "raw-interview", "archival-public-appeal", "archival-interview", "police-interrogation",
  "prison-interview", "archival-prison-interview", "direct-conference-interview", "direct-interview",
  "direct-presentation", "public-statement", "corporate-statement", "public-speech", "press-briefing",
  "congressional-testimony", "courtroom-evidence-playback", "courtroom-confession", "courtroom-statement",
  "police-confession", "court-testimony", "raw-release-statement", "documentary-interview", "direct-confession",
]);

if (filenames.length !== 10) failures.push(`Expected 10 case files, found ${filenames.length}.`);
if (baseClaims.length !== 50) failures.push(`Expected 50 archived cases, found ${baseClaims.length}.`);
if (!Array.isArray(activeCaseNumbers) || activeCaseNumbers.length !== 12) failures.push(`Expected 12 active cases, found ${activeCaseNumbers.length}.`);
if (!unique(activeCaseNumbers)) failures.push("Active case numbers are not unique.");
if (claims.length !== activeCaseNumbers.length) failures.push(`Expected ${activeCaseNumbers.length} active cases, found ${claims.length}.`);
if (!unique(claims.map((claim) => claim.id))) failures.push("Case IDs are not unique.");
if (!unique(claims.map((claim) => claim.slug))) failures.push("Case slugs are not unique.");
if (!unique(claims.map((claim) => claim.caseNumber))) failures.push("Case numbers are not unique.");
if (!unique(claims.map((claim) => claim.media?.youtubeId))) failures.push("Every active case must use a different YouTube video.");

const truths = claims.filter((claim) => claim.verdict === "truth").length;
const lies = claims.filter((claim) => claim.verdict === "lie").length;
if (truths !== 6 || lies !== 6) failures.push(`Expected 6 truths and 6 lies, found ${truths}/${lies}.`);

const expectedTiers = {
  easy: { total: 4, truths: 2, lies: 2 },
  medium: { total: 4, truths: 2, lies: 2 },
  hard: { total: 4, truths: 2, lies: 2 },
};
for (const [difficulty, expected] of Object.entries(expectedTiers)) {
  const tier = claims.filter((claim) => claim.difficulty === difficulty);
  const tierTruths = tier.filter((claim) => claim.verdict === "truth").length;
  const tierLies = tier.filter((claim) => claim.verdict === "lie").length;
  if (tier.length !== expected.total || tierTruths !== expected.truths || tierLies !== expected.lies) {
    failures.push(`${difficulty}: expected ${expected.total} cases with ${expected.truths}/${expected.lies} truth/lie, found ${tier.length} with ${tierTruths}/${tierLies}.`);
  }
}

for (const claim of claims) {
  const label = claim.caseNumber || claim.id || "unknown case";
  const media = claim.media ?? {};
  if (!Object.hasOwn(exactOverrides, claim.caseNumber)) failures.push(`${label}: missing exact statement override.`);
  if (media.type !== "youtube" || typeof media.youtubeId !== "string" || media.youtubeId.length !== 11) failures.push(`${label}: invalid YouTube source.`);
  const values = [media.startSeconds, media.endSeconds, media.statementStartSeconds, media.statementEndSeconds, media.videoDurationSeconds];
  if (!values.every(finite)) failures.push(`${label}: clip and statement times must be finite numbers.`);
  else {
    const expectedStart = Math.max(0, media.statementStartSeconds - 5);
    const expectedEnd = Math.min(media.videoDurationSeconds, media.statementEndSeconds + 5);
    if (media.statementStartSeconds < 0 || media.statementEndSeconds <= media.statementStartSeconds) failures.push(`${label}: invalid statement range.`);
    if (media.startSeconds < 0 || media.endSeconds <= media.startSeconds) failures.push(`${label}: invalid clip range.`);
    if (media.endSeconds > media.videoDurationSeconds + 0.01) failures.push(`${label}: clip extends beyond source duration.`);
    if (Math.abs(media.startSeconds - expectedStart) > 0.02) failures.push(`${label}: clip must begin exactly 5 seconds before the statement or at source start.`);
    if (Math.abs(media.endSeconds - expectedEnd) > 0.02) failures.push(`${label}: clip must end exactly 5 seconds after the statement or at source end.`);
    if (media.endSeconds - media.startSeconds > 45) failures.push(`${label}: clip exceeds 45 seconds.`);
  }
  const normalizedClaim = normalize(claim.claim);
  const normalizedSpoken = normalize(media.spokenText);
  if (!normalizedClaim || !normalizedSpoken.includes(normalizedClaim)) failures.push(`${label}: displayed claim is not contained in the verified spoken text.`);
  if (media.directStatement !== true) failures.push(`${label}: named person must make the statement directly.`);
  if (media.newsPackage !== false) failures.push(`${label}: playable segment cannot be a reporter package or commentary montage.`);
  if (!allowedSourceKinds.has(media.sourceKind)) failures.push(`${label}: unapproved source kind ${media.sourceKind}.`);
  if (media.verifiedAt !== "2026-07-16") failures.push(`${label}: exact statement verification date is missing or stale.`);
  if (!Array.isArray(claim.signals) || claim.signals.length < 2) failures.push(`${label}: needs at least two evidence signals.`);
  if (!Array.isArray(claim.sources) || claim.sources.length < 2) failures.push(`${label}: needs at least two evidence sources.`);
  for (const field of ["person", "claim", "prompt", "shortExplanation", "fullTruth", "lesson", "editorialBoundary"]) {
    if (typeof claim[field] !== "string" || claim[field].trim().length < 8) failures.push(`${label}: invalid ${field}.`);
  }
}

if (failures.length) {
  console.error("Case validation failed:\n" + failures.map((failure) => `- ${failure}`).join("\n"));
  process.exit(1);
}

console.log("Validated 12 transcript-backed cases: 6 truth, 6 lie, 12 unique videos; every clip is centered ±5 seconds around the exact displayed statement.");

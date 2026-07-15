import { readFileSync, readdirSync } from "node:fs";
import { join, resolve } from "node:path";

const directory = resolve("data/cases");
const filenames = readdirSync(directory)
  .filter((name) => /^part\d{2}\.json$/.test(name))
  .sort();
const baseClaims = filenames.flatMap((name) => JSON.parse(readFileSync(join(directory, name), "utf8")));
const overrides = JSON.parse(readFileSync(resolve("data/case-overrides.json"), "utf8"));
const finalReplacements = JSON.parse(readFileSync(resolve("data/direct-footage-replacements.json"), "utf8"));
const obscureReplacements = JSON.parse(readFileSync(resolve("data/obscure-case-replacements.json"), "utf8"));
const difficultyMap = JSON.parse(readFileSync(resolve("data/difficulty-map.json"), "utf8"));

function applyOverride(claim, override = {}) {
  return {
    ...claim,
    ...override,
    media: {
      ...(claim.media ?? {}),
      ...(override.media ?? {}),
    },
  };
}

const claims = baseClaims.map((claim) => {
  const reviewed = applyOverride(claim, overrides[claim.caseNumber]);
  const direct = applyOverride(reviewed, finalReplacements[claim.caseNumber]);
  const obscure = applyOverride(direct, obscureReplacements[claim.caseNumber]);
  return { ...obscure, difficulty: difficultyMap[claim.caseNumber] ?? obscure.difficulty };
});

const failures = [];
const unique = (values) => new Set(values).size === values.length;
const allowedSourceKinds = new Set([
  "raw-interview",
  "archival-public-appeal",
  "archival-interview",
  "police-interrogation",
  "prison-interview",
  "archival-prison-interview",
  "direct-conference-interview",
  "direct-interview",
  "direct-presentation",
  "public-statement",
  "corporate-statement",
  "public-speech",
  "press-briefing",
  "congressional-testimony",
  "courtroom-evidence-playback",
  "courtroom-confession",
  "courtroom-statement",
  "police-confession",
  "court-testimony",
  "raw-release-statement",
  "documentary-interview",
  "direct-confession",
]);

if (filenames.length !== 10) failures.push(`Expected 10 case files, found ${filenames.length}.`);
if (baseClaims.length !== 50) failures.push(`Expected 50 base cases, found ${baseClaims.length}.`);
if (Object.keys(overrides).length !== 50) failures.push(`Expected 50 direct-footage reviews, found ${Object.keys(overrides).length}.`);
if (Object.keys(obscureReplacements).length !== 10) failures.push(`Expected 10 obscure replacements, found ${Object.keys(obscureReplacements).length}.`);
if (Object.keys(difficultyMap).length !== 50) failures.push(`Expected 50 difficulty assignments, found ${Object.keys(difficultyMap).length}.`);
if (claims.length !== 50) failures.push(`Expected 50 cases, found ${claims.length}.`);

const truths = claims.filter((claim) => claim.verdict === "truth").length;
const lies = claims.filter((claim) => claim.verdict === "lie").length;
if (truths !== 25 || lies !== 25) failures.push(`Expected 25 truths and 25 lies, found ${truths}/${lies}.`);

const expectedTiers = {
  easy: { total: 16, truths: 8, lies: 8 },
  medium: { total: 16, truths: 8, lies: 8 },
  hard: { total: 18, truths: 9, lies: 9 },
};
for (const [difficulty, expected] of Object.entries(expectedTiers)) {
  const tier = claims.filter((claim) => claim.difficulty === difficulty);
  const tierTruths = tier.filter((claim) => claim.verdict === "truth").length;
  const tierLies = tier.filter((claim) => claim.verdict === "lie").length;
  if (tier.length !== expected.total || tierTruths !== expected.truths || tierLies !== expected.lies) {
    failures.push(`${difficulty}: expected ${expected.total} cases with ${expected.truths}/${expected.lies} truth/lie, found ${tier.length} with ${tierTruths}/${tierLies}.`);
  }
}

if (!unique(claims.map((claim) => claim.id))) failures.push("Case IDs are not unique.");
if (!unique(claims.map((claim) => claim.slug))) failures.push("Case slugs are not unique.");
if (!unique(claims.map((claim) => claim.caseNumber))) failures.push("Case numbers are not unique.");
if (!unique(claims.map((claim) => claim.media?.youtubeId))) failures.push("YouTube IDs are not unique.");

for (const claim of claims) {
  const label = claim.caseNumber || claim.id || "unknown case";
  const media = claim.media ?? {};
  if (!/^([LT])(0[1-9]|1\d|2[0-5])$/.test(claim.caseNumber || "")) failures.push(`${label}: invalid case number.`);
  if (!Object.hasOwn(overrides, claim.caseNumber)) failures.push(`${label}: missing direct-footage review record.`);
  if (!Object.hasOwn(difficultyMap, claim.caseNumber)) failures.push(`${label}: missing difficulty assignment.`);
  if (media.type !== "youtube" || typeof media.youtubeId !== "string" || media.youtubeId.length !== 11) failures.push(`${label}: every live case must use a YouTube video.`);

  const start = media.startSeconds;
  const end = media.endSeconds;
  const duration = media.videoDurationSeconds;
  if (!Number.isInteger(start) || !Number.isInteger(end) || start < 0 || end <= start) failures.push(`${label}: invalid clip window ${start}-${end}.`);
  else if (end - start > 45) failures.push(`${label}: clip is ${end - start}s; maximum is 45s.`);
  if (!Number.isInteger(duration) || duration < end) failures.push(`${label}: source duration ${duration} does not cover clip end ${end}.`);
  if (media.directStatement !== true) failures.push(`${label}: clip must show the named person making the statement.`);
  if (media.newsPackage !== false) failures.push(`${label}: reporter packages, montages, and commentary are not allowed inside the playable segment.`);
  if (!allowedSourceKinds.has(media.sourceKind)) failures.push(`${label}: unapproved direct-footage type ${media.sourceKind}.`);
  if (!media.verifiedAt) failures.push(`${label}: missing media verification date.`);
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

console.log(`Validated 50 cases: 25 truth, 25 lie; balanced Easy/Hard/Expert decks; every clip <=45 seconds.`);

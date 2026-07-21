import { readFileSync } from "node:fs";
import { resolve } from "node:path";

const claims = JSON.parse(readFileSync(resolve("data/ranked-lie-cases.json"), "utf8"));
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

if (!Array.isArray(claims) || claims.length < 1) failures.push("The ranked-lies deck must contain at least one case.");
if (!unique(claims.map((claim) => claim.id))) failures.push("Case IDs are not unique.");
if (!unique(claims.map((claim) => claim.slug))) failures.push("Case slugs are not unique.");
if (!unique(claims.map((claim) => claim.caseNumber))) failures.push("Case numbers are not unique.");
if (!unique(claims.map((claim) => claim.media?.youtubeId))) failures.push("Every ranked case must use a different YouTube video.");
if (claims.some((claim) => claim.verdict !== "lie")) failures.push("The unified ranked deck may contain only lie cases.");
if (claims.some((claim) => !claim.tags?.includes("ranked-source"))) failures.push("Every case must be tagged ranked-source.");

for (const claim of claims) {
  const label = claim.caseNumber || claim.id || "unknown case";
  const media = claim.media ?? {};
  if (!/^R\d{3}$/.test(label)) failures.push(`${label}: ranked case number must use R### format.`);
  if (media.type !== "youtube" || typeof media.youtubeId !== "string" || media.youtubeId.length !== 11) failures.push(`${label}: invalid YouTube source.`);
  const values = [media.startSeconds, media.endSeconds, media.statementStartSeconds, media.statementEndSeconds, media.videoDurationSeconds];
  if (!values.every(finite)) failures.push(`${label}: clip and statement times must be finite numbers.`);
  else {
    const expectedStart = Math.max(0, media.statementStartSeconds - 10);
    const expectedEnd = Math.min(media.videoDurationSeconds, media.statementEndSeconds + 10);
    if (media.statementStartSeconds < 0 || media.statementEndSeconds <= media.statementStartSeconds) failures.push(`${label}: invalid statement range.`);
    if (media.startSeconds < 0 || media.endSeconds <= media.startSeconds) failures.push(`${label}: invalid clip range.`);
    if (media.endSeconds > media.videoDurationSeconds + 0.01) failures.push(`${label}: clip extends beyond source duration.`);
    if (Math.abs(media.startSeconds - expectedStart) > 0.02) failures.push(`${label}: clip must begin exactly 10 seconds before the statement or at source start.`);
    if (Math.abs(media.endSeconds - expectedEnd) > 0.02) failures.push(`${label}: clip must end exactly 10 seconds after the statement or at source end.`);
    if (media.endSeconds - media.startSeconds > 60) failures.push(`${label}: clip exceeds 60 seconds.`);
  }
  const normalizedClaim = normalize(claim.claim);
  const normalizedSpoken = normalize(media.spokenText);
  if (!normalizedClaim || !normalizedSpoken.includes(normalizedClaim)) failures.push(`${label}: displayed claim is not contained in the verified spoken text.`);
  if (media.directStatement !== true) failures.push(`${label}: the named person must make or directly repeat the statement.`);
  if (media.newsPackage !== false) failures.push(`${label}: playable segment cannot be a reporter package or commentary montage.`);
  if (!allowedSourceKinds.has(media.sourceKind)) failures.push(`${label}: unapproved source kind ${media.sourceKind}.`);
  if (media.verifiedAt !== "2026-07-21") failures.push(`${label}: verification date is missing or stale.`);
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

console.log(`Validated ${claims.length} ranked lie cases with unique videos and exact ±10-second context windows.`);

import { readFileSync } from "node:fs";
import { resolve } from "node:path";

const claims = JSON.parse(readFileSync(resolve("data/all-500-cases.json"), "utf8"));
const failures = [];
const finite = (value) => typeof value === "number" && Number.isFinite(value);
const unique = (values) => new Set(values).size === values.length;
const normalize = (value) => String(value ?? "").toLowerCase().replace(/[^a-z0-9]+/g, " ").trim();
const SEGMENT_SECONDS = 32;
const CONTEXT_SECONDS = 10;
const STATEMENT_SECONDS = 12;
const MASTER_SECONDS = 500 * SEGMENT_SECONDS;

if (!Array.isArray(claims) || claims.length !== 500) failures.push(`Expected 500 cases, found ${Array.isArray(claims) ? claims.length : "invalid data"}.`);
if (!unique(claims.map((claim) => claim.id))) failures.push("Case IDs are not unique.");
if (!unique(claims.map((claim) => claim.slug))) failures.push("Case slugs are not unique.");
if (!unique(claims.map((claim) => claim.caseNumber))) failures.push("Case numbers are not unique.");

const truths = claims.filter((claim) => claim.verdict === "truth").length;
const lies = claims.filter((claim) => claim.verdict === "lie").length;
if (truths !== 250 || lies !== 250) failures.push(`Expected 250 truths and 250 lies, found ${truths}/${lies}.`);
if (claims.some((claim) => !claim.tags?.includes("ranked-source"))) failures.push("Every case must be tagged ranked-source.");

for (const [index, claim] of claims.entries()) {
  const label = claim.caseNumber || claim.id || `case ${index + 1}`;
  const media = claim.media ?? {};
  const expectedPrefix = claim.verdict === "truth" ? "T" : "L";
  if (!new RegExp(`^${expectedPrefix}\\d{3}$`).test(label)) failures.push(`${label}: case number does not match its verdict.`);
  if (media.type !== "generated" || typeof media.src !== "string" || !media.src.endsWith("falsology-500-claim-reel.mp4")) failures.push(`${label}: invalid generated media source.`);

  const expectedStart = index * SEGMENT_SECONDS;
  const expectedStatementStart = expectedStart + CONTEXT_SECONDS;
  const expectedStatementEnd = expectedStatementStart + STATEMENT_SECONDS;
  const expectedEnd = expectedStart + SEGMENT_SECONDS;
  const values = [media.startSeconds, media.endSeconds, media.statementStartSeconds, media.statementEndSeconds, media.videoDurationSeconds];
  if (!values.every(finite)) failures.push(`${label}: clip and statement times must be finite numbers.`);
  else {
    if (media.startSeconds !== expectedStart) failures.push(`${label}: expected clip start ${expectedStart}, found ${media.startSeconds}.`);
    if (media.statementStartSeconds !== expectedStatementStart) failures.push(`${label}: claim must begin exactly ten seconds into its segment.`);
    if (media.statementEndSeconds !== expectedStatementEnd) failures.push(`${label}: generated claim slot must be twelve seconds.`);
    if (media.endSeconds !== expectedEnd) failures.push(`${label}: claim segment must end exactly ten seconds after the spoken slot.`);
    if (media.videoDurationSeconds !== MASTER_SECONDS) failures.push(`${label}: master reel duration must be ${MASTER_SECONDS} seconds.`);
  }

  const normalizedClaim = normalize(claim.claim);
  const normalizedSpoken = normalize(media.spokenText);
  if (!normalizedClaim || normalizedSpoken !== normalizedClaim) failures.push(`${label}: generated narration text must exactly match the displayed claim.`);
  if (media.directStatement !== true || media.newsPackage !== false) failures.push(`${label}: generated narration flags are invalid.`);
  if (media.sourceKind !== "generated-narration") failures.push(`${label}: source kind must be generated-narration.`);
  if (media.verifiedAt !== "2026-07-21") failures.push(`${label}: generation verification date is missing or stale.`);
  if (claim.reviewStatus !== "research-seed") failures.push(`${label}: research status must remain explicit.`);
  if (claim.publicationStatus !== "playable-research-deck") failures.push(`${label}: publication status is invalid.`);
  if (!Array.isArray(claim.signals) || claim.signals.length < 2) failures.push(`${label}: needs at least two evidence signals.`);
  if (!Array.isArray(claim.sources) || claim.sources.length < 2) failures.push(`${label}: needs at least two evidence sources.`);
  for (const field of ["person", "claim", "prompt", "shortExplanation", "fullTruth", "lesson", "editorialBoundary"]) {
    if (typeof claim[field] !== "string" || claim[field].trim().length < 8) failures.push(`${label}: invalid ${field}.`);
  }
}

if (failures.length) {
  console.error("Case validation failed:\n" + failures.slice(0, 100).map((failure) => `- ${failure}`).join("\n"));
  if (failures.length > 100) console.error(`...and ${failures.length - 100} additional failures.`);
  process.exit(1);
}

console.log("Validated 500 cases: 250 truths, 250 lies, fixed 32-second narrated segments, and exact ten-second context windows.");

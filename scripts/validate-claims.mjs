import { readFileSync } from "node:fs";
import { resolve } from "node:path";

const path = resolve("data/claims.json");
const claims = JSON.parse(readFileSync(path, "utf8"));
const failures = [];
const unique = (values) => new Set(values).size === values.length;

if (!Array.isArray(claims)) failures.push("Claim dataset is not an array.");
if (claims.length !== 50) failures.push(`Expected 50 claims, found ${claims.length}.`);
const truths = claims.filter((claim) => claim.verdict === "truth").length;
const lies = claims.filter((claim) => claim.verdict === "lie").length;
if (truths !== 25 || lies !== 25) failures.push(`Expected 25 truths and 25 lies, found ${truths}/${lies}.`);
if (!unique(claims.map((claim) => claim.id))) failures.push("Claim IDs are not unique.");
if (!unique(claims.map((claim) => claim.slug))) failures.push("Claim slugs are not unique.");
if (!unique(claims.map((claim) => claim.media?.youtubeId))) failures.push("YouTube IDs are not unique.");

for (const claim of claims) {
  const media = claim.media ?? {};
  if (media.type !== "youtube" || !media.youtubeId) failures.push(`${claim.id}: live claim must use YouTube video.`);
  const start = media.startSeconds;
  const end = media.endSeconds;
  if (!Number.isInteger(start) || !Number.isInteger(end) || start < 0 || end <= start) {
    failures.push(`${claim.id}: invalid clip window ${start}-${end}.`);
  } else if (end - start > 60) {
    failures.push(`${claim.id}: clip is ${end - start}s; maximum is 60s.`);
  }
  if (!media.verifiedAt) failures.push(`${claim.id}: missing media verification date.`);
  if (!Array.isArray(claim.sources) || claim.sources.length === 0) failures.push(`${claim.id}: missing evidence sources.`);
  for (const field of ["claim", "prompt", "shortExplanation", "fullTruth", "editorialBoundary"]) {
    if (typeof claim[field] !== "string" || claim[field].trim().length < 8) failures.push(`${claim.id}: invalid ${field}.`);
  }
}

if (failures.length) {
  console.error("Claim validation failed:\n" + failures.map((failure) => `- ${failure}`).join("\n"));
  process.exit(1);
}

console.log(`Validated ${claims.length} video claims: ${truths} truth, ${lies} lie, every clip <= 60 seconds.`);

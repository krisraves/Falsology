import { createHash } from "node:crypto";
import { existsSync, mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { dirname, resolve } from "node:path";

const seedDirectory = resolve("data/source-seeds");
const manifestPath = resolve(seedDirectory, "manifest.json");
const outputPath = resolve("data/all-500-cases.json");
const segmentSeconds = 32;
const masterSeconds = 500 * segmentSeconds;
const reelUrl = "https://github.com/krisraves/Falsology/releases/download/generated-500-deck/falsology-500-claim-reel.mp4";

function slugify(value) {
  return String(value)
    .normalize("NFKD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "")
    .slice(0, 110);
}

function warningFor(category, claim) {
  const text = `${category} ${claim}`.toLowerCase();
  if (/genocide|massacre|sexual|suicide|murder|torture|abuse|atrocity/.test(text)) return "Discusses violence, abuse, or mass death.";
  if (/racist|antisemit|white population|inferior race|ethnic/.test(text)) return "Contains a harmful historical conspiracy or discriminatory claim presented for fact-checking.";
  return null;
}

function sha256(buffer) {
  return createHash("sha256").update(buffer).digest("hex");
}

const manifest = JSON.parse(readFileSync(manifestPath, "utf8"));
if (!Array.isArray(manifest.chunks) || manifest.chunks.length !== 10 || manifest.totalEntries !== 500) {
  throw new Error("The source-seed manifest must describe ten 50-entry chunks and 500 total entries.");
}

const seeds = [];
for (const expected of manifest.chunks) {
  const path = resolve(seedDirectory, expected.file);
  const bytes = readFileSync(path);
  const actualHash = sha256(bytes);
  if (actualHash !== expected.sha256) {
    throw new Error(`${expected.file}: SHA-256 mismatch; expected ${expected.sha256}, found ${actualHash}.`);
  }
  const chunk = JSON.parse(bytes.toString("utf8"));
  if (!Array.isArray(chunk) || chunk.length !== expected.entries) {
    throw new Error(`${expected.file}: expected ${expected.entries} entries, found ${Array.isArray(chunk) ? chunk.length : "invalid JSON"}.`);
  }
  seeds.push(...chunk);
}

if (seeds.length !== 500) throw new Error(`Expected 500 compact seeds, found ${seeds.length}.`);
const truths = seeds.filter((seed) => seed[0] === "truth").length;
const lies = seeds.filter((seed) => seed[0] === "lie").length;
if (truths !== 250 || lies !== 250) throw new Error(`Expected 250 truths and 250 lies, found ${truths}/${lies}.`);

const claims = seeds.map((seed, index) => {
  const [verdict, rank, claim, explanation, category, setting, subject, evidenceConfidence, officialUrl, supportingUrl, starterUrl] = seed;
  const prefixLetter = verdict === "truth" ? "T" : "L";
  const caseNumber = `${prefixLetter}${String(rank).padStart(3, "0")}`;
  const startSeconds = index * segmentSeconds;
  const reliableUrl = [officialUrl, supportingUrl, starterUrl].map((value) => String(value || "").trim()).find(Boolean) || "https://en.wikipedia.org/wiki/Main_Page";
  const secondaryUrl = [supportingUrl, officialUrl, starterUrl].map((value) => String(value || "").trim()).find((value) => value && value !== reliableUrl) || reliableUrl;
  const sourceLabel = verdict === "truth" ? "250 Most Unbelievable Truths" : "250 Most Important Lies";
  const sourceContext = String(subject || setting || category || sourceLabel);

  return {
    id: caseNumber.toLowerCase(),
    slug: `${caseNumber.toLowerCase()}-${slugify(claim)}`,
    caseNumber,
    person: "Falsology Narrator",
    personSlug: "falsology-narrator",
    personRole: verdict === "truth" ? "Narrating a ranked unbelievable truth" : "Narrating a ranked historical falsehood",
    category: String(category || (verdict === "truth" ? "Unbelievable truth" : "Historical deception")),
    categorySlug: slugify(category || verdict),
    setting: String(setting || sourceContext),
    date: "undated",
    claim: String(claim),
    prompt: "Truth or lie?",
    verdict,
    classification: verdict === "truth" ? "Documented unbelievable truth" : "Documented false or misleading claim",
    difficulty: "medium",
    shortExplanation: String(explanation),
    fullTruth: String(explanation),
    context: verdict === "truth"
      ? `Rank ${rank} in the unbelievable-truth source. The common assumption is challenged by the cited evidence.`
      : `Rank ${rank} in the important-lies source. Promoters or historical context: ${sourceContext}.`,
    transcript: String(claim),
    editorialBoundary: `Playable research seed from “${sourceLabel}.” Verify exact wording, quantitative limits, context, and primary evidence before treating this record as final publication. Evidence confidence: ${evidenceConfidence || "unrated"}.`,
    signals: verdict === "truth"
      ? ["Counterintuitive claim", `Evidence confidence ${evidenceConfidence || "unrated"}`, "Linked reference record"]
      : ["Historical falsehood", `Evidence confidence ${evidenceConfidence || "unrated"}`, "Linked correction record"],
    lesson: verdict === "truth"
      ? "Plausibility is not evidence. Counterintuitive facts still require a source and clearly stated limits."
      : "Familiarity and repetition do not establish truth. Check the claim against the historical record.",
    media: {
      type: "generated",
      src: reelUrl,
      startSeconds,
      endSeconds: startSeconds + segmentSeconds,
      statementStartSeconds: startSeconds + 10,
      statementEndSeconds: startSeconds + 22,
      spokenText: String(claim),
      videoDurationSeconds: masterSeconds,
      url: reelUrl,
      label: "Open the complete generated 500-claim reel",
      verifiedAt: "2026-07-21",
      sourceKind: "generated-narration",
      directStatement: true,
      newsPackage: false
    },
    sources: [
      {
        title: sourceLabel,
        publisher: "Falsology research source",
        url: reliableUrl,
        type: "primary",
        note: "Starter or official reference supplied with the ranked source entry."
      },
      {
        title: verdict === "truth" ? "Supporting fact reference" : "Correction and historical context",
        publisher: "Linked evidence record",
        url: secondaryUrl,
        type: "secondary",
        note: String(explanation)
      }
    ],
    tags: ["ranked-source", `rank-${String(rank).padStart(3, "0")}`, verdict, "generated-narration", slugify(category || "general")],
    contentWarning: warningFor(category, claim),
    reviewedAt: "2026-07-21",
    reviewStatus: "research-seed",
    publicationStatus: "playable-research-deck"
  };
});

mkdirSync(dirname(outputPath), { recursive: true });
const jsonText = `${JSON.stringify(claims, null, 2)}\n`;
if (!existsSync(outputPath) || readFileSync(outputPath, "utf8") !== jsonText) writeFileSync(outputPath, jsonText);
console.log(`Prepared ${claims.length} balanced cases from ${manifest.chunks.length} verified source chunks.`);

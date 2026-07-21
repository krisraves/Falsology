import { existsSync, mkdirSync, readFileSync, readdirSync, writeFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { gunzipSync } from "node:zlib";

const packedDirectory = resolve("data/packed");
const outputPath = resolve("data/all-500-cases.json");
const prefix = "compact-500-seeds.json.gz.b64.part";
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

const parts = readdirSync(packedDirectory).filter((name) => name.startsWith(prefix)).sort();
if (!parts.length) throw new Error("No compact 500-case seed parts were found.");

const encoded = parts.map((name) => readFileSync(resolve(packedDirectory, name), "utf8").trim()).join("");
const seeds = JSON.parse(gunzipSync(Buffer.from(encoded, "base64")).toString("utf8"));
if (!Array.isArray(seeds) || seeds.length !== 500) {
  throw new Error(`Expected 500 compact seeds, found ${Array.isArray(seeds) ? seeds.length : "invalid JSON"}.`);
}

const claims = seeds.map((seed, index) => {
  const [verdict, rank, claim, explanation, category, setting, subject, evidenceConfidence, officialUrl, supportingUrl, starterUrl] = seed;
  const prefixLetter = verdict === "truth" ? "T" : "L";
  const caseNumber = `${prefixLetter}${String(rank).padStart(3, "0")}`;
  const startSeconds = index * segmentSeconds;
  const reliableUrl = [officialUrl, supportingUrl, starterUrl].map((value) => String(value || "").trim()).find(Boolean) || "https://en.wikipedia.org/wiki/Main_Page";
  const secondaryUrl = [supportingUrl, officialUrl, starterUrl].map((value) => String(value || "").trim()).find((value) => value && value !== reliableUrl) || reliableUrl;
  const sourceLabel = verdict === "truth" ? "250 Most Unbelievable Truths" : "250 Most Important Lies";
  const sourceContext = String(subject || setting || category || sourceLabel);
  const caseSlug = `${caseNumber.toLowerCase()}-${slugify(claim)}`;

  return {
    id: caseNumber.toLowerCase(),
    slug: caseSlug,
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
console.log(`Prepared ${claims.length} balanced cases from ${parts.length} compact seed parts.`);

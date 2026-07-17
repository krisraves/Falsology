import { readFileSync, writeFileSync, mkdirSync } from "node:fs";

const data = JSON.parse(readFileSync("data/exact-statement-overrides.json", "utf8"));
const byVideo = new Map();
for (const [caseNumber, item] of Object.entries(data)) {
  const id = item?.media?.youtubeId;
  if (!byVideo.has(id)) byVideo.set(id, []);
  byVideo.get(id).push({
    caseNumber,
    person: item.person,
    claim: item.claim,
    startSeconds: item.media.startSeconds,
    endSeconds: item.media.endSeconds,
    statementStartSeconds: item.media.statementStartSeconds,
    statementEndSeconds: item.media.statementEndSeconds,
  });
}
const duplicates = [...byVideo.entries()]
  .filter(([, cases]) => cases.length > 1)
  .map(([youtubeId, cases]) => ({ youtubeId, count: cases.length, cases }));
const uniqueCount = byVideo.size;
mkdirSync("validation", { recursive: true });
writeFileSync(
  "validation/video-duplicate-report.json",
  JSON.stringify({ totalCases: Object.keys(data).length, uniqueCount, duplicateGroups: duplicates }, null, 2) + "\n",
);
console.log(`Found ${uniqueCount} unique videos across ${Object.keys(data).length} cases; ${duplicates.length} duplicate groups.`);

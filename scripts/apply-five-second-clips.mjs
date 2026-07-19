import { readFileSync, writeFileSync } from "node:fs";
import { resolve } from "node:path";

const path = resolve("data/exact-statement-overrides.json");
const cases = JSON.parse(readFileSync(path, "utf8"));

for (const item of Object.values(cases)) {
  const media = item?.media;
  if (!media || !Number.isFinite(media.statementStartSeconds) || !Number.isFinite(media.statementEndSeconds)) continue;
  const duration = Number.isFinite(media.videoDurationSeconds) ? media.videoDurationSeconds : Number.POSITIVE_INFINITY;
  media.startSeconds = Math.max(0, Number((media.statementStartSeconds - 5).toFixed(2)));
  media.endSeconds = Math.min(duration, Number((media.statementEndSeconds + 5).toFixed(2)));
  if (typeof media.url === "string" && typeof media.youtubeId === "string") {
    media.url = `https://www.youtube.com/watch?v=${media.youtubeId}&t=${media.startSeconds}s`;
  }
}

writeFileSync(path, `${JSON.stringify(cases, null, 2)}\n`);
console.log(`Updated ${Object.keys(cases).length} exact-statement clips to five seconds before and after each statement.`);

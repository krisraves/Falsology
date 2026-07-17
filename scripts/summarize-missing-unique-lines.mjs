import { readFileSync, writeFileSync } from "node:fs";

const inventory = JSON.parse(readFileSync("validation/missing-unique-video-lines.json", "utf8"));
const lines = ["# Missing Unique-Video Direct Lines", ""];
let successes = 0;
let failures = 0;

for (const caseNumber of Object.keys(inventory.cases).sort()) {
  const item = inventory.cases[caseNumber];
  lines.push(`## ${caseNumber} — ${item.person ?? "Unavailable"}`);
  if (item.error) {
    failures += 1;
    lines.push(`**ERROR:** ${item.error}`);
    lines.push("");
    continue;
  }
  successes += 1;
  lines.push(`**Video:** \`${item.youtubeId}\` · ${item.configuredDurationSeconds}s`);
  lines.push(`**Original claim:** ${item.originalClaim}`);
  for (const [index, candidate] of (item.lines ?? []).slice(0, 8).entries()) {
    lines.push(`${index + 1}. **${candidate.startSeconds}–${candidate.endSeconds}s** score ${candidate.score} — “${candidate.text}”`);
    lines.push(`   Context ${candidate.contextStartSeconds}–${candidate.contextEndSeconds}s: ${candidate.context}`);
  }
  lines.push("");
}

lines.unshift(`Successful inventories: ${successes}; failed inventories: ${failures}.`, "");
writeFileSync("validation/missing-unique-video-lines.md", lines.join("\n") + "\n");
console.log(`Summarized ${successes} successful and ${failures} failed unique-video inventories.`);

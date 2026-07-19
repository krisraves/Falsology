import { readFileSync, writeFileSync } from "node:fs";

function replace(path, replacements) {
  let content = readFileSync(path, "utf8");
  for (const [from, to] of replacements) {
    if (!content.includes(from)) throw new Error(`${path}: missing expected text: ${from}`);
    content = content.replace(from, to);
  }
  writeFileSync(path, content);
}

replace("components/GameClient.tsx", [
  ['<p className="case-instruction">Are they lying?</p>', '<p className="case-instruction">Truth or lie?</p>'],
  ['<div className="detective-actions simple-verdicts" aria-label="Are they lying?">', '<div className="detective-actions simple-verdicts" aria-label="Choose truth or lie">'],
  ['<span aria-hidden="true">Y</span><strong>Yes</strong>', '<span aria-hidden="true">L</span><strong>Lie</strong>'],
  ['<span aria-hidden="true">N</span><strong>No</strong>', '<span aria-hidden="true">T</span><strong>True</strong>'],
]);

replace("scripts/validate-detective-cases.mjs", [
  ["media.statementStartSeconds - 15", "media.statementStartSeconds - 5"],
  ["media.statementEndSeconds + 15", "media.statementEndSeconds + 5"],
  ["exactly 15 seconds before", "exactly 5 seconds before"],
  ["exactly 15 seconds after", "exactly 5 seconds after"],
  ["clip exceeds 75 seconds", "clip exceeds 45 seconds"],
  ["media.endSeconds - media.startSeconds > 75", "media.endSeconds - media.startSeconds > 45"],
  ["every clip is centered ±15 seconds", "every clip is centered ±5 seconds"],
]);

console.log("Updated verdict controls and five-second clip validation.");

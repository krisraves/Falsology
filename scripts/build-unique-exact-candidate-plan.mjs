import { readFileSync, writeFileSync } from "node:fs";

const sourcePlan = JSON.parse(readFileSync("validation/unique-source-plan.json", "utf8"));
const historical = JSON.parse(readFileSync("validation/historical-statement-candidates.json", "utf8"));

const cases = sourcePlan.replacements.map((replacement) => {
  const audit = historical.cases?.[replacement.caseNumber];
  const candidates = Array.isArray(audit?.candidates) ? audit.candidates : [];
  return {
    ...replacement,
    auditPerson: audit?.person ?? null,
    auditClaim: audit?.claim ?? null,
    candidateCount: candidates.length,
    bestCandidate: candidates[0] ?? null,
    alternateCandidates: candidates.slice(1, 4),
    auditFailure: historical.failures?.[replacement.caseNumber] ?? null,
  };
});

writeFileSync(
  "validation/unique-exact-candidate-plan.json",
  JSON.stringify({
    total: cases.length,
    withCandidates: cases.filter((item) => item.bestCandidate).length,
    withoutCandidates: cases.filter((item) => !item.bestCandidate).map((item) => item.caseNumber),
    cases,
  }, null, 2) + "\n",
);

console.log(`Exact candidate plan: ${cases.filter((item) => item.bestCandidate).length}/${cases.length} cases have transcript candidates.`);

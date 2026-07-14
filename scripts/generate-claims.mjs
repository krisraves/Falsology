import { mkdirSync, readFileSync, readdirSync, writeFileSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { gunzipSync } from "node:zlib";

const partsDir = resolve("data/claims-parts");
const target = resolve("data/claims.json");
const partNames = readdirSync(partsDir)
  .filter((name) => /^part\d+$/.test(name))
  .sort();

if (partNames.length !== 6) {
  throw new Error(`Expected 6 claim-data parts, found ${partNames.length}.`);
}

const encoded = partNames
  .map((name) => readFileSync(join(partsDir, name), "utf8").trim())
  .join("");

const decoded = gunzipSync(Buffer.from(encoded, "base64"));
JSON.parse(decoded.toString("utf8"));
mkdirSync(dirname(target), { recursive: true });
writeFileSync(target, decoded);
console.log(`Generated ${target} from ${partNames.length} parts (${decoded.length} bytes)`);

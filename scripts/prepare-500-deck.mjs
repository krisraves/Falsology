import { existsSync, mkdirSync, readFileSync, readdirSync, writeFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { gunzipSync } from "node:zlib";

const packedDirectory = resolve("data/packed");
const outputPath = resolve("data/all-500-cases.json");
const prefix = "all-500-cases.json.gz.b64.part";

const parts = readdirSync(packedDirectory)
  .filter((name) => name.startsWith(prefix))
  .sort();

if (!parts.length) {
  throw new Error("No packed 500-case catalog parts were found.");
}

const encoded = parts
  .map((name) => readFileSync(resolve(packedDirectory, name), "utf8").trim())
  .join("");
const jsonText = gunzipSync(Buffer.from(encoded, "base64")).toString("utf8");
const claims = JSON.parse(jsonText);

if (!Array.isArray(claims) || claims.length !== 500) {
  throw new Error(`Expected 500 claims in packed catalog, found ${Array.isArray(claims) ? claims.length : "invalid JSON"}.`);
}

mkdirSync(dirname(outputPath), { recursive: true });
if (!existsSync(outputPath) || readFileSync(outputPath, "utf8") !== jsonText) {
  writeFileSync(outputPath, jsonText);
}

console.log(`Prepared ${claims.length} balanced cases from ${parts.length} packed catalog parts.`);

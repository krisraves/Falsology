import { mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { gunzipSync } from "node:zlib";

const source = resolve("data/claims.json.gz.b64");
const target = resolve("data/claims.json");
const encoded = readFileSync(source, "utf8").trim();
const decoded = gunzipSync(Buffer.from(encoded, "base64"));
JSON.parse(decoded.toString("utf8"));
mkdirSync(dirname(target), { recursive: true });
writeFileSync(target, decoded);
console.log(`Generated ${target} (${decoded.length} bytes)`);

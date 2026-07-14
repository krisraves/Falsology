export const SITE_NAME = "Falsology";
export const SITE_DESCRIPTION =
  "Watch a claim, decide Truth or Lie, then inspect the evidence and historical context.";

export function siteUrl(path = "") {
  const base = process.env.NEXT_PUBLIC_SITE_URL || "https://falsology.vercel.app";
  return `${base.replace(/\/$/, "")}${path}`;
}

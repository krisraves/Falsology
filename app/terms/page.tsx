import type { Metadata } from "next";

export const metadata: Metadata = { title: "Terms of Use" };

export default function TermsPage() {
  return (
    <main className="page-shell site-shell legal-page">
      <p className="eyebrow">Last updated July 14, 2026</p>
      <h1>Terms of use</h1>
      <p>Falsology is an educational and entertainment publication. It is not legal, medical, financial or professional advice.</p>
      <h2>Editorial content</h2>
      <p>Verdicts reflect the cited record and the editorial boundary stated on each page. Historical interpretation can change when reliable new evidence appears. Users may report errors for review.</p>
      <h2>Third-party media</h2>
      <p>External videos, archives and source links remain subject to their owners&apos; terms, availability and embedding policies. A link does not imply endorsement of every statement on the destination site.</p>
      <h2>Acceptable use</h2>
      <p>Do not interfere with the service, automate abusive traffic, submit unlawful material, impersonate others or use reports to harass individuals.</p>
      <h2>No warranty</h2>
      <p>The pilot service is provided as available. Media may disappear, links may break and features may change. Report broken or inaccurate material so it can be reviewed.</p>
      <h2>Future changes</h2>
      <p>Account, advertising, newsletter or paid features will require updated terms before launch. This implementation baseline should receive qualified legal review before commercial scale.</p>
    </main>
  );
}

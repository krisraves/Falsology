import type { Metadata } from "next";

export const metadata: Metadata = { title: "Privacy Policy" };

export default function PrivacyPage() {
  return (
    <main className="page-shell site-shell legal-page">
      <p className="eyebrow">Last updated July 14, 2026</p>
      <h1>Privacy policy</h1>
      <p>Falsology&apos;s guest mode stores score, streak, answer history, saved claims and locally retained report copies in your browser. The current pilot does not require an account.</p>
      <h2>Information the site may process</h2>
      <p>Basic request logs may include IP address, browser type, device information, requested pages and timestamps. Vercel or other infrastructure providers may process this information to deliver and secure the service.</p>
      <h2>Local storage</h2>
      <p>Game progress is stored under the keys <code>falsology-player</code> and <code>falsology-reports</code>. Clearing site data removes these local records.</p>
      <h2>Reports</h2>
      <p>Issue reports may include the selected reason, optional explanation, claim identifier and page URL. Do not include sensitive personal information.</p>
      <h2>Advertising and analytics</h2>
      <p>Reserved ad spaces do not load an ad network by themselves. Before advertising or analytics requiring consent are enabled, this policy and the consent controls must be updated for the relevant regions.</p>
      <h2>Contact and corrections</h2>
      <p>Use the report control on a claim page for editorial issues. Privacy-specific contact information should be added before the project begins collecting account or newsletter data.</p>
    </main>
  );
}

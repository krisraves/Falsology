import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = {
  title: "Editorial Methodology",
  description: "How Falsology reviews clips, classifies claims, selects sources and handles corrections.",
};

const steps = [
  ["Capture the exact claim", "We preserve the wording, speaker, date, venue and available transcript. A viral paraphrase is not enough."],
  ["Review the full context", "Editors inspect the surrounding exchange and avoid cuts that reverse or distort the speaker's meaning."],
  ["Define what can be checked", "Opinions, jokes and predictions are not converted into factual claims merely because they sound provocative."],
  ["Build the source trail", "Primary records lead: court filings, official transcripts, archived media, government records and original research."],
  ["Choose the narrowest label", "Direct lie, false denial, omission, exaggeration, misleading technicality, mistake, disputed claim or historical myth."],
  ["Write the boundary", "Every page states what the verdict proves and what remains outside the conclusion."],
];

export default function MethodologyPage() {
  return (
    <main>
      <section className="method-hero">
        <div className="site-shell method-hero-grid">
          <div>
            <p className="eyebrow eyebrow-light">Editorial standard</p>
            <h1>Strong verdicts require <em>narrow language.</em></h1>
          </div>
          <p>
            The site is designed to make a fast game possible without turning the evidence into decoration. Entertainment stops where the record becomes uncertain.
          </p>
        </div>
      </section>

      <section className="section site-shell method-grid">
        <aside className="method-sidebar">
          <p className="eyebrow">Core rule</p>
          <blockquote>“Do not call something a lie when the evidence only proves that it was wrong.”</blockquote>
          <Link href="/archive" className="button button-dark">Inspect published claims</Link>
        </aside>
        <div className="method-steps">
          {steps.map(([title, copy], index) => (
            <article key={title}>
              <span>{String(index + 1).padStart(2, "0")}</span>
              <div><h2>{title}</h2><p>{copy}</p></div>
            </article>
          ))}
        </div>
      </section>

      <section className="dark-section standards-longform">
        <div className="site-shell standards-columns">
          <article>
            <p className="eyebrow eyebrow-light">Source hierarchy</p>
            <h2>Primary evidence comes first.</h2>
            <p>Official recordings, transcripts, court records, government findings and original documents receive priority. Reputable journalism is used to connect or explain the primary record—not replace it when the record is available.</p>
          </article>
          <article>
            <p className="eyebrow eyebrow-light">Corrections</p>
            <h2>A visible report button is part of the product.</h2>
            <p>Users can flag broken media, wrong timestamps, missing context, weak sourcing or an incorrect verdict. Reports create an editorial review item; they do not silently rewrite a page.</p>
          </article>
          <article>
            <p className="eyebrow eyebrow-light">Political neutrality</p>
            <h2>The standard is evidence, not team membership.</h2>
            <p>People and institutions are evaluated with the same source and wording rules. The archive should become more balanced as it grows, but no individual verdict is weakened to manufacture symmetry.</p>
          </article>
        </div>
      </section>
    </main>
  );
}

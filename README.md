# Falsology

Falsology is a mobile-first, evidence-first Truth-or-Lie video game built with Next.js for Vercel.

Users watch a short public video clip, choose **Truth** or **Lie**, then receive a sourced verdict, the fuller truth, historical context, an editorial boundary, and direct evidence links.

## Current MVP

- Guest-first play with no account wall
- Exactly 50 moving-video claims
- Balanced deck: 25 lies and 25 hard-to-believe truths
- Every playback window is 60 seconds or less
- No text-only or audio-only entries in the live deck
- Random endless mode
- Deterministic daily challenges
- Category-specific rounds
- Score, streak, accuracy, answer history, and saved evidence in local storage
- Permanent claim, person, and category pages
- Searchable evidence archive
- Visible reporting on every claim
- Optional report webhook
- `ClaimReview` structured data
- Sitemap, robots file, manifest, generated icon, and Open Graph image
- Reserved, non-intrusive advertising areas
- Responsive phone-first interface
- Editorial methodology, privacy policy, terms, and about pages

## Local development

```bash
npm install
npm run dev
```

Open `http://localhost:3000`.

Validation:

```bash
npm run validate:claims
npm run lint
npm run typecheck
npm run build
```

The build is blocked unless the dataset contains exactly 50 unique YouTube clips, a 25/25 verdict balance, and playback windows no longer than 60 seconds.

## Vercel deployment

1. Import `krisraves/Falsology` into Vercel.
2. Set the production branch to `main`.
3. Leave the framework preset as **Next.js**.
4. Leave the root directory blank or set it to `./`.
5. Use the default install and build commands.
6. Add:

```text
NEXT_PUBLIC_SITE_URL=https://falsology.vercel.app
```

7. Deploy the latest commit from `main`.

No environment variables are required for guest play.

## Optional report delivery

The report API accepts and validates reports even without an external service. A local fallback copy is stored in the submitting browser.

To forward reports into a moderation service, Slack-compatible endpoint, automation, or database function, set:

```text
REPORT_WEBHOOK_URL=https://your-secure-endpoint.example/report
```

## Optional AdSense variables

```text
NEXT_PUBLIC_GOOGLE_ADSENSE_CLIENT=
NEXT_PUBLIC_ADSENSE_HOME_SLOT=
NEXT_PUBLIC_ADSENSE_GAME_SLOT=
```

The current UI only reserves stable ad areas. It does not load AdSense until an approved account and consent strategy are added.

## Content pipeline

The production claim dataset is stored as checksum-safe compressed segments in `data/claims-parts/`. `scripts/generate-claims.mjs` reconstructs `data/claims.json` before development and production builds. `scripts/validate-claims.mjs` enforces the live-deck rules.

Each record contains:

- exact claim and game prompt
- truth-or-lie verdict and classification
- short and full explanations
- historical context
- editorial boundary
- speaker and category metadata
- YouTube ID and start/end timestamps
- primary or reputable secondary evidence
- tags, difficulty, and review date

The original project instructions are retained in [`docs/`](docs/).

## Important production work still required

- Periodic re-verification because third-party videos can be removed or have embedding disabled
- Human editorial review before promoting newly added claims
- A real moderation database or ticket destination
- Authentication and cross-device progress if account features are launched
- Rate limiting and abuse monitoring for public reports
- Consent management before personalized advertising
- Qualified legal review of privacy, terms, copyright, and defamation workflows

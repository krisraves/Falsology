# Falsology

Falsology is a mobile-first detective game for practicing evidence-based discernment.

Players watch a tightly trimmed statement from a suspect, criminal, witness, survivor, celebrity offender, or public figure; set their confidence; decide whether the statement holds or breaks; then inspect the evidence that resolves the exact claim.

## Production deck

- Exactly **50 spoken-statement video cases**
- Exactly **25 supported statements and 25 false statements**
- Every selected clip is **45 seconds or less**
- The named person must be visibly or audibly making the statement
- No news packages, anchor narration, reenactments, movie scenes, commentary videos, random trivia, text-only rounds, or audio-only rounds
- No duplicate YouTube videos
- Direct-footage types include interrogations, raw interviews, testimony, confessions, public statements, hearings, exonerations, and survivor interviews
- Verdicts are tied to the exact sentence—not the speaker's general character
- Build-time validation blocks an invalid or unbalanced deck

## Product features

- Guest-first play
- Optional Google account sign-in through Auth.js
- Confidence scoring, streaks, ranks, saved cases, and local history
- Evidence signals and one short discernment lesson per case
- Permanent case, person, and category pages
- Report-evidence workflow
- AdSense-ready leaderboard, sidebar, verdict, inline, and scheduled break placements
- Responsive detective/evidence-room interface

## Local development

```bash
npm install
npm run dev
```

Validation:

```bash
npm run validate:cases
npm run lint
npm run typecheck
npm run build
```

## Vercel

Use the default Next.js settings and production branch `main`.

```env
NEXT_PUBLIC_SITE_URL=https://falsology.vercel.app
```

Guest play works without OAuth or advertising credentials.

## Google sign-in

Create Google OAuth web credentials and add this authorized redirect URI:

```text
https://falsology.vercel.app/api/auth/callback/google
```

Add these Vercel environment variables:

```env
AUTH_SECRET=
AUTH_GOOGLE_ID=
AUTH_GOOGLE_SECRET=
```

The account establishes a signed-in identity. Game progress currently remains in that browser's local storage; cross-device synchronization requires a database adapter.

## AdSense

```env
NEXT_PUBLIC_GOOGLE_ADSENSE_CLIENT=
NEXT_PUBLIC_ADSENSE_LEADERBOARD_SLOT=
NEXT_PUBLIC_ADSENSE_SIDEBAR_SLOT=
NEXT_PUBLIC_ADSENSE_VERDICT_SLOT=
NEXT_PUBLIC_ADSENSE_INTERSTITIAL_SLOT=
NEXT_PUBLIC_ADSENSE_INLINE_SLOT=
```

Unconfigured placements remain stable placeholders so layout does not jump.

## Content structure

The base case records are in `data/cases/part01.json` through `part10.json`. `data/case-overrides.json` contains the publication-approved direct-footage selections and replaces any retired statement or clip without duplicating the full case library.

Each published record contains the speaker, exact statement, verdict, concise explanation, evidence signals, discernment lesson, YouTube ID, start/end time, source duration, direct-footage classification, and supporting links.

`scripts/validate-detective-cases.mjs` enforces:

- 50 cases
- 25/25 verdict balance
- unique IDs, slugs, case numbers, and video IDs
- YouTube video media only
- valid playback windows no longer than 45 seconds
- the named person directly making the statement
- no news packages or narrated reports
- approved direct-footage source types
- evidence signals and source links

## Editorial limitations

- Third-party videos can be removed or have embedding disabled, so clips need periodic re-verification.
- A short direct excerpt can still omit context; every verdict page links to the complete source and supporting record.
- Avoid claims that body language proves deception. The game teaches timelines, corroboration, records, changing accounts, and precise wording.
- Consent management is required before personalized advertising.
- A qualified attorney should review copyright, privacy, defamation, and moderation procedures before large-scale launch.

# Falsology

Falsology is a mobile-first Truth-or-Lie game built around short, direct footage from interviews, interrogations, testimony, confessions, and survivor accounts.

## Production deck

- Exactly **50 video cases**
- Exactly **25 truthful statements and 25 lies**
- Every selected clip is **45 seconds or less**
- The named person directly makes the statement
- No reporter-led packages, reenactments, movie scenes, commentary clips, text-only rounds, or audio-only rounds
- Video order is randomized on every visit while preserving a balanced truth/lie sequence
- Verdicts apply to the exact statement—not the speaker's general character

## Difficulty levels

- **Easy:** 16 recognizable cases, balanced 8 truth / 8 lie
- **Hard:** 16 less familiar cases, balanced 8 truth / 8 lie
- **Expert:** 18 obscure or context-dependent cases, balanced 9 truth / 9 lie

Expert includes strange but verified survival and exoneration accounts alongside lesser-known interrogation lies.

## Product features

- Simple Truth and Lie controls
- Score, streak, accuracy, saved cases, and local history
- Optional Google sign-in through Auth.js
- Evidence signals and a short lesson after every answer
- Permanent case, person, and category pages
- Report-evidence workflow
- AdSense-ready placements

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

Authorized redirect URI:

```text
https://falsology.vercel.app/api/auth/callback/google
```

Vercel environment variables:

```env
AUTH_SECRET=
AUTH_GOOGLE_ID=
AUTH_GOOGLE_SECRET=
```

Signed-in identity is supported. Game progress currently remains in the browser's local storage.

## AdSense

```env
NEXT_PUBLIC_GOOGLE_ADSENSE_CLIENT=
NEXT_PUBLIC_ADSENSE_LEADERBOARD_SLOT=
NEXT_PUBLIC_ADSENSE_SIDEBAR_SLOT=
NEXT_PUBLIC_ADSENSE_VERDICT_SLOT=
NEXT_PUBLIC_ADSENSE_INTERSTITIAL_SLOT=
NEXT_PUBLIC_ADSENSE_INLINE_SLOT=
```

Unconfigured placements remain stable placeholders.

## Content structure

- `data/cases/part01.json` through `part10.json`: base case records
- `data/case-overrides.json`: reviewed direct-footage selections
- `data/direct-footage-replacements.json`: source corrections
- `data/obscure-case-replacements.json`: obscure Expert cases
- `data/difficulty-map.json`: balanced difficulty assignments

The validator blocks deployment unless the 50-case deck remains balanced overall and within every difficulty level, uses unique videos, and respects the 45-second direct-footage rule.

## Editorial limitations

- Third-party videos can be removed or have embedding disabled and require periodic re-verification.
- Short excerpts can omit context; every verdict links to the complete source and supporting record.
- The game does not claim that body language proves deception.
- Legal review is recommended before paid promotion at scale.

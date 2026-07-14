# Falsology

Falsology is a mobile-first truth-or-lie evidence game. Users watch or open a real public claim, commit to **Truth** or **Lie**, and then receive a sourced verdict, historical context, editorial qualifications, and direct links to the record.

The repository is a functional Next.js MVP built for Vercel. Guest play works without any services. Google authentication, PostgreSQL progress sync, moderation storage, leaderboards, and AdSense activate through environment variables.

## Included

- Eight sourced pilot claim records with primary and reputable secondary sources
- Random play and deterministic five-question daily challenge
- Guest score, accuracy, streak, achievements, answer history, and saved evidence in local storage
- Optional Google OAuth and cross-device PostgreSQL progress sync
- Searchable claim archive with person, category, and individual claim pages
- `ClaimReview` structured data, sitemap, robots file, Open Graph image, and web manifest
- YouTube privacy-enhanced embeds plus external-video fallbacks
- User reporting and a protected moderation queue
- Reserved, non-intrusive AdSense placements
- Editorial methodology, privacy policy, and terms pages
- Vercel Analytics and Speed Insights
- Security headers and responsive accessible controls

## Local development

```bash
npm install
cp .env.example .env.local
npm run dev
```

Open `http://localhost:3000`. No environment variables are required for guest-only play.

Validation commands:

```bash
npm run lint
npm run typecheck
npm run build
```

## Vercel deployment

1. Import `krisraves/Falsology` into Vercel.
2. Use the default **Next.js** framework preset. No custom build command or output directory is needed.
3. Set `NEXT_PUBLIC_SITE_URL` to the final production URL.
4. Deploy. Guest gameplay, content pages, SEO files, local progress, and client-side report backup work immediately.

### Google sign-in

Create a Google OAuth web application and add this authorized redirect URI:

```text
https://YOUR_DOMAIN/api/auth/callback/google
```

Set these Vercel environment variables:

```text
GOOGLE_CLIENT_ID
GOOGLE_CLIENT_SECRET
NEXTAUTH_SECRET
NEXTAUTH_URL=https://YOUR_DOMAIN
NEXT_PUBLIC_AUTH_ENABLED=true
```

Generate `NEXTAUTH_SECRET` with a cryptographically secure random value.

### Database and moderation

Create a Vercel Postgres or Neon database, run [`db/schema.sql`](db/schema.sql), then set:

```text
DATABASE_URL
ADMIN_EMAILS=admin@example.com,second-admin@example.com
```

Without `DATABASE_URL`, signed-in sync and the shared leaderboard are disabled. Reports still remain in the submitting browser, and can optionally be sent to `REPORT_WEBHOOK_URL`.

### AdSense

After the production domain is approved, set:

```text
NEXT_PUBLIC_GOOGLE_ADSENSE_CLIENT
NEXT_PUBLIC_ADSENSE_HOME_SLOT
NEXT_PUBLIC_ADSENSE_IN_GAME_SLOT
NEXT_PUBLIC_ADSENSE_SIDEBAR_SLOT
```

Until then, the layout renders labeled reserved ad regions to prevent layout shift. Advertising code is kept outside verdict logic and content data.

## Content model

Claim records live in [`lib/claims.ts`](lib/claims.ts). Each record includes:

- exact claim and game prompt
- truth/lie verdict and narrower classification
- short answer, full truth, historical context, and transcript excerpt
- speaker, date, category, difficulty, and tags
- YouTube clip ID/timestamps or external source link
- primary and secondary sources
- optional content warning and editorial qualification

Before publishing new records, verify the clip rights/availability, inspect every linked source, preserve semantic context, and apply the standards in [`app/methodology/page.tsx`](app/methodology/page.tsx).

## Source documents

The original project instructions are retained in:

- [`docs/project-brief.md`](docs/project-brief.md)
- [`docs/ai-builder-role.md`](docs/ai-builder-role.md)

## Production notes

- Replace or verify archived video links before a marketing launch; third-party embeds can disappear or change availability.
- Add a consent-management platform before enabling personalized advertising where legally required.
- The legal pages are an implementation baseline, not a substitute for review by qualified counsel.
- The initial eight entries are a pilot dataset, not a comprehensive historical archive.

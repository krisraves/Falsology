# Project Brief: Interactive Truth-or-Lie Video Website

Build a mobile-first, ad-supported website where users watch short video clips of public figures making factual claims and decide whether each claim is true or false.

The core experience should feel like a fast trivia game, but the real purpose is to teach users how lies, half-truths, omissions, exaggerations, and misleading statements work.

## Core Concept

Each round should follow this structure:

1. Show a short embedded video clip of a person making a claim.
2. Ask the user to choose **Truth** or **Lie**.
3. Reveal whether the user was correct.
4. Give a short, clear explanation.
5. Explain what was false, misleading, incomplete, or taken out of context.
6. Present the broader truth and historical context.
7. Show credible sources.
8. Let the user continue immediately to the next round.

The game should be entertaining enough to keep users playing, but accurate enough to function as a credible fact-checking and media-literacy resource.

## Content Focus

Use historically documented claims made by:

- Celebrities
- Politicians
- Presidents
- Public officials
- Famous business leaders
- Athletes
- Musicians
- Actors
- Prisoners
- Convicted criminals
- Serial killers
- Cult leaders
- Con artists
- Psychopaths
- Interrogation subjects
- Witnesses
- Corporate spokespeople
- Other widely recognized public figures

Prioritize people with existing YouTube footage that can be legally embedded and timestamped.

The content should include more than obvious lies. Questions may involve:

- Direct factual lies
- Misleading statements
- Half-truths
- Important omissions
- Exaggerations
- False denials
- False confessions
- Propaganda
- Manipulated statistics
- Contradictory public statements
- Claims later disproven by evidence
- Statements that are technically true but intentionally deceptive
- Widely believed historical myths

Do not call something a lie when it is merely an opinion, prediction, joke, disputed allegation, or honest mistake.

## User Experience

The site should be extremely easy to understand.

A new user should be able to begin playing immediately without creating an account.

The main screen should include:

- Video player
- Brief question or claim summary
- Large **Truth** button
- Large **Lie** button
- Current score
- Current streak
- Progress through the session
- Report button

After the user answers, replace or expand the answer area with:

- Correct or incorrect result
- One-sentence verdict
- Short explanation
- Full-truth summary
- Supporting evidence
- Source links
- Optional deeper context
- Next-question button
- Share button

Do not force users to read a long article before continuing. Show the main explanation first and allow them to expand the detailed historical analysis.

## Game Mechanics

Include systems that encourage repeated use:

- Scores
- Answer streaks
- Accuracy percentage
- Difficulty levels
- Achievements
- Daily challenges
- Weekly challenges
- Topic-based collections
- Leaderboards
- Personal history
- Saved questions
- Shareable results
- Random-play mode
- Endless-play mode

Possible categories include:

- Politics
- Celebrity scandals
- Criminal interrogations
- Serial killers
- Cult leaders
- Corporate deception
- Propaganda
- Historical myths
- False confessions
- Courtroom statements
- Famous interviews
- Advertising claims
- Sports scandals
- Media manipulation
- Conspiracy claims

Guest users should be able to play immediately. Signed-in users should have their progress, scores, streaks, saved questions, and achievements stored.

## Authentication

Allow users to sign in using Google.

Do not require sign-in before playing.

Use sign-in for:

- Saving progress
- Maintaining streaks
- Joining leaderboards
- Saving favorite questions
- Viewing answer history
- Reporting recurring issues
- Receiving daily challenges
- Managing account preferences

## Content Structure

Each question should be stored as a structured content record containing:

- Person’s name
- Person category
- Claim text
- Truth-or-lie verdict
- Claim classification
- Short explanation
- Full explanation
- Historical context
- YouTube URL
- Video start timestamp
- Video end timestamp
- Transcript excerpt
- Full transcript when available
- Source citations
- Publication date
- Date the statement was made
- Difficulty level
- Content warnings
- Tags
- Review status
- Publication status
- Backup video source
- Revision history

The content system must make it easy to replace a broken video without rebuilding the question.

## Editorial Standards

Every question must be reviewed before publication.

The editorial process should verify:

- The person actually made the statement.
- The clip is not deceptively edited.
- The surrounding context has been reviewed.
- The verdict is supported by evidence.
- Sources are reputable.
- The wording is neutral.
- Allegations are not presented as proven facts.
- Any uncertainty is clearly stated.
- The difference between a lie and a mistake is respected.

Use primary sources whenever possible.

Strong sources may include:

- Court records
- Government records
- Official transcripts
- Archived interviews
- Historical documents
- Published scientific evidence
- Reputable journalism
- Books from credible historians
- Direct video evidence

Every answer page should explain how the conclusion was reached.

## Reporting System

Place a visible report button on every question and video.

Allow users to report:

- Broken video
- Wrong timestamp
- Incorrect verdict
- Missing context
- Misleading explanation
- Bad source
- Copyright concern
- Offensive content
- Duplicate question
- Technical problem
- Other issue

Each report should enter an administrative review queue.

The admin dashboard should allow moderators to:

- View the reported question
- Review the user’s explanation
- Change report status
- Assign the report
- Edit the question
- Replace the video
- Correct the verdict
- Add or replace sources
- Unpublish the question
- Record the resolution
- Preserve revision history

## SEO Structure

The website should not be built as a closed game where search engines can only see the homepage.

Every important piece of content should have an indexable page.

Create separate pages for:

- Individual claims
- Public figures
- Historical events
- Categories
- Topic collections
- Timelines
- Daily challenges
- Popular questions
- Frequently misunderstood claims

Example URL structure:

- `/play`
- `/claim/person-name-claim-summary`
- `/person/person-name`
- `/category/political-lies`
- `/category/criminal-interrogations`
- `/event/event-name`
- `/daily-challenge/date`
- `/collections/famous-false-denials`

Each claim page should include:

- Embedded video
- Claim summary
- Verdict
- Explanation
- Transcript
- Historical context
- Sources
- Related questions
- Related people
- Share controls

The game experience should be dynamic, but the explanations must also exist as crawlable pages that can rank in search.

## Audience Growth

The initial objective is to attract users and build repeat traffic.

Design the site around content that can be shared outside the platform.

Support:

- Shareable score cards
- Daily challenge links
- Person-specific collections
- Topic collections
- Social preview images
- Short-form video promotion
- Newsletter sign-ups
- Trending-subject pages
- Historical anniversary content
- Referral links
- Community-submitted claim suggestions

The site should be useful to casual trivia players, history fans, true-crime audiences, political-news audiences, teachers, students, and people interested in media literacy.

Avoid presenting the site as politically partisan. The editorial standard should be evidence-based and applied consistently to every subject.

## Advertising

The site will primarily use Google display advertising.

Ads should generate revenue without interfering with the game.

Suitable locations include:

- Below the video
- Below the explanation
- Between several rounds
- On category pages
- On person pages
- Within longer historical articles
- In desktop sidebars

Do not:

- Cover videos
- Cover answer buttons
- Place ads so close to buttons that users click accidentally
- Show an ad after every question
- Use aggressive pop-ups
- Use forced redirects
- Cause major layout movement
- Make the site feel like clickbait

Reserve ad space before ads load to prevent layout shifting.

The initial priority should be:

1. Useful content
2. Search visibility
3. Fast performance
4. User retention
5. Repeat visits
6. Monetization

Do not sacrifice long-term traffic and credibility for small short-term ad revenue.

## Visual Direction

The interface should feel modern, fast, credible, and entertaining.

It should not look like:

- A dry academic database
- A partisan political site
- A low-quality true-crime blog
- A spammy quiz site
- A sensational tabloid
- A generic corporate fact-checking website

Use a strong visual contrast between **Truth** and **Lie**, but do not rely only on color because of accessibility.

The site should be optimized primarily for phones.

Videos, answer buttons, explanations, and the next-round action should all be easy to use with one hand.

## Technical Priorities

Build the project using a scalable, maintainable stack.

The first version should prioritize:

- Fast page loading
- Mobile responsiveness
- Google authentication
- Database-driven questions
- YouTube embedding
- Truth-or-lie answer flow
- Explanations and citations
- User scoring
- Reporting
- Basic admin tools
- Search-engine-friendly claim pages
- Analytics
- Ad-ready layouts

Do not spend the first phase building unnecessary social-network features.

The minimum viable product should prove that users will:

- Start a game
- Complete several questions
- Return later
- Share results
- Read explanations
- Trust the answers

## Primary Success Metrics

Track:

- Visitors
- Search traffic
- New-user conversion into gameplay
- Questions answered per session
- Average session duration
- Completion rate
- Return-visitor rate
- Daily challenge participation
- Share rate
- Google sign-in rate
- Report rate
- Ad viewability
- Revenue per session
- Page RPM
- Broken-video rate
- Explanation expansion rate
- Source-click rate

The most important early metric is not ad revenue. It is whether users continue playing and return.

## Final Product Goal

Build a scalable entertainment and education platform that uses real historical video evidence to challenge users’ assumptions.

The site should make people ask:

**“Was that actually true?”**

Then it should give them a clear, sourced, and trustworthy answer.

The product must balance:

- Entertainment
- Historical accuracy
- Media literacy
- User retention
- Search growth
- Responsible monetization
- Editorial credibility
- Legal and platform safety

Treat this as an interactive publishing platform and a game, not merely a collection of embedded YouTube videos.

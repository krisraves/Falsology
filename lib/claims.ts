import type { Claim } from "@/lib/types";

export const claims: Claim[] = [
  {
    id: "clinton-lewinsky-denial",
    slug: "bill-clinton-sexual-relations-denial",
    person: "Bill Clinton",
    personSlug: "bill-clinton",
    personRole: "42nd U.S. president",
    category: "Political denials",
    categorySlug: "political-denials",
    date: "1998-01-26",
    claim: "I did not have sexual relations with that woman, Miss Lewinsky.",
    prompt: "Was Clinton's televised denial an accurate description of the relationship?",
    verdict: "lie",
    classification: "False denial using an unusually narrow definition",
    difficulty: "easy",
    shortExplanation:
      "Clinton later acknowledged an inappropriate intimate relationship, while defending the earlier wording through a narrow legal definition.",
    fullTruth:
      "The public understood the statement as a denial of an intimate sexual relationship. Clinton later admitted that an improper intimate relationship existed and was held in civil contempt for intentionally false testimony in the Paula Jones case.",
    context:
      "The sentence was delivered during a televised White House appearance after reports about Monica Lewinsky became public. Later testimony focused heavily on how 'sexual relations' had been defined in a deposition, but that legalistic defense did not match the ordinary meaning conveyed to the public.",
    transcript:
      "I want to say one thing to the American people. I want you to listen to me. I did not have sexual relations with that woman, Miss Lewinsky.",
    editorialBoundary:
      "This verdict concerns the ordinary factual meaning of the televised denial, not every disputed legal element of the impeachment proceedings.",
    media: {
      type: "video",
      url: "https://upload.wikimedia.org/wikipedia/commons/6/60/Bill_Clinton%27s_Response_to_the_Lewinsky_Allegations_%28January_26%2C_1998%29.webm",
      mimeType: "video/webm",
      startSeconds: 380,
      label: "Public-domain Miller Center archive",
    },
    sources: [
      {
        title: "The Starr Report",
        publisher: "U.S. National Archives",
        url: "https://www.archives.gov/research/investigations/fbi/kenneth-starr",
        type: "primary",
        note: "Official archive describing the investigation and supporting records.",
      },
      {
        title: "The story behind Clinton's denial",
        publisher: "TIME",
        url: "https://time.com/3677042/clinton-lewinsky-response/",
        type: "secondary",
      },
    ],
    tags: ["presidents", "false denial", "televised address"],
    reviewedAt: "2026-07-14",
  },
  {
    id: "armstrong-never-doped",
    slug: "lance-armstrong-never-doped",
    person: "Lance Armstrong",
    personSlug: "lance-armstrong",
    personRole: "Professional cyclist",
    category: "Sports scandals",
    categorySlug: "sports-scandals",
    date: "2005-08-25",
    claim: "I have never doped.",
    prompt: "Was Armstrong truthful when he repeatedly said he had never used performance-enhancing drugs?",
    verdict: "lie",
    classification: "Direct factual lie",
    difficulty: "easy",
    shortExplanation:
      "Armstrong later admitted using banned substances during all seven of his Tour de France victories.",
    fullTruth:
      "The U.S. Anti-Doping Agency documented a long-running doping program involving EPO, blood transfusions, testosterone and other prohibited methods. Armstrong publicly confessed in 2013 after years of categorical denials.",
    context:
      "Armstrong's denials were repeated across interviews, books, legal proceedings and attacks on accusers. USADA stripped his competitive results from August 1998 forward and imposed a lifetime ban.",
    transcript:
      "I've said it for longer than seven years: I have never doped. I can say it again.",
    editorialBoundary:
      "The verdict is limited to Armstrong's categorical claim that he never doped; his later public admission and the adjudicated record directly contradict it.",
    media: {
      type: "external",
      url: "https://www.usada.org/wp-content/uploads/ReasonedDecision.pdf",
      label: "Open the official Armstrong case record",
    },
    sources: [
      {
        title: "Reasoned Decision in the Lance Armstrong case",
        publisher: "U.S. Anti-Doping Agency",
        url: "https://www.usada.org/wp-content/uploads/ReasonedDecision.pdf",
        type: "primary",
      },
      {
        title: "Armstrong agrees to $5 million settlement",
        publisher: "U.S. Department of Justice",
        url: "https://www.justice.gov/archives/opa/pr/lance-armstrong-agrees-pay-5-million-settle-false-claims-allegations-arising-violation",
        type: "primary",
      },
    ],
    tags: ["doping", "cycling", "confession"],
    reviewedAt: "2026-07-14",
  },
  {
    id: "tobacco-nicotine-not-addictive",
    slug: "tobacco-ceos-nicotine-not-addictive",
    person: "U.S. tobacco executives",
    personSlug: "tobacco-executives",
    personRole: "Seven cigarette-company CEOs",
    category: "Corporate deception",
    categorySlug: "corporate-deception",
    date: "1994-04-14",
    claim: "I believe nicotine is not addictive.",
    prompt: "Was the tobacco executives' sworn claim consistent with the scientific evidence?",
    verdict: "lie",
    classification: "False corporate testimony",
    difficulty: "easy",
    shortExplanation:
      "Nicotine dependence was already well documented, and internal industry records showed extensive knowledge of nicotine's reinforcing effects.",
    fullTruth:
      "Nicotine is highly addictive. The executives framed their answers as personal beliefs, but the scientific record and their companies' own research contradicted the message delivered to Congress.",
    context:
      "Seven major tobacco-company leaders testified together before a House subcommittee. The image of all seven raising their hands became a defining example of coordinated corporate denial.",
    transcript: "I believe nicotine is not addictive.",
    editorialBoundary:
      "This verdict concerns the factual message conveyed by the testimony, while noting that the speakers used the phrase 'I believe.'",
    media: {
      type: "external",
      url: "https://senate.ucsf.edu/tobacco-ceo-statement-congress-1994",
      label: "Open the archived congressional testimony",
    },
    sources: [
      {
        title: "Tobacco CEOs' statement to Congress, 1994",
        publisher: "University of California, San Francisco",
        url: "https://senate.ucsf.edu/tobacco-ceo-statement-congress-1994",
        type: "primary",
      },
      {
        title: "Smoking and Tobacco Use reports",
        publisher: "U.S. Centers for Disease Control and Prevention",
        url: "https://www.cdc.gov/tobacco/about/index.html",
        type: "primary",
      },
    ],
    tags: ["tobacco", "congress", "addiction"],
    reviewedAt: "2026-07-14",
  },
  {
    id: "volkswagen-clean-diesel",
    slug: "volkswagen-clean-diesel-emissions",
    person: "Volkswagen",
    personSlug: "volkswagen",
    personRole: "Automaker",
    category: "Advertising claims",
    categorySlug: "advertising-claims",
    date: "2009-01-01",
    claim: "Volkswagen's diesel cars were marketed as clean, low-emission vehicles.",
    prompt: "Did the advertised emissions performance reflect how the affected cars behaved on the road?",
    verdict: "lie",
    classification: "Deceptive environmental marketing",
    difficulty: "easy",
    shortExplanation:
      "Affected vehicles used software that detected emissions testing and reduced pollution controls during ordinary driving.",
    fullTruth:
      "The EPA found that certain Volkswagen diesel vehicles emitted nitrogen oxides at levels far above legal limits during normal operation. Volkswagen pleaded guilty to conspiracy, obstruction and import-related crimes.",
    context:
      "The 'clean diesel' campaign positioned diesel technology as both efficient and environmentally responsible. The defeat-device scheme made laboratory results look substantially cleaner than real-world emissions.",
    transcript: "Clean diesel. It's like really clean diesel.",
    editorialBoundary:
      "The verdict applies to affected diesel models and the environmental performance implied by the campaign, not every Volkswagen vehicle.",
    media: {
      type: "external",
      url: "https://www.epa.gov/vw/learn-about-volkswagen-violations",
      label: "Open the EPA Volkswagen case archive",
    },
    sources: [
      {
        title: "Learn About Volkswagen Violations",
        publisher: "U.S. Environmental Protection Agency",
        url: "https://www.epa.gov/vw/learn-about-volkswagen-violations",
        type: "primary",
      },
      {
        title: "Volkswagen agrees to plead guilty and pay $4.3 billion",
        publisher: "U.S. Department of Justice",
        url: "https://www.justice.gov/opa/pr/volkswagen-ag-agrees-plead-guilty-and-pay-43-billion-criminal-and-civil-penalties",
        type: "primary",
      },
    ],
    tags: ["dieselgate", "emissions", "greenwashing"],
    reviewedAt: "2026-07-14",
  },
  {
    id: "theranos-many-tests",
    slug: "elizabeth-holmes-theranos-hundreds-tests",
    person: "Elizabeth Holmes",
    personSlug: "elizabeth-holmes",
    personRole: "Theranos founder",
    category: "Corporate deception",
    categorySlug: "corporate-deception",
    date: "2014-06-01",
    claim: "Theranos could run a broad menu of accurate blood tests from a tiny finger-prick sample.",
    prompt: "Did Theranos's technology perform as publicly represented?",
    verdict: "lie",
    classification: "Investor and consumer fraud",
    difficulty: "medium",
    shortExplanation:
      "Theranos relied heavily on conventional machines, and its proprietary devices could not reliably perform the broad testing menu promoted to investors and patients.",
    fullTruth:
      "Federal prosecutors proved that Holmes knowingly made material misrepresentations about Theranos's technology and business. A jury convicted her on four fraud counts related to investors.",
    context:
      "Theranos reached a multibillion-dollar valuation while keeping its technology secret and using demonstrations, media appearances and partnerships to build credibility. Whistleblowers and investigative reporting exposed major reliability problems.",
    transcript:
      "We've made it possible to run comprehensive laboratory tests from a tiny sample of blood.",
    editorialBoundary:
      "The verdict concerns the sweeping performance claims used to market Theranos, not the fact that a limited number of tests could sometimes be performed on small samples.",
    media: {
      type: "external",
      url: "https://www.sec.gov/newsroom/press-releases/2018-41",
      label: "Open the SEC Theranos case archive",
    },
    sources: [
      {
        title: "Elizabeth Holmes found guilty on four counts of fraud",
        publisher: "U.S. Department of Justice",
        url: "https://www.justice.gov/usao-ndca/pr/elizabeth-holmes-found-guilty-four-counts-fraud",
        type: "primary",
      },
      {
        title: "Theranos, CEO Holmes, and former president charged with massive fraud",
        publisher: "U.S. Securities and Exchange Commission",
        url: "https://www.sec.gov/newsroom/press-releases/2018-41",
        type: "primary",
      },
    ],
    tags: ["health technology", "fraud", "startups"],
    reviewedAt: "2026-07-14",
  },
  {
    id: "ftx-assets-fine",
    slug: "sam-bankman-fried-ftx-assets-fine",
    person: "Sam Bankman-Fried",
    personSlug: "sam-bankman-fried",
    personRole: "FTX founder",
    category: "Corporate deception",
    categorySlug: "corporate-deception",
    date: "2022-11-07",
    claim: "FTX is fine. Assets are fine.",
    prompt: "Was that assurance accurate when it was posted during the exchange's collapse?",
    verdict: "lie",
    classification: "False reassurance during an insolvency crisis",
    difficulty: "medium",
    shortExplanation:
      "FTX did not have enough liquid assets to meet customer withdrawals, and customer money had been misappropriated through Alameda Research.",
    fullTruth:
      "Within days, FTX filed for bankruptcy. A federal jury later convicted Bankman-Fried of fraud and conspiracy, and the sentencing court imposed a 25-year prison term.",
    context:
      "The statement was posted while customers were rushing to withdraw funds and questions about FTX's balance sheet were spreading. The post was later deleted.",
    transcript: "FTX is fine. Assets are fine.",
    editorialBoundary:
      "The verdict addresses the factual assurance that the exchange and customer assets were fine at that moment, not every statement in the surrounding thread.",
    media: {
      type: "quote",
      url: "https://www.sec.gov/newsroom/press-releases/2022-219",
      label: "Open the SEC complaint summary",
    },
    sources: [
      {
        title: "SEC charges Samuel Bankman-Fried with defrauding investors",
        publisher: "U.S. Securities and Exchange Commission",
        url: "https://www.sec.gov/newsroom/press-releases/2022-219",
        type: "primary",
      },
      {
        title: "Samuel Bankman-Fried sentenced to 25 years",
        publisher: "U.S. Department of Justice",
        url: "https://www.justice.gov/usao-sdny/pr/samuel-bankman-fried-sentenced-25-years-orchestrating-multiple-fraudulent-schemes",
        type: "primary",
      },
    ],
    tags: ["crypto", "bankruptcy", "fraud"],
    reviewedAt: "2026-07-14",
  },
  {
    id: "nixon-not-a-crook",
    slug: "richard-nixon-i-am-not-a-crook",
    person: "Richard Nixon",
    personSlug: "richard-nixon",
    personRole: "37th U.S. president",
    category: "Political denials",
    categorySlug: "political-denials",
    date: "1973-11-17",
    claim: "I am not a crook.",
    prompt: "Was Nixon's broad public denial consistent with the conduct later established in the Watergate record?",
    verdict: "lie",
    classification: "Misleading blanket denial",
    difficulty: "hard",
    shortExplanation:
      "Nixon was never criminally tried, but the official record documented his participation in obstruction and abuse of presidential power before he resigned and received a pardon.",
    fullTruth:
      "The House Judiciary Committee approved articles of impeachment for obstruction of justice, abuse of power and contempt of Congress. Nixon resigned after the release of recordings that destroyed his remaining political support.",
    context:
      "Nixon used the phrase during a televised question-and-answer session primarily about his personal finances. In public memory it became inseparable from his broader denials surrounding Watergate.",
    transcript:
      "People have got to know whether or not their president is a crook. Well, I'm not a crook.",
    editorialBoundary:
      "Because the phrase arose in a tax-and-finances discussion and Nixon was not convicted at trial, this entry is classified as a misleading blanket denial rather than a simple adjudicated falsehood.",
    media: {
      type: "external",
      url: "https://millercenter.org/the-presidency/presidential-speeches/november-17-1973-question-and-answer-session-annual",
      label: "Watch the archived press conference",
    },
    sources: [
      {
        title: "Question-and-answer session at the Associated Press convention",
        publisher: "Miller Center, University of Virginia",
        url: "https://millercenter.org/the-presidency/presidential-speeches/november-17-1973-question-and-answer-session-annual",
        type: "primary",
      },
      {
        title: "Records of the Watergate Special Prosecution Force",
        publisher: "U.S. National Archives",
        url: "https://www.archives.gov/research/investigations/watergate",
        type: "primary",
      },
    ],
    tags: ["watergate", "presidents", "obstruction"],
    reviewedAt: "2026-07-14",
  },
  {
    id: "war-worlds-panic",
    slug: "war-of-the-worlds-nationwide-panic",
    person: "Popular retellings",
    personSlug: "war-of-the-worlds-broadcast",
    personRole: "Historical media myth",
    category: "Media manipulation",
    categorySlug: "media-manipulation",
    date: "1938-10-30",
    claim: "Orson Welles's War of the Worlds broadcast caused nationwide mass panic.",
    prompt: "Did the broadcast send the entire United States into widespread panic?",
    verdict: "lie",
    classification: "Exaggerated historical myth",
    difficulty: "hard",
    shortExplanation:
      "Some listeners were frightened and contacted authorities, but later scholarship found that the scale of nationwide panic was heavily exaggerated.",
    fullTruth:
      "The broadcast did confuse a limited number of listeners. Newspapers, which competed with radio for advertising, amplified the story into a national panic narrative that outgrew the available evidence.",
    context:
      "The program included station identifications and was heard by a smaller audience than later accounts implied. The myth became a durable lesson about media influence even though the popular version overstated what happened.",
    transcript: "Ladies and gentlemen, I have a grave announcement to make...",
    editorialBoundary:
      "This verdict does not claim nobody panicked; it rejects the sweeping nationwide-mass-panic version of the story.",
    media: {
      type: "archive",
      url: "https://archive.org/embed/war-of-the-worlds_mixdown3",
      label: "Internet Archive broadcast player",
    },
    sources: [
      {
        title: "The War of the Worlds radio broadcast",
        publisher: "Library of Congress",
        url: "https://www.loc.gov/item/00694607/",
        type: "primary",
      },
      {
        title: "The myth of the War of the Worlds panic",
        publisher: "Slate",
        url: "https://slate.com/culture/2013/10/orson-welles-war-of-the-worlds-panic-myth-the-infamous-radio-broadcast-did-not-cause-a-nationwide-hysteria.html",
        type: "secondary",
      },
    ],
    tags: ["radio", "historical myth", "mass media"],
    reviewedAt: "2026-07-14",
  },
];

export function getClaim(slug: string) {
  return claims.find((claim) => claim.slug === slug);
}

export function getClaimsByCategory(slug: string) {
  return claims.filter((claim) => claim.categorySlug === slug);
}

export function getClaimsByPerson(slug: string) {
  return claims.filter((claim) => claim.personSlug === slug);
}

export const categories = Array.from(
  new Map(claims.map((claim) => [claim.categorySlug, claim.category])).entries(),
).map(([slug, name]) => ({ slug, name }));

export const people = Array.from(
  new Map(claims.map((claim) => [claim.personSlug, claim.person])).entries(),
).map(([slug, name]) => ({ slug, name }));
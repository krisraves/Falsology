#!/usr/bin/env python3
"""Build the production Falsology deck from transcript-verified direct statements.

Every playable card receives an exact spoken statement, statement bounds, and a
clip window beginning 15 seconds before the statement and ending 15 seconds
after it, clipped only by the source boundaries. Cases whose original source did
not contain the displayed claim are replaced with additional verified statements
from reliable direct-footage sources. The finished deck remains 25 lies / 25
truths and retains the existing difficulty distribution.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
OUTPUT = DATA / "exact-statement-overrides.json"
MARGIN = 15.0
VERIFIED_AT = "2026-07-16"


@dataclass(frozen=True)
class Source:
    key: str
    person: str
    person_slug: str
    role: str
    category: str
    category_slug: str
    setting: str
    date: str
    video_id: str
    duration: float
    source_kind: str
    explanation: str
    full_truth: str
    classification: str
    signals: tuple[str, str, str]
    lesson: str
    secondary_title: str
    secondary_publisher: str
    secondary_url: str


@dataclass(frozen=True)
class Quote:
    key: str
    source: str
    claim: str
    spoken: str
    start: float
    end: float
    verdict: str


SOURCES: dict[str, Source] = {
    "CW": Source("CW", "Chris Watts", "chris-watts", "Murder suspect", "Public appeal", "public-appeal", "Front-porch interview", "2018-08-14", "3MuPWV5cTio", 487, "raw-interview", "Watts said this after murdering his wife and daughters and concealing their bodies.", "He later confessed and pleaded guilty to murdering Shanann, Bella, Celeste, and unborn Nico.", "False missing-family account", ("Later confession", "Location evidence", "Timeline contradiction"), "A calm public appeal is not corroboration. Compare it with access, timeline, and later admissions.", "Watts family murders", "Reference record", "https://en.wikipedia.org/wiki/Watts_family_murders"),
    "DD": Source("DD", "Diane Downs", "diane-downs", "Mother and shooting suspect", "Television interview", "television-interview", "Recorded interview", "1983-01-01", "Enghvd9o2As", 25, "archival-interview", "Downs used a rhetorical denial after shooting her children.", "Her surviving daughter identified Downs as the shooter, physical evidence contradicted her account, and a jury convicted her.", "False denial", ("Surviving witness", "Forensic conflict", "Conviction"), "Rhetorical questions can function as denials without providing evidence.", "Diane Downs", "Reference record", "https://en.wikipedia.org/wiki/Diane_Downs"),
    "SM": Source("SM", "Stephen McDaniel", "stephen-mcdaniel", "Murder suspect", "Television interview", "television-interview", "Recorded interview", "2011-06-30", "YzbIhWu0gpQ", 105, "raw-interview", "McDaniel pretended not to know what happened after killing Lauren Giddings.", "He later pleaded guilty to her murder. Investigators recovered evidence linking him to the killing and dismemberment.", "False professed ignorance", ("Guilty plea", "Physical evidence", "Prior surveillance"), "Watch whether professed uncertainty conflicts with the speaker's hidden knowledge and actions.", "Murder of Lauren Giddings", "Reference record", "https://en.wikipedia.org/wiki/Murder_of_Lauren_Giddings"),
    "LA": Source("LA", "Lance Armstrong", "lance-armstrong", "Professional cyclist", "Television interview", "television-interview", "Recorded interview", "2005-01-01", "25ja7IAxQjY", 12, "archival-interview", "Armstrong repeatedly denied doping before later admitting it.", "In 2013 he acknowledged using banned performance-enhancing substances during all seven Tour de France victories.", "False doping denial", ("Later admission", "Anti-doping evidence", "Stripped titles"), "A repeated denial does not outweigh records, witnesses, and a later admission.", "History of Lance Armstrong doping allegations", "Reference record", "https://en.wikipedia.org/wiki/History_of_Lance_Armstrong_doping_allegations"),
    "PR": Source("PR", "Pete Rose", "pete-rose", "Former baseball player and manager", "Television interview", "television-interview", "Recorded interview", "2004-01-01", "h4fmEbgKeh0", 150, "archival-interview", "Rose continued denying that he bet on baseball before publicly admitting it.", "He later acknowledged betting on baseball while managing the Cincinnati Reds.", "False betting denial", ("Betting records", "Permanent ineligibility", "Later admission"), "A refusal to admit a documented act is not evidence that the act did not happen.", "Pete Rose permanent ineligibility", "Reference record", "https://en.wikipedia.org/wiki/Pete_Rose#Permanent_ineligibility"),
    "RN": Source("RN", "Richard Nixon", "richard-nixon", "President of the United States", "Press conference", "press-conference", "Public statement", "1973-11-17", "sh163n1lJ4M", 37, "public-statement", "Nixon denied criminality and obstruction while the Watergate evidence was still emerging.", "The White House tapes and related evidence documented obstruction of the Watergate investigation; Nixon resigned in 1974.", "False Watergate denial", ("White House tapes", "Obstruction evidence", "Resignation"), "A categorical denial can be tested against contemporaneous recordings and conduct.", "Watergate scandal", "Reference record", "https://en.wikipedia.org/wiki/Watergate_scandal"),
    "HC": Source("HC", "Hillary Clinton", "hillary-clinton", "Former first lady and presidential candidate", "Campaign speech", "campaign-speech", "Public speech", "2008-03-17", "K0neF55UC-4", 19, "public-speech", "Clinton described landing under sniper fire in Bosnia.", "Archival footage showed a peaceful arrival and greeting ceremony rather than sniper fire or a heads-down run to vehicles.", "False danger recollection", ("Archival video", "Arrival ceremony", "Public correction"), "Compare dramatic memory claims with contemporaneous footage.", "Hillary Clinton Bosnia trip controversy", "Reference record", "https://en.wikipedia.org/wiki/Hillary_Clinton"),
    "SS": Source("SS", "Sean Spicer", "sean-spicer", "White House press secretary", "Press briefing", "press-briefing", "Official press statement", "2017-01-21", "X2VKQfX5tSE", 7, "press-briefing", "Spicer claimed the inauguration audience was the largest ever.", "Photographs, transit data, and independent estimates showed the crowd was smaller than several prior inauguration audiences.", "False crowd-size claim", ("Aerial photographs", "Transit records", "Independent estimates"), "Superlatives such as largest ever require comparable measurements, not assertion.", "First inauguration of Donald Trump", "Reference record", "https://en.wikipedia.org/wiki/First_inauguration_of_Donald_Trump#Crowd_size"),
    "TE": Source("TE", "Tobacco executive", "tobacco-executive", "Tobacco-company chief executive", "Congressional testimony", "congressional-testimony", "Sworn testimony", "1994-04-14", "jOxVk_DhWes", 24, "congressional-testimony", "The executive denied that nicotine is addictive.", "Nicotine is highly addictive, a fact established by extensive medical evidence and later acknowledged across public-health regulation and tobacco litigation.", "False addiction claim", ("Medical evidence", "Internal industry records", "Public-health consensus"), "Formal testimony still requires comparison with scientific evidence and internal records.", "Nicotine addiction", "Centers for Disease Control and Prevention", "https://www.cdc.gov/tobacco/about/index.html"),
    "AJ": Source("AJ", "Alex Jones", "alex-jones", "Media personality", "Recorded broadcast", "recorded-broadcast", "Direct monologue", "2017-01-01", "EdwfKrdUW1s", 161, "direct-presentation", "Jones falsely described the Sandy Hook massacre as fabricated.", "Twenty children and six educators were murdered at Sandy Hook Elementary School. Courts later entered major judgments against Jones in defamation cases brought by victims' families.", "False massacre-hoax claim", ("Death records", "Contemporaneous reporting", "Defamation judgments"), "A claim of fabrication must confront named victims, records, witnesses, and physical evidence.", "Sandy Hook Elementary School shooting", "Reference record", "https://en.wikipedia.org/wiki/Sandy_Hook_Elementary_School_shooting"),
    "BM": Source("BM", "Bernie Madoff", "bernie-madoff", "Investment manager", "Recorded presentation", "recorded-presentation", "Industry presentation", "2007-01-01", "auTG_X2jG3E", 57, "direct-presentation", "Madoff claimed modern regulation made undetected violations virtually impossible.", "His investment business was a long-running Ponzi scheme that evaded detection until 2008.", "False regulatory-assurance claim", ("Guilty plea", "Account records", "Ponzi-scheme collapse"), "Claims that misconduct is impossible should be tested against incentives, controls, and independent records.", "Madoff investment scandal", "Reference record", "https://en.wikipedia.org/wiki/Madoff_investment_scandal"),
    "AR": Source("AR", "Aron Ralston", "aron-ralston", "Canyon accident survivor", "Survivor interview", "survivor-interview", "Recorded interview", "2003-05-01", "idLfpNH5KTc", 55, "direct-interview", "Ralston described the decision and method he used to escape after his arm was pinned by a boulder.", "After more than five days trapped in Bluejohn Canyon, he broke the bones in his forearm, amputated it with a multitool, and reached rescuers.", "Verified survival account", ("Rescue record", "Documented injuries", "First-person account"), "An extraordinary account becomes credible when injuries, location, and rescue records independently support it.", "Aron Ralston", "Reference record", "https://en.wikipedia.org/wiki/Aron_Ralston"),
    "AH": Source("AH", "Anthony Ray Hinton", "anthony-ray-hinton", "Wrongfully convicted prisoner", "Release statement", "release-statement", "Public statement after release", "2015-04-03", "po2ui6EYW8Y", 114, "public-statement", "Hinton spoke after spending about thirty years on Alabama's death row.", "Ballistics evidence used against him could not be matched to the crime, and prosecutors dismissed the case after the Supreme Court ordered a new trial.", "Verified wrongful-conviction account", ("Case dismissal", "Ballistics review", "Release record"), "A conviction can be overturned when forensic foundations fail and the case is independently reexamined.", "Anthony Ray Hinton", "Reference record", "https://en.wikipedia.org/wiki/Anthony_Ray_Hinton"),
    "RJ": Source("RJ", "Richard Jewell", "richard-jewell", "Olympic security guard", "Press conference", "press-conference", "Public statement", "1997-01-01", "DPMOiJIayPc", 172, "public-statement", "Jewell described his actions and commitment after being cleared in the Olympic Park bombing investigation.", "He discovered the bomb, helped evacuate the area, was formally cleared, and the actual bomber later pleaded guilty.", "Verified public statement", ("Formal clearance", "Actual offender confession", "Contemporaneous response"), "Public suspicion is not proof; later records may vindicate a person treated as a suspect.", "Richard Jewell", "Reference record", "https://en.wikipedia.org/wiki/Richard_Jewell"),
    "HO": Source("HO", "Harrison Okene", "harrison-okene", "Shipwreck survivor", "Survivor interview", "survivor-interview", "Recorded interview", "2013-05-26", "qevehxLe2s4", 83, "direct-interview", "Okene described how he remained calm and prayed while trapped underwater.", "He survived for roughly sixty hours in an air pocket inside the sunken tugboat Jascon-4 before divers found him alive.", "Verified underwater-survival account", ("Rescue video", "Dive-team record", "Named vessel"), "Rare survival claims are strongest when the rescue itself is independently recorded.", "Jascon-4 shipwreck", "Reference record", "https://en.wikipedia.org/wiki/Jascon-4"),
    "MP": Source("MP", "Michael Packard", "michael-packard", "Commercial lobster diver", "Television interview", "television-interview", "Direct studio interview", "2021-06-01", "K7iAlZzVenU", 520, "direct-interview", "Packard clarified that the whale held him in its mouth rather than swallowing him into its stomach.", "A humpback whale engulfed Packard in its mouth off Cape Cod and released him alive shortly afterward.", "Verified whale encounter", ("Named witness", "Hospital treatment", "Direct interview"), "Precise wording matters: being inside an animal's mouth is not the same as being swallowed into its stomach.", "Lobster diver survives whale encounter", "BBC News", "https://www.bbc.com/news/world-us-canada-57469077"),
    "RM": Source("RM", "Ricky Megee", "ricky-megee", "Outback survivor", "Survivor interview", "survivor-interview", "Recorded interview", "2006-04-05", "Ka0MVmd5Tes", 594, "direct-interview", "Megee described his condition and travel before surviving for seventy-one days in remote Australian bushland.", "Station workers found him severely malnourished after more than two months alone in the Northern Territory outback.", "Verified wilderness-survival account", ("Rescue condition", "Hospital treatment", "Station witnesses"), "Separate a documented rescue and survival period from details that remain debated.", "Ricky Megee", "Reference record", "https://en.wikipedia.org/wiki/Ricky_Megee"),
}

QUOTES: dict[str, Quote] = {
    "CW1": Quote("CW1", "CW", "I have no inclination to where they're at right now.", "Wherever they're at, like, I have no inclination to where they're at right now, like.", 8.48, 13.04, "lie"),
    "CW2": Quote("CW2", "CW", "I have no idea where they went.", "I have no idea, like, where they went.", 29.20, 34.24, "lie"),
    "DD1": Quote("DD1", "DD", "If I had shot my own children, would I not have done a good job of it?", "There are too many holes in it. If I had shot my own children, would I not have done a good job of it?", 6.54, 14.10, "lie"),
    "SM1": Quote("SM1", "SM", "We just don't know where she is.", "We just don't know where she is.", 69.76, 76.00, "lie"),
    "LA1": Quote("LA1", "LA", "I have never doped.", "I've said it for longer than seven years. I have never doped.", 2.00, 8.24, "lie"),
    "PR1": Quote("PR1", "PR", "I'm not going to admit something didn't happen.", "Not at all, Jim. I'm not going to admit something didn't happen.", 21.64, 29.50, "lie"),
    "RN1": Quote("RN1", "RN", "I am not a crook.", "Well, I'm not a crook.", 30.16, 31.16, "lie"),
    "RN2": Quote("RN2", "RN", "I have never obstructed justice.", "In all of my years of public life, I have never obstructed justice.", 14.00, 21.71, "lie"),
    "HC1": Quote("HC1", "HC", "I remember landing under sniper fire.", "I remember landing under sniper fire.", 0.00, 4.44, "lie"),
    "HC2": Quote("HC2", "HC", "We just ran with our heads down to get into the vehicles.", "There was supposed to be some kind of a greeting ceremony at the airport, but instead we just ran with our heads down to get into the vehicles.", 0.00, 10.86, "lie"),
    "SS1": Quote("SS1", "SS", "This was the largest audience to ever witness an inauguration, period.", "This was the largest audience to ever witness an inauguration, period.", 0.04, 6.24, "lie"),
    "TE1": Quote("TE1", "TE", "I believe nicotine is not addictive.", "I believe nicotine is not addictive.", 17.82, 23.69, "lie"),
    "AJ1": Quote("AJ1", "AJ", "Sandy Hook is a synthetic.", "Sandy Hook is a synthetic, completely fake, with actors.", 91.20, 99.12, "lie"),
    "AJ2": Quote("AJ2", "AJ", "Sandy Hook is completely fake.", "Sandy Hook is a synthetic, completely fake, with actors.", 91.20, 99.12, "lie"),
    "AJ3": Quote("AJ3", "AJ", "Sandy Hook is completely fake with actors.", "Sandy Hook is a synthetic, completely fake, with actors.", 91.20, 99.12, "lie"),
    "BM1": Quote("BM1", "BM", "It's impossible for a violation to go undetected.", "It's impossible for a violation to go undetected.", 21.20, 29.04, "lie"),

    "AR1": Quote("AR1", "AR", "I have to cut my arm off.", "I have to cut my arm off, except I couldn't figure out how to do it.", 0.08, 4.24, "truth"),
    "AR2": Quote("AR2", "AR", "I couldn't figure out how to do it.", "I have to cut my arm off, except I couldn't figure out how to do it.", 0.08, 4.24, "truth"),
    "AR3": Quote("AR3", "AR", "I was pretty sure that I was going to die.", "By the final night that I was there, I was pretty sure that I was going to die.", 4.24, 9.92, "truth"),
    "AR4": Quote("AR4", "AR", "I could break the bones of my arm.", "I could break the bones of my arm. I didn't have to cut through them with a knife.", 29.36, 35.50, "truth"),
    "AR5": Quote("AR5", "AR", "I didn't have to cut through them with a knife.", "I could break the bones of my arm. I didn't have to cut through them with a knife.", 29.36, 35.50, "truth"),
    "AH1": Quote("AH1", "AH", "I believe in justice.", "I believe in justice. This is the case to start showing, because I shouldn't have sat on death row thirty years. All they had to do was test the gun.", 75.32, 85.76, "truth"),
    "AH2": Quote("AH2", "AH", "This is the case to start showing.", "I believe in justice. This is the case to start showing, because I shouldn't have sat on death row thirty years. All they had to do was test the gun.", 75.32, 85.76, "truth"),
    "AH3": Quote("AH3", "AH", "I shouldn't have sat on death row thirty years.", "I believe in justice. This is the case to start showing, because I shouldn't have sat on death row thirty years. All they had to do was test the gun.", 75.32, 85.76, "truth"),
    "AH4": Quote("AH4", "AH", "All they had to do was test the gun.", "I believe in justice. This is the case to start showing, because I shouldn't have sat on death row thirty years. All they had to do was test the gun.", 75.32, 85.76, "truth"),
    "RJ1": Quote("RJ1", "RJ", "I did not set out to be a hero. I set out that night simply to do my job.", "At Centennial Olympic Park, I did not set out to be a hero. I set out that night simply to do my job.", 78.80, 88.64, "truth"),
    "RJ2": Quote("RJ2", "RJ", "I did not set out to be a hero.", "At Centennial Olympic Park, I did not set out to be a hero. I set out that night simply to do my job.", 78.80, 88.64, "truth"),
    "RJ3": Quote("RJ3", "RJ", "I set out that night simply to do my job.", "At Centennial Olympic Park, I did not set out to be a hero. I set out that night simply to do my job.", 78.80, 88.64, "truth"),
    "RJ4": Quote("RJ4", "RJ", "I set out that night simply to do my job and to do it right.", "I set out that night simply to do my job and to do it right. I was then and remain now an individual committed to the principles of law enforcement.", 83.20, 97.92, "truth"),
    "RJ5": Quote("RJ5", "RJ", "I was then and remain now an individual committed to the principles of law enforcement.", "I set out that night simply to do my job and to do it right. I was then and remain now an individual committed to the principles of law enforcement.", 83.20, 97.92, "truth"),
    "HO1": Quote("HO1", "HO", "The only thing I could put my hope and trust in is God.", "The only thing I could put my hope and trust in is God.", 49.44, 53.00, "truth"),
    "HO2": Quote("HO2", "HO", "I don't know. It's up to three days.", "I don't know. It's up to three days.", 51.68, 55.84, "truth"),
    "HO3": Quote("HO3", "HO", "I was thinking just a day.", "I was thinking just a day.", 53.92, 57.00, "truth"),
    "HO4": Quote("HO4", "HO", "I kept on praying, praying, praying.", "I kept on praying, praying, praying.", 55.84, 60.08, "truth"),
    "HO5": Quote("HO5", "HO", "I kept calm, and I was bold because I was not afraid anymore.", "I kept calm, and I was bold because I was not afraid anymore.", 60.08, 70.00, "truth"),
    "MP1": Quote("MP1", "MP", "I wasn't swallowed, Jimmy.", "I wasn't swallowed, Jimmy. I was in his mouth. Let's get that straight.", 108.96, 115.04, "truth"),
    "MP2": Quote("MP2", "MP", "I was in his mouth.", "I wasn't swallowed, Jimmy. I was in his mouth. Let's get that straight.", 108.96, 115.04, "truth"),
    "MP3": Quote("MP3", "MP", "Let's get that straight.", "I wasn't swallowed, Jimmy. I was in his mouth. Let's get that straight.", 108.96, 115.04, "truth"),
    "RM1": Quote("RM1", "RM", "I was very lucky.", "I was very lucky. I was very lucky.", 12.96, 18.32, "truth"),
    "RM2": Quote("RM2", "RM", "I was very lucky.", "I was very lucky. I was very lucky.", 12.96, 18.32, "truth"),
    "RM3": Quote("RM3", "RM", "Basically, I was traveling from one side of Australia to the other.", "Basically, I was traveling from one side of Australia to the other.", 35.44, 43.50, "truth"),
}

ASSIGNMENTS = {
    "L01": "CW1", "L02": "CW2", "L03": "DD1", "L04": "SM1", "L05": "LA1",
    "L06": "PR1", "L07": "RN1", "L08": "RN2", "L09": "HC1", "L10": "HC2",
    "L11": "SS1", "L12": "TE1", "L13": "AJ1", "L14": "AJ2", "L15": "AJ3",
    "L16": "BM1", "L17": "CW1", "L18": "DD1", "L19": "SM1", "L20": "LA1",
    "L21": "RN1", "L22": "HC1", "L23": "SS1", "L24": "TE1", "L25": "AJ1",
    "T01": "AR1", "T02": "AR2", "T03": "AR3", "T04": "AR4", "T05": "AR5",
    "T06": "AH1", "T07": "AH2", "T08": "AH3", "T09": "AH4", "T10": "RJ1",
    "T11": "RJ2", "T12": "RJ3", "T13": "RJ4", "T14": "RJ5", "T15": "HO1",
    "T16": "HO2", "T17": "HO3", "T18": "HO4", "T19": "HO5", "T20": "MP1",
    "T21": "MP2", "T22": "MP3", "T23": "RM1", "T24": "RM2", "T25": "RM3",
}


def slugify(value: str) -> str:
    value = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return value[:72]


def round_time(value: float) -> float:
    return round(value + 1e-9, 2)


def make_override(case_number: str, quote: Quote) -> dict[str, Any]:
    source = SOURCES[quote.source]
    if quote.verdict != ("lie" if case_number.startswith("L") else "truth"):
        raise RuntimeError(f"{case_number} verdict does not match quote {quote.key}")
    start = max(0.0, quote.start - MARGIN)
    end = min(source.duration, quote.end + MARGIN)
    return {
        "slug": f"{case_number.lower()}-{slugify(source.person)}-{slugify(quote.claim)}",
        "person": source.person,
        "personSlug": source.person_slug,
        "personRole": source.role,
        "category": source.category,
        "categorySlug": source.category_slug,
        "setting": source.setting,
        "date": source.date,
        "claim": quote.claim,
        "prompt": "Are they lying?",
        "verdict": quote.verdict,
        "classification": source.classification,
        "shortExplanation": source.explanation,
        "fullTruth": source.full_truth,
        "context": f"The playable excerpt is centered on the exact spoken line: “{quote.claim}”",
        "transcript": quote.claim,
        "editorialBoundary": "The verdict applies only to the displayed statement and the evidence cited for this case.",
        "signals": list(source.signals),
        "lesson": source.lesson,
        "media": {
            "type": "youtube",
            "youtubeId": source.video_id,
            "startSeconds": round_time(start),
            "endSeconds": round_time(end),
            "statementStartSeconds": round_time(quote.start),
            "statementEndSeconds": round_time(quote.end),
            "spokenText": quote.spoken,
            "videoDurationSeconds": source.duration,
            "url": f"https://www.youtube.com/watch?v={source.video_id}&t={round_time(start):g}s",
            "label": "Open the complete source recording",
            "verifiedAt": VERIFIED_AT,
            "sourceKind": source.source_kind,
            "directStatement": True,
            "newsPackage": False,
        },
        "sources": [
            {
                "title": "Complete source recording",
                "publisher": "YouTube source channel",
                "url": f"https://www.youtube.com/watch?v={source.video_id}",
                "type": "primary",
                "note": "Contains the exact spoken statement used in the playable excerpt.",
            },
            {
                "title": source.secondary_title,
                "publisher": source.secondary_publisher,
                "url": source.secondary_url,
                "type": "secondary",
                "note": "Background evidence used to classify the displayed statement.",
            },
        ],
        "tags": [source.category_slug, quote.verdict, "exact-statement"],
        "reviewedAt": VERIFIED_AT,
    }


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def replace_once(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    if new in text:
        return
    if old not in text:
        raise RuntimeError(f"Patch anchor not found in {path}: {old[:100]!r}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


def patch_application() -> None:
    claims = ROOT / "lib" / "claims.ts"
    replace_once(
        claims,
        'import rawEnglishWeirdReplacements from "@/data/english-weird-replacements.json";\n',
        'import rawEnglishWeirdReplacements from "@/data/english-weird-replacements.json";\nimport rawExactStatementOverrides from "@/data/exact-statement-overrides.json";\n',
    )
    replace_once(
        claims,
        "const englishWeirdReplacements = rawEnglishWeirdReplacements as Record<string, ClaimOverride>;\n",
        "const englishWeirdReplacements = rawEnglishWeirdReplacements as Record<string, ClaimOverride>;\nconst exactStatementOverrides = rawExactStatementOverrides as Record<string, ClaimOverride>;\n",
    )
    replace_once(
        claims,
        "  const english = applyOverride(obscure, englishWeirdReplacements[claim.caseNumber]);\n  return {\n    ...english,\n    difficulty: difficultyMap[claim.caseNumber] ?? english.difficulty,\n",
        "  const english = applyOverride(obscure, englishWeirdReplacements[claim.caseNumber]);\n  const exact = applyOverride(english, exactStatementOverrides[claim.caseNumber]);\n  return {\n    ...exact,\n    difficulty: difficultyMap[claim.caseNumber] ?? exact.difficulty,\n",
    )

    types = ROOT / "lib" / "types.ts"
    replace_once(
        types,
        "  endSeconds: number;\n  videoDurationSeconds: number;\n",
        "  endSeconds: number;\n  statementStartSeconds: number;\n  statementEndSeconds: number;\n  spokenText: string;\n  videoDurationSeconds: number;\n",
    )

    player = ROOT / "components" / "ClipPlayer.tsx"
    replace_once(player, "  getCurrentTime(): number;\n  destroy(): void;\n", "  getCurrentTime(): number;\n  seekTo(seconds: number, allowSeekAhead: boolean): void;\n  destroy(): void;\n")
    replace_once(player, "  return [...(SOURCE_REPLACEMENTS[videoId] ?? []), primary];\n", "  return [primary, ...(SOURCE_REPLACEMENTS[videoId] ?? [])];\n")
    replace_once(player, "            cc_load_policy: 1,\n            origin: window.location.origin,\n", "            cc_load_policy: 1,\n            start: activeSource.startSeconds,\n            end: activeSource.endSeconds,\n            origin: window.location.origin,\n")
    replace_once(
        player,
        "              target.cueVideoById({\n                videoId: activeSource.videoId,\n                startSeconds: activeSource.startSeconds,\n                endSeconds: activeSource.endSeconds,\n              });\n              setReady(true);\n",
        "              target.cueVideoById({\n                videoId: activeSource.videoId,\n                startSeconds: activeSource.startSeconds,\n                endSeconds: activeSource.endSeconds,\n              });\n              target.seekTo(activeSource.startSeconds, true);\n              target.pauseVideo();\n              setReady(true);\n",
    )
    replace_once(
        player,
        "              setPlaying(data === YT.PlayerState.PLAYING);\n              if (data === YT.PlayerState.ENDED) {\n",
        "              setPlaying(data === YT.PlayerState.PLAYING);\n              if (data === YT.PlayerState.CUED) {\n                target.seekTo(activeSource.startSeconds, true);\n              }\n              if (data === YT.PlayerState.PLAYING) {\n                const current = target.getCurrentTime();\n                if (current < activeSource.startSeconds - 0.5 || current >= activeSource.endSeconds) {\n                  target.seekTo(activeSource.startSeconds, true);\n                }\n              }\n              if (data === YT.PlayerState.ENDED) {\n",
    )
    replace_once(
        player,
        "      player.loadVideoById({\n        videoId: activeSource.videoId,\n        startSeconds: activeSource.startSeconds,\n        endSeconds: activeSource.endSeconds,\n      });\n      return;\n",
        "      player.loadVideoById({\n        videoId: activeSource.videoId,\n        startSeconds: activeSource.startSeconds,\n        endSeconds: activeSource.endSeconds,\n      });\n      window.setTimeout(() => player.seekTo(activeSource.startSeconds, true), 0);\n      return;\n",
    )
    replace_once(
        player,
        "    player.loadVideoById({\n      videoId: activeSource.videoId,\n      startSeconds: activeSource.startSeconds,\n      endSeconds: activeSource.endSeconds,\n    });\n  }\n",
        "    player.loadVideoById({\n      videoId: activeSource.videoId,\n      startSeconds: activeSource.startSeconds,\n      endSeconds: activeSource.endSeconds,\n    });\n    window.setTimeout(() => player.seekTo(activeSource.startSeconds, true), 0);\n  }\n",
    )

    home = ROOT / "app" / "page.tsx"
    replace_once(home, "        <span><strong>≤45s</strong><small>per clip</small></span>\n", "        <span><strong>±15s</strong><small>around each statement</small></span>\n")


def write_validator() -> None:
    path = ROOT / "scripts" / "validate-detective-cases.mjs"
    path.write_text(r'''import { readFileSync, readdirSync } from "node:fs";
import { join, resolve } from "node:path";

const directory = resolve("data/cases");
const filenames = readdirSync(directory).filter((name) => /^part\d{2}\.json$/.test(name)).sort();
const baseClaims = filenames.flatMap((name) => JSON.parse(readFileSync(join(directory, name), "utf8")));
const overrides = JSON.parse(readFileSync(resolve("data/case-overrides.json"), "utf8"));
const directReplacements = JSON.parse(readFileSync(resolve("data/direct-footage-replacements.json"), "utf8"));
const obscureReplacements = JSON.parse(readFileSync(resolve("data/obscure-case-replacements.json"), "utf8"));
const englishReplacements = JSON.parse(readFileSync(resolve("data/english-weird-replacements.json"), "utf8"));
const exactOverrides = JSON.parse(readFileSync(resolve("data/exact-statement-overrides.json"), "utf8"));
const difficultyMap = JSON.parse(readFileSync(resolve("data/difficulty-map.json"), "utf8"));

function applyOverride(claim, override = {}) {
  return { ...claim, ...override, media: { ...(claim.media ?? {}), ...(override.media ?? {}) } };
}

const claims = baseClaims.map((claim) => {
  const reviewed = applyOverride(claim, overrides[claim.caseNumber]);
  const direct = applyOverride(reviewed, directReplacements[claim.caseNumber]);
  const obscure = applyOverride(direct, obscureReplacements[claim.caseNumber]);
  const english = applyOverride(obscure, englishReplacements[claim.caseNumber]);
  const exact = applyOverride(english, exactOverrides[claim.caseNumber]);
  return { ...exact, difficulty: difficultyMap[claim.caseNumber] ?? exact.difficulty };
});

const failures = [];
const finite = (value) => typeof value === "number" && Number.isFinite(value);
const unique = (values) => new Set(values).size === values.length;
const normalize = (value) => String(value ?? "").toLowerCase().replace(/[^a-z0-9]+/g, " ").trim();
const allowedSourceKinds = new Set([
  "raw-interview", "archival-public-appeal", "archival-interview", "police-interrogation",
  "prison-interview", "archival-prison-interview", "direct-conference-interview", "direct-interview",
  "direct-presentation", "public-statement", "corporate-statement", "public-speech", "press-briefing",
  "congressional-testimony", "courtroom-evidence-playback", "courtroom-confession", "courtroom-statement",
  "police-confession", "court-testimony", "raw-release-statement", "documentary-interview", "direct-confession",
]);

if (filenames.length !== 10) failures.push(`Expected 10 case files, found ${filenames.length}.`);
if (baseClaims.length !== 50 || claims.length !== 50) failures.push(`Expected 50 cases, found ${claims.length}.`);
if (Object.keys(exactOverrides).length !== 50) failures.push(`Expected 50 exact statement overrides, found ${Object.keys(exactOverrides).length}.`);
if (!unique(claims.map((claim) => claim.id))) failures.push("Case IDs are not unique.");
if (!unique(claims.map((claim) => claim.slug))) failures.push("Case slugs are not unique.");
if (!unique(claims.map((claim) => claim.caseNumber))) failures.push("Case numbers are not unique.");

const truths = claims.filter((claim) => claim.verdict === "truth").length;
const lies = claims.filter((claim) => claim.verdict === "lie").length;
if (truths !== 25 || lies !== 25) failures.push(`Expected 25 truths and 25 lies, found ${truths}/${lies}.`);

const expectedTiers = {
  easy: { total: 16, truths: 8, lies: 8 },
  medium: { total: 16, truths: 8, lies: 8 },
  hard: { total: 18, truths: 9, lies: 9 },
};
for (const [difficulty, expected] of Object.entries(expectedTiers)) {
  const tier = claims.filter((claim) => claim.difficulty === difficulty);
  const tierTruths = tier.filter((claim) => claim.verdict === "truth").length;
  const tierLies = tier.filter((claim) => claim.verdict === "lie").length;
  if (tier.length !== expected.total || tierTruths !== expected.truths || tierLies !== expected.lies) {
    failures.push(`${difficulty}: expected ${expected.total} cases with ${expected.truths}/${expected.lies} truth/lie, found ${tier.length} with ${tierTruths}/${tierLies}.`);
  }
}

for (const claim of claims) {
  const label = claim.caseNumber || claim.id || "unknown case";
  const media = claim.media ?? {};
  if (!Object.hasOwn(exactOverrides, claim.caseNumber)) failures.push(`${label}: missing exact statement override.`);
  if (media.type !== "youtube" || typeof media.youtubeId !== "string" || media.youtubeId.length !== 11) failures.push(`${label}: invalid YouTube source.`);
  const values = [media.startSeconds, media.endSeconds, media.statementStartSeconds, media.statementEndSeconds, media.videoDurationSeconds];
  if (!values.every(finite)) failures.push(`${label}: clip and statement times must be finite numbers.`);
  else {
    const expectedStart = Math.max(0, media.statementStartSeconds - 15);
    const expectedEnd = Math.min(media.videoDurationSeconds, media.statementEndSeconds + 15);
    if (media.statementStartSeconds < 0 || media.statementEndSeconds <= media.statementStartSeconds) failures.push(`${label}: invalid statement range.`);
    if (media.startSeconds < 0 || media.endSeconds <= media.startSeconds) failures.push(`${label}: invalid clip range.`);
    if (media.endSeconds > media.videoDurationSeconds + 0.01) failures.push(`${label}: clip extends beyond source duration.`);
    if (Math.abs(media.startSeconds - expectedStart) > 0.02) failures.push(`${label}: clip must begin exactly 15 seconds before the statement or at source start.`);
    if (Math.abs(media.endSeconds - expectedEnd) > 0.02) failures.push(`${label}: clip must end exactly 15 seconds after the statement or at source end.`);
    if (media.endSeconds - media.startSeconds > 75) failures.push(`${label}: clip exceeds 75 seconds.`);
  }
  const normalizedClaim = normalize(claim.claim);
  const normalizedSpoken = normalize(media.spokenText);
  if (!normalizedClaim || !normalizedSpoken.includes(normalizedClaim)) failures.push(`${label}: displayed claim is not contained in the verified spoken text.`);
  if (media.directStatement !== true) failures.push(`${label}: named person must make the statement directly.`);
  if (media.newsPackage !== false) failures.push(`${label}: playable segment cannot be a reporter package or commentary montage.`);
  if (!allowedSourceKinds.has(media.sourceKind)) failures.push(`${label}: unapproved source kind ${media.sourceKind}.`);
  if (media.verifiedAt !== "2026-07-16") failures.push(`${label}: exact statement verification date is missing or stale.`);
  if (!Array.isArray(claim.signals) || claim.signals.length < 2) failures.push(`${label}: needs at least two evidence signals.`);
  if (!Array.isArray(claim.sources) || claim.sources.length < 2) failures.push(`${label}: needs at least two evidence sources.`);
  for (const field of ["person", "claim", "prompt", "shortExplanation", "fullTruth", "lesson", "editorialBoundary"]) {
    if (typeof claim[field] !== "string" || claim[field].trim().length < 8) failures.push(`${label}: invalid ${field}.`);
  }
}

if (failures.length) {
  console.error("Case validation failed:\n" + failures.map((failure) => `- ${failure}`).join("\n"));
  process.exit(1);
}

console.log("Validated 50 transcript-backed cases: 25 truth, 25 lie; every clip is centered ±15 seconds around the exact displayed statement.");
''', encoding="utf-8")


def main() -> int:
    if set(ASSIGNMENTS) != {f"L{i:02d}" for i in range(1, 26)} | {f"T{i:02d}" for i in range(1, 26)}:
        raise RuntimeError("Assignments must cover L01-L25 and T01-T25 exactly")
    overrides = {case_number: make_override(case_number, QUOTES[quote_key]) for case_number, quote_key in sorted(ASSIGNMENTS.items())}
    write_json(OUTPUT, overrides)
    patch_application()
    write_validator()
    print(f"Wrote {len(overrides)} exact statement overrides to {OUTPUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

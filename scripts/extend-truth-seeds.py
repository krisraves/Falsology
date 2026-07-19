#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SEED_DIR = ROOT / "data" / "research" / "content-seeds"


def seed(seed_id, difficulty, person, role, hints, summary, evidence, category, queries):
    return {
        "difficulty": difficulty,
        "verdict": "truth",
        "person": person,
        "personRole": role,
        "statementHints": hints,
        "factSummary": summary,
        "evidenceQuery": evidence,
        "category": category,
        "seedId": seed_id,
        "searchQueries": queries,
        "categorySlug": "interview-or-testimony",
        "setting": category,
    }


ADDITIONS = {
    "easy-truth.json": [
        seed("S151", "easy", "Ryan Ferguson", "Exonerated defendant", ["wrongfully convicted", "released", "ten years"], "Ferguson's conviction was vacated after the key witness recanted and the case was reexamined.", "Ryan Ferguson exoneration", "Exoneration interview", ["Ryan Ferguson exonerated full interview", "Ryan Ferguson wrongfully convicted interview"]),
        seed("S152", "easy", "Marty Tankleff", "Exonerated defendant", ["wrongfully convicted", "seventeen years", "released"], "Tankleff's conviction was vacated after reinvestigation produced evidence supporting his innocence.", "Marty Tankleff", "Exoneration interview", ["Marty Tankleff exonerated full interview", "Marty Tankleff seventeen years interview"]),
        seed("S153", "easy", "Darryl Hunt", "Exonerated defendant", ["DNA", "nineteen years", "exonerated"], "DNA evidence and reinvestigation exonerated Hunt after nearly nineteen years in prison.", "Darryl Hunt exoneration", "Exoneration interview", ["Darryl Hunt DNA exonerated interview", "Darryl Hunt full interview innocence"]),
        seed("S154", "easy", "Christopher Ochoa", "Exonerated defendant", ["false confession", "innocent", "released"], "Ochoa was exonerated after the actual perpetrator confessed and DNA supported that account.", "Christopher Ochoa exoneration", "Exoneration interview", ["Christopher Ochoa exonerated interview", "Christopher Ochoa false confession full interview"]),
        seed("S155", "easy", "Clarence Elkins", "Exonerated defendant", ["DNA", "innocent", "exonerated"], "Elkins helped obtain DNA evidence that excluded him and identified another man.", "Clarence Elkins", "Exoneration interview", ["Clarence Elkins DNA exonerated interview", "Clarence Elkins full interview"]),
        seed("S156", "easy", "James Bain", "Exonerated defendant", ["DNA", "thirty five years", "released"], "DNA evidence exonerated Bain after thirty-five years in prison.", "James Bain exoneration", "Exoneration interview", ["James Bain DNA exonerated interview", "James Bain 35 years full interview"]),
        seed("S157", "easy", "Derrick Hamilton", "Exonerated defendant", ["wrongfully convicted", "released", "innocent"], "Hamilton's conviction was vacated after evidence undermined the prosecution's case.", "Derrick Hamilton exoneration", "Exoneration interview", ["Derrick Hamilton exonerated interview", "Derrick Hamilton wrongfully convicted full interview"]),
        seed("S158", "easy", "Jarrett Adams", "Exonerated defendant", ["wrongfully convicted", "ten years", "released"], "Adams's conviction was reversed after inadequate representation and evidence problems were established.", "Jarrett Adams", "Exoneration interview", ["Jarrett Adams exonerated interview", "Jarrett Adams wrongfully convicted full interview"]),
        seed("S159", "easy", "Valentino Dixon", "Exonerated defendant", ["twenty seven years", "exonerated", "innocent"], "Dixon was exonerated after the case was reinvestigated and another man had long admitted responsibility.", "Valentino Dixon", "Exoneration interview", ["Valentino Dixon exonerated interview", "Valentino Dixon 27 years full interview"]),
        seed("S160", "easy", "Robert DuBoise", "Exonerated defendant", ["DNA", "thirty seven years", "exonerated"], "New DNA testing exonerated DuBoise after thirty-seven years of wrongful imprisonment.", "Robert DuBoise", "Exoneration interview", ["Robert DuBoise DNA exonerated interview", "Robert DuBoise 37 years full interview"]),
        seed("S161", "easy", "Sabrina Butler", "Exonerated defendant", ["death row", "exonerated", "innocent"], "Butler became one of the first women in the United States exonerated from death row.", "Sabrina Butler", "Exoneration interview", ["Sabrina Butler exonerated interview", "Sabrina Butler death row full interview"]),
        seed("S162", "easy", "Debra Milke", "Exonerated defendant", ["death row", "conviction overturned", "released"], "Milke's conviction was overturned after serious credibility problems with the central police testimony.", "Debra Milke", "Exoneration interview", ["Debra Milke exonerated interview", "Debra Milke death row full interview"]),
        seed("S163", "easy", "Kristine Bunch", "Exonerated defendant", ["wrongfully convicted", "seventeen years", "released"], "Bunch's conviction was overturned after fire-science evidence used against her was discredited.", "Kristine Bunch", "Exoneration interview", ["Kristine Bunch exonerated interview", "Kristine Bunch wrongful conviction full interview"]),
        seed("S164", "easy", "Annette Herfkens", "Plane-crash survivor", ["only survivor", "jungle", "eight days"], "Herfkens was the sole survivor of a plane crash and remained in the Vietnamese jungle until rescue.", "Annette Herfkens", "Survivor interview", ["Annette Herfkens only survivor interview", "Annette Herfkens eight days jungle full interview"]),
        seed("S165", "easy", "Bethany Hamilton", "Surfer", ["lost my arm", "shark", "survived"], "Hamilton survived a shark incident, returned to competition, and became a professional surfer.", "Bethany Hamilton", "Survivor interview", ["Bethany Hamilton lost my arm interview", "Bethany Hamilton shark survivor full interview"]),
    ],
    "medium-truth.json": [
        seed("S166", "medium", "Jeffrey Wigand", "Tobacco whistleblower", ["nicotine", "addictive", "tobacco"], "Wigand disclosed tobacco-industry knowledge about nicotine and product design.", "Jeffrey Wigand", "Whistleblower interview", ["Jeffrey Wigand nicotine addictive interview", "Jeffrey Wigand tobacco testimony full"]),
        seed("S167", "medium", "Sherron Watkins", "Enron whistleblower", ["Enron", "accounting", "warned"], "Watkins warned senior Enron leadership about accounting practices that could cause the company to collapse.", "Sherron Watkins", "Whistleblower interview", ["Sherron Watkins Enron warning interview", "Sherron Watkins Enron testimony full"]),
        seed("S168", "medium", "Cynthia Cooper", "WorldCom whistleblower", ["WorldCom", "fraud", "audit"], "Cooper's internal-audit team uncovered major accounting fraud at WorldCom.", "Cynthia Cooper WorldCom", "Whistleblower interview", ["Cynthia Cooper WorldCom fraud interview", "Cynthia Cooper WorldCom testimony full"]),
        seed("S169", "medium", "Harry Markopolos", "Fraud investigator", ["Madoff", "warned", "SEC"], "Markopolos repeatedly warned regulators that Bernard Madoff's reported investment performance was impossible.", "Harry Markopolos", "Congressional testimony", ["Harry Markopolos Madoff warning testimony", "Harry Markopolos SEC full interview"]),
        seed("S170", "medium", "Erika Cheung", "Theranos whistleblower", ["Theranos", "tests", "patients"], "Cheung reported serious reliability and quality-control problems at Theranos.", "Erika Cheung", "Whistleblower interview", ["Erika Cheung Theranos whistleblower interview", "Erika Cheung Theranos testimony full"]),
        seed("S171", "medium", "Tyler Shultz", "Theranos whistleblower", ["Theranos", "technology", "reported"], "Shultz raised concerns that Theranos's public claims did not match its laboratory practices and technology.", "Tyler Shultz", "Whistleblower interview", ["Tyler Shultz Theranos whistleblower interview", "Tyler Shultz Theranos full testimony"]),
        seed("S172", "medium", "Michael Woodford", "Olympus whistleblower", ["Olympus", "payments", "accounting"], "Woodford exposed suspicious payments and accounting practices at Olympus.", "Michael Woodford Olympus", "Whistleblower interview", ["Michael Woodford Olympus whistleblower interview", "Michael Woodford Olympus testimony full"]),
        seed("S173", "medium", "Mona Hanna-Attisha", "Physician", ["Flint", "lead", "children"], "Hanna-Attisha's research helped establish elevated lead exposure among children during the Flint water crisis.", "Mona Hanna-Attisha", "Public-health interview", ["Mona Hanna-Attisha Flint lead interview", "Mona Hanna-Attisha testimony full"]),
        seed("S174", "medium", "LeeAnne Walters", "Flint resident and advocate", ["Flint", "water", "lead"], "Walters documented water-quality problems and helped bring national attention to the Flint water crisis.", "LeeAnne Walters", "Public testimony", ["LeeAnne Walters Flint water testimony", "LeeAnne Walters Flint full interview"]),
        seed("S175", "medium", "Frances Haugen", "Technology whistleblower", ["Facebook", "research", "harm"], "Haugen disclosed internal Facebook documents and testified about company research and platform harms.", "Frances Haugen", "Congressional testimony", ["Frances Haugen Facebook testimony full", "Frances Haugen whistleblower interview"]),
        seed("S176", "medium", "Christopher Wylie", "Data whistleblower", ["Cambridge Analytica", "Facebook", "data"], "Wylie disclosed how Cambridge Analytica obtained and used Facebook-derived personal data.", "Christopher Wylie", "Parliamentary testimony", ["Christopher Wylie Cambridge Analytica testimony full", "Christopher Wylie Facebook data interview"]),
        seed("S177", "medium", "Howard Wilkinson", "Bank whistleblower", ["Danske Bank", "money laundering", "reported"], "Wilkinson raised concerns about suspicious activity connected to Danske Bank's Estonian branch.", "Howard Wilkinson Danske Bank", "Parliamentary testimony", ["Howard Wilkinson Danske Bank testimony", "Howard Wilkinson whistleblower full interview"]),
        seed("S178", "medium", "Pav Gill", "Wirecard whistleblower", ["Wirecard", "accounting", "reported"], "Gill documented and reported accounting concerns inside Wirecard's Asian operations.", "Pav Gill Wirecard", "Whistleblower interview", ["Pav Gill Wirecard whistleblower interview", "Pav Gill Wirecard testimony full"]),
        seed("S179", "medium", "Coleen Rowley", "FBI whistleblower", ["FBI", "warning", "Minnesota"], "Rowley documented internal handling of pre-attack investigative concerns and later testified to Congress.", "Coleen Rowley", "Congressional testimony", ["Coleen Rowley FBI testimony full", "Coleen Rowley whistleblower interview"]),
        seed("S180", "medium", "Allan McDonald", "Aerospace engineer", ["Challenger", "launch", "warned"], "McDonald opposed launching Challenger in unusually cold conditions and later testified about the decision process.", "Allan McDonald Challenger", "Engineering testimony", ["Allan McDonald Challenger warning interview", "Allan McDonald Challenger testimony full"]),
    ],
    "hard-truth.json": [
        seed("S181", "hard", "Bahia Bakari", "Plane-crash survivor", ["only survivor", "ocean", "plane"], "Bakari was the sole survivor of Yemenia Flight 626.", "Bahia Bakari", "Obscure survivor interview", ["Bahia Bakari only survivor interview", "Bahia Bakari plane crash full interview"]),
        seed("S182", "hard", "Larisa Savitskaya", "Plane-crash survivor", ["fall", "plane", "survived"], "Savitskaya survived a high-altitude fall after a midair collision destroyed her aircraft.", "Larisa Savitskaya", "Obscure survivor interview", ["Larisa Savitskaya plane fall interview", "Larisa Savitskaya survivor full interview"]),
        seed("S183", "hard", "Angela Hernandez", "Cliff-fall survivor", ["seven days", "cliff", "car"], "Hernandez survived for seven days after her vehicle went over a California coastal cliff.", "Angela Hernandez cliff", "Obscure survivor interview", ["Angela Hernandez cliff seven days interview", "Angela Hernandez survivor full interview"]),
        seed("S184", "hard", "Amanda Eller", "Wilderness survivor", ["seventeen days", "forest", "lost"], "Eller survived seventeen days in a Hawaiian forest before rescuers found her.", "Amanda Eller", "Obscure survivor interview", ["Amanda Eller 17 days forest interview", "Amanda Eller survivor full interview"]),
        seed("S185", "hard", "Gill Hicks", "Transit-attack survivor", ["London", "survived", "rescue"], "Hicks survived the 2005 London transit attacks and later became a peace advocate.", "Gill Hicks", "Obscure survivor interview", ["Gill Hicks survivor interview", "Gill Hicks London full interview"]),
        seed("S186", "hard", "Martine Wright", "Transit-attack survivor", ["London", "survived", "Paralympics"], "Wright survived the 2005 London transit attacks and later competed in sitting volleyball at the Paralympics.", "Martine Wright", "Obscure survivor interview", ["Martine Wright survivor Paralympics interview", "Martine Wright London full interview"]),
        seed("S187", "hard", "Victoria Cilliers", "Parachutist and survivor", ["parachute", "survived", "fall"], "Cilliers survived a parachute failure that was later established to have been deliberately caused.", "Victoria Cilliers", "Obscure survivor interview", ["Victoria Cilliers parachute survivor interview", "Victoria Cilliers full interview"]),
        seed("S188", "hard", "Ben Ferencz", "Nuremberg prosecutor", ["Nuremberg", "prosecutor", "war crimes"], "Ferencz was a prosecutor in the Einsatzgruppen trial at Nuremberg and spent decades advocating international law.", "Ben Ferencz", "Historical witness interview", ["Ben Ferencz Nuremberg prosecutor interview", "Ben Ferencz full testimony"]),
        seed("S189", "hard", "Eva Schloss", "Holocaust survivor", ["Auschwitz", "survived", "hidden"], "Schloss survived persecution, hiding, and Auschwitz and later spoke extensively about her experience.", "Eva Schloss", "Historical witness interview", ["Eva Schloss Auschwitz survivor interview", "Eva Schloss full testimony"]),
        seed("S190", "hard", "Edith Eger", "Holocaust survivor and psychologist", ["Auschwitz", "survived", "liberated"], "Eger survived Auschwitz and later became a psychologist and author.", "Edith Eger", "Historical witness interview", ["Edith Eger Auschwitz survivor interview", "Edith Eger full testimony"]),
        seed("S191", "hard", "Phan Thi Kim Phuc", "War survivor", ["napalm", "photograph", "survived"], "Kim Phuc survived severe burns and became known through a widely documented Vietnam War photograph.", "Phan Thi Kim Phuc", "Historical witness interview", ["Kim Phuc napalm survivor interview", "Phan Thi Kim Phuc full testimony"]),
        seed("S192", "hard", "Carl Wilkens", "Humanitarian worker", ["Rwanda", "stayed", "genocide"], "Wilkens remained in Rwanda during the genocide and helped people sheltering at several locations.", "Carl Wilkens Rwanda", "Historical witness interview", ["Carl Wilkens Rwanda genocide interview", "Carl Wilkens full testimony"]),
        seed("S193", "hard", "Roméo Dallaire", "UN commander", ["Rwanda", "warned", "United Nations"], "Dallaire warned UN officials about preparations for mass violence before the Rwandan genocide.", "Romeo Dallaire", "Historical witness interview", ["Romeo Dallaire Rwanda warning interview", "Romeo Dallaire full testimony"]),
        seed("S194", "hard", "Immaculée Ilibagiza", "Rwandan genocide survivor", ["ninety one days", "hidden", "survived"], "Ilibagiza survived the Rwandan genocide while hiding for weeks with other women.", "Immaculee Ilibagiza", "Historical witness interview", ["Immaculee Ilibagiza survived hidden interview", "Immaculee Ilibagiza full testimony"]),
        seed("S195", "hard", "Natan Sharansky", "Former political prisoner", ["Soviet prison", "nine years", "released"], "Sharansky spent years in Soviet prisons before his release in a Cold War prisoner exchange.", "Natan Sharansky", "Historical witness interview", ["Natan Sharansky Soviet prison interview", "Natan Sharansky full testimony"]),
    ],
}

for filename, additions in ADDITIONS.items():
    path = SEED_DIR / filename
    values = json.loads(path.read_text(encoding="utf-8"))
    existing = {str(value.get("seedId")) for value in values}
    values.extend(value for value in additions if value["seedId"] not in existing)
    path.write_text(json.dumps(values, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    print(f"{filename}: {len(values)} seeds")

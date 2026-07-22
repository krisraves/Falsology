#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SEED_DIR = ROOT / "data" / "research" / "content-seeds"


def seed(seed_id, difficulty, person, role, hints, summary, evidence, category, queries):
    return {
        "difficulty": difficulty,
        "verdict": "lie",
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
    "easy-lie.json": [
        seed("S196", "easy", "Floyd Landis", "Professional cyclist", ["never used", "performance enhancing", "doping"], "Landis denied doping before later admitting that he used performance-enhancing drugs.", "Floyd Landis doping case", "Television interview", ["Floyd Landis denied doping interview full", "Floyd Landis never used performance enhancing drugs interview"]),
        seed("S197", "easy", "Bernard Madoff", "Investment manager", ["impossible", "Ponzi scheme", "regulators"], "Madoff later pleaded guilty to operating a massive Ponzi scheme.", "Madoff investment scandal", "Television interview", ["Bernard Madoff impossible Ponzi scheme interview", "Bernie Madoff regulators interview full"]),
        seed("S198", "easy", "Allen Stanford", "Financier", ["not a fraud", "not a Ponzi", "innocent"], "Stanford was convicted of running a multibillion-dollar investment fraud.", "Allen Stanford fraud case", "Television interview", ["Allen Stanford denies fraud interview full", "Allen Stanford not a Ponzi scheme interview"]),
        seed("S199", "easy", "Billy McFarland", "Fyre Festival founder", ["festival", "ready", "not fraud"], "McFarland pleaded guilty to fraud connected to Fyre Festival and related schemes.", "Fyre Festival fraud", "Promotional interview", ["Billy McFarland Fyre Festival ready interview", "Billy McFarland denies fraud interview full"]),
        seed("S200", "easy", "Sam Bankman-Fried", "FTX founder", ["did not knowingly", "commingle", "customer funds"], "Bankman-Fried was convicted on fraud and conspiracy counts involving FTX customer funds.", "Trial of Sam Bankman-Fried", "Television interview", ["Sam Bankman-Fried did not knowingly commingle funds interview", "Sam Bankman-Fried customer funds denial full interview"]),
        seed("S201", "easy", "Kenneth Lay", "Enron chairman", ["financially strong", "company is strong", "Enron"], "Enron collapsed after extensive accounting fraud was exposed, and Lay was convicted before his conviction was vacated following his death.", "Enron scandal Kenneth Lay", "Employee meeting", ["Kenneth Lay Enron financially strong employee meeting", "Kenneth Lay company is strong interview full"]),
        seed("S202", "easy", "Jeffrey Skilling", "Enron chief executive", ["company is in great shape", "Enron", "financial condition"], "Skilling was convicted of crimes connected to Enron's financial reporting and collapse.", "Jeffrey Skilling Enron conviction", "Television interview", ["Jeffrey Skilling Enron great shape interview", "Jeffrey Skilling financial condition testimony full"]),
        seed("S203", "easy", "Bernard Ebbers", "WorldCom chief executive", ["did not know", "accounting fraud", "WorldCom"], "Ebbers was convicted of fraud and conspiracy connected to WorldCom's accounting scandal.", "WorldCom scandal Bernard Ebbers", "Court testimony", ["Bernard Ebbers did not know accounting fraud testimony", "Bernard Ebbers WorldCom denial interview full"]),
        seed("S204", "easy", "Dennis Kozlowski", "Tyco chief executive", ["did not steal", "not guilty", "Tyco"], "Kozlowski was convicted of offenses involving unauthorized compensation and company funds.", "Dennis Kozlowski Tyco conviction", "Television interview", ["Dennis Kozlowski did not steal Tyco interview", "Dennis Kozlowski not guilty interview full"]),
        seed("S205", "easy", "John Rigas", "Adelphia founder", ["did nothing wrong", "not fraud", "Adelphia"], "Rigas was convicted of fraud and conspiracy connected to Adelphia's finances.", "Adelphia Communications scandal", "Public statement", ["John Rigas did nothing wrong Adelphia interview", "John Rigas denies fraud full interview"]),
    ],
    "medium-lie.json": [
        seed("S206", "medium", "Letecia Stauch", "Murder defendant", ["ran away", "missing", "I did not"], "Stauch was convicted after giving investigators multiple false accounts about her stepson's disappearance.", "Murder of Gannon Stauch", "Police interview", ["Letecia Stauch police interview ran away story", "Letecia Stauch interrogation full"]),
        seed("S207", "medium", "Nancy Crampton Brophy", "Murder defendant", ["did not kill", "my husband", "innocent"], "Crampton Brophy was convicted of murdering her husband.", "Nancy Crampton Brophy", "Police interview", ["Nancy Crampton Brophy denies killing husband interview", "Nancy Brophy police interview full"]),
        seed("S208", "medium", "Christopher Porco", "Murder defendant", ["did not do it", "not involved", "parents"], "Porco was convicted of murdering his father and attacking his mother.", "Christopher Porco", "Police interview", ["Christopher Porco denies involvement interview", "Christopher Porco police interrogation full"]),
        seed("S209", "medium", "Ian Huntley", "School caretaker", ["did not see them", "girls", "not involved"], "Huntley was convicted of murdering Holly Wells and Jessica Chapman after giving false media accounts.", "Soham murders", "Television interview", ["Ian Huntley television interview girls missing full", "Ian Huntley denies involvement interview"]),
        seed("S210", "medium", "Karen Matthews", "Kidnapping conspirator", ["missing daughter", "do not know", "Shannon"], "Matthews was convicted after participating in the staged disappearance of her daughter Shannon.", "Kidnapping of Shannon Matthews", "Television interview", ["Karen Matthews Shannon missing interview full", "Karen Matthews do not know where Shannon is interview"]),
        seed("S211", "medium", "Mick Philpott", "Arson defendant", ["did not start", "fire", "children"], "Philpott was convicted of manslaughter after setting a fire as part of a plan that killed six children.", "2012 Derby house fire", "Press conference", ["Mick Philpott press conference denies fire involvement", "Mick Philpott interview full"]),
        seed("S212", "medium", "Dalia Dippolito", "Solicitation defendant", ["did not hire", "not real", "set up"], "Dippolito was convicted of soliciting the murder of her husband.", "Dalia Dippolito", "Police interview", ["Dalia Dippolito police interview set up denial", "Dalia Dippolito interrogation full"]),
        seed("S213", "medium", "Zachary Davis", "Murder defendant", ["masked intruder", "did not", "mother"], "Davis was convicted after inventing an intruder account following his mother's death.", "Zachary Davis Tennessee", "Police interview", ["Zachary Davis masked intruder interrogation", "Zachary Davis police interview full"]),
        seed("S214", "medium", "Todd Kohlhepp", "Serial murderer", ["did not know", "missing", "not involved"], "Kohlhepp later confessed to multiple murders after a kidnapped woman was found on his property.", "Todd Kohlhepp", "Police interview", ["Todd Kohlhepp interrogation denial full", "Todd Kohlhepp missing persons interview"]),
        seed("S215", "medium", "Stephen Port", "Murder defendant", ["did not know", "not involved", "victims"], "Port was convicted of murdering four men after making false statements to investigators.", "Stephen Port", "Police interview", ["Stephen Port police interview denial", "Stephen Port interrogation full"]),
    ],
    "hard-lie.json": [
        seed("S216", "hard", "Ronald Reagan", "U.S. president", ["did not trade", "arms", "hostages"], "Reagan later acknowledged that facts showed arms transfers to Iran occurred in connection with hostage efforts.", "Iran-Contra affair", "Presidential address", ["Ronald Reagan did not trade arms for hostages speech", "Reagan arms hostages address full"]),
        seed("S217", "hard", "James Clapper", "Director of National Intelligence", ["not wittingly", "collect data", "millions of Americans"], "Disclosures showed broad NSA collection programs inconsistent with the categorical impression left by Clapper's testimony.", "James Clapper congressional testimony surveillance", "Congressional testimony", ["James Clapper not wittingly testimony full", "Clapper collect data millions Americans hearing"]),
        seed("S218", "hard", "John Brennan", "CIA director", ["CIA did not hack", "Senate computers", "nothing further"], "The CIA inspector general later found that agency personnel improperly accessed Senate Intelligence Committee files.", "CIA Senate computer search", "Television interview", ["John Brennan CIA did not hack Senate computers interview", "John Brennan Senate computers denial full"]),
        seed("S219", "hard", "Richard Nixon", "U.S. president", ["White House staff", "not involved", "Watergate"], "Watergate investigations and recordings established White House involvement in the cover-up.", "Watergate scandal Nixon denial", "Press conference", ["Richard Nixon White House staff not involved Watergate statement", "Nixon Watergate denial press conference full"]),
        seed("S220", "hard", "James W. Johnston", "Tobacco executive", ["nicotine is not addictive", "not addictive"], "Scientific evidence establishes that nicotine is addictive.", "1994 tobacco executives congressional hearing", "Congressional testimony", ["James Johnston nicotine not addictive testimony", "tobacco CEO nicotine not addictive hearing full"]),
        seed("S221", "hard", "William Campbell", "Tobacco executive", ["nicotine is not addictive", "not addictive"], "Scientific evidence establishes that nicotine is addictive.", "1994 tobacco executives congressional hearing", "Congressional testimony", ["William Campbell nicotine not addictive testimony tobacco", "Philip Morris CEO nicotine hearing full"]),
        seed("S222", "hard", "Andrew Tisch", "Tobacco executive", ["nicotine is not addictive", "not addictive"], "Scientific evidence establishes that nicotine is addictive.", "1994 tobacco executives congressional hearing", "Congressional testimony", ["Andrew Tisch nicotine not addictive testimony", "Lorillard CEO nicotine hearing full"]),
        seed("S223", "hard", "Thomas Sandefur", "Tobacco executive", ["nicotine is not addictive", "not addictive"], "Scientific evidence establishes that nicotine is addictive.", "1994 tobacco executives congressional hearing", "Congressional testimony", ["Thomas Sandefur nicotine not addictive testimony", "Brown Williamson CEO nicotine hearing full"]),
        seed("S224", "hard", "Tony Hayward", "BP chief executive", ["environmental impact", "very modest", "oil spill"], "The Deepwater Horizon spill caused extensive and long-lasting environmental damage.", "Deepwater Horizon oil spill", "Television interview", ["Tony Hayward environmental impact very modest interview", "BP CEO modest environmental impact full"]),
        seed("S225", "hard", "Michael Horn", "Volkswagen U.S. chief executive", ["couple of software engineers", "did not know", "emissions"], "Volkswagen admitted installing defeat-device software across a large number of diesel vehicles.", "Volkswagen emissions scandal", "Congressional testimony", ["Michael Horn couple software engineers testimony", "Volkswagen CEO emissions hearing full"]),
    ],
}

for filename, additions in ADDITIONS.items():
    path = SEED_DIR / filename
    values = json.loads(path.read_text(encoding="utf-8"))
    existing = {str(value.get("seedId")) for value in values}
    values.extend(value for value in additions if value["seedId"] not in existing)
    path.write_text(json.dumps(values, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    print(f"{filename}: {len(values)} seeds")

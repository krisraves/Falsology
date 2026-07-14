const queries = [
  ["T01", "NASA day on Venus longer than a year"],
  ["T02", "sharks older than trees fact"],
  ["T03", "octopus three hearts blue blood fact"],
  ["T04", "wombat cube shaped poop fact"],
  ["T05", "male seahorses give birth fact"],
  ["T06", "polar bears have black skin fact"],
  ["T07", "flamingos are born gray fact"],
  ["T08", "tardigrades survive vacuum of space fact"],
  ["T09", "Saturn would float in water fact"],
  ["T10", "lightning hotter than surface of the sun fact"],
  ["T11", "cloud weighs a million pounds fact"],
  ["T12", "bananas are berries strawberries are not fact"],
  ["T13", "Eiffel Tower grows in summer heat fact"],
  ["T14", "Cleopatra closer to moon landing than pyramids fact"],
  ["T15", "Oxford University older than Aztec Empire fact"],
  ["T16", "Nintendo founded in 1889 fact"],
  ["T17", "wood frog freezes solid survives fact"],
  ["T18", "koala fingerprints fact"],
  ["T19", "crows recognize human faces fact"],
  ["T20", "dolphins have names signature whistles fact"],
  ["T21", "mantis shrimp punch creates light fact"],
  ["T22", "sloths hold breath longer than dolphins fact"],
  ["T23", "turtles breathe through their butts fact"],
  ["T24", "honey never spoils fact"],
  ["T25", "water boils and freezes at same time triple point"],
  ["L01", "Bill Clinton I did not have sexual relations"],
  ["L02", "Richard Nixon I am not a crook"],
  ["L03", "Lance Armstrong I have never doped interview"],
  ["L04", "tobacco CEOs nicotine is not addictive Congress"],
  ["L05", "Elizabeth Holmes one drop blood hundreds tests interview"],
  ["L06", "Volkswagen clean diesel commercial"],
  ["L07", "Ken Lay Enron company strong interview"],
  ["L08", "Bernie Madoff impossible for violation to go undetected interview"],
  ["L09", "Pete Rose never bet on baseball interview"],
  ["L10", "Marion Jones never used steroids press conference"],
  ["L11", "Ryan Lochte robbed at gunpoint interview Rio"],
  ["L12", "Trevor Milton Nikola fully functioning truck interview"],
  ["L13", "Fyre Festival luxury promotional video"],
  ["L14", "Purdue Pharma OxyContin less addictive promotional video"],
  ["L15", "Juul totally safe testimony video"],
  ["L16", "Sam Bankman Fried customer funds safe interview FTX"],
  ["L17", "George Santos worked at Goldman Sachs interview"],
  ["L18", "Sean Spicer largest audience ever press briefing"],
  ["L19", "Alex Jones Sandy Hook staged crisis actors video"],
  ["L20", "Rudy Giuliani Dominion voting machines fraud press conference"],
  ["L21", "Flint water safe official statement video"],
  ["L22", "Colin Powell Iraq weapons of mass destruction UN speech"],
  ["L23", "BP oil spill tiny compared to ocean Tony Hayward"],
  ["L24", "Balloon Boy father not a hoax interview"],
  ["L25", "Listerine prevents colds vintage commercial"],
] as const;

export default function ResearchClipsPage() {
  return (
    <main style={{ padding: 24, fontFamily: "sans-serif" }}>
      <h1>Temporary clip research</h1>
      <ol>
        {queries.map(([id, query]) => {
          const url = `https://inv.nadeko.net/api/v1/search?q=${encodeURIComponent(query)}&type=video&duration=short`;
          return <li key={id}><a href={url}>{id}: {query}</a></li>;
        })}
      </ol>
    </main>
  );
}

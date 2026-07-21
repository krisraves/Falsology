import type { Metadata } from "next";
import { GameClient } from "@/components/GameClient";
import { claims } from "@/lib/claims";

export const metadata: Metadata = {
  title: "Play the Ranked Lies Deck",
  description: "Watch a short documented false statement, make the call, then check the evidence.",
};

export default function PlayPage() {
  return (
    <GameClient
      initialClaims={claims}
      mode="random"
      levelLabel="Ranked lies"
    />
  );
}

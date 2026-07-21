import type { Metadata } from "next";
import { GameClient } from "@/components/GameClient";
import { claims } from "@/lib/claims";

export const metadata: Metadata = {
  title: "Play 500 Truth-or-Lie Claims",
  description: "Hear 250 unbelievable truths and 250 important lies in one balanced shuffled deck.",
};

export default function PlayPage() {
  return <GameClient initialClaims={claims} mode="random" levelLabel="500 claims" />;
}

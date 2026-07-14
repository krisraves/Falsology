import type { Metadata } from "next";
import { GameClient } from "@/components/GameClient";
import { claims } from "@/lib/claims";

export const metadata: Metadata = {
  title: "Open a Detective Case",
  description: "Watch a real spoken statement, set your confidence, decide whether it survives the evidence, and sharpen your discernment.",
};

export default function PlayPage() {
  return <GameClient initialClaims={claims} mode="random" />;
}

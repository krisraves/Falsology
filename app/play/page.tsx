import type { Metadata } from "next";
import { GameClient } from "@/components/GameClient";
import { claims } from "@/lib/claims";

export const metadata: Metadata = {
  title: "Play Truth or Lie",
  description: "Watch a public claim, choose Truth or Lie, and inspect the evidence behind the verdict.",
};

export default function PlayPage() {
  return <main><GameClient initialClaims={claims} mode="random" /></main>;
}

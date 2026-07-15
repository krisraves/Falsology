import type { Metadata } from "next";
import { GameClient } from "@/components/GameClient";
import { claims } from "@/lib/claims";
import type { Difficulty } from "@/lib/types";

export const metadata: Metadata = {
  title: "Play Truth or Lie",
  description: "Watch a short direct statement, choose Truth or Lie, then check the evidence.",
};

const levels: Record<string, { difficulty: Difficulty; label: string }> = {
  easy: { difficulty: "easy", label: "Easy" },
  hard: { difficulty: "medium", label: "Hard" },
  expert: { difficulty: "hard", label: "Expert" },
};

export default async function PlayPage({
  searchParams,
}: {
  searchParams: Promise<{ difficulty?: string }>;
}) {
  const { difficulty } = await searchParams;
  const level = difficulty ? levels[difficulty] : undefined;
  const selectedClaims = level
    ? claims.filter((claim) => claim.difficulty === level.difficulty)
    : claims;

  return (
    <GameClient
      initialClaims={selectedClaims}
      mode="random"
      levelLabel={level?.label ?? "Mixed"}
    />
  );
}

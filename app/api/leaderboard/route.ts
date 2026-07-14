import { NextResponse } from "next/server";

export function GET() {
  return NextResponse.json({
    mode: "guest",
    leaderboard: [],
    message: "The public leaderboard activates when account storage is configured.",
  });
}

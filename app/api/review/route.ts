import { NextRequest, NextResponse } from "next/server";

export async function POST(request: NextRequest) {
  let body: unknown;
  try {
    body = await request.json();
  } catch {
    return NextResponse.json({ error: "Invalid JSON" }, { status: 400 });
  }

  const record = body as Record<string, unknown>;
  const rating = typeof record.rating === "number" ? Math.round(record.rating) : 0;
  const details = typeof record.details === "string" ? record.details.slice(0, 1200) : "";
  const difficulty = typeof record.difficulty === "string" ? record.difficulty.slice(0, 60) : "Unknown";
  const sectionScore = typeof record.sectionScore === "string" ? record.sectionScore.slice(0, 30) : "";
  const page = typeof record.page === "string" ? record.page.slice(0, 500) : "";

  if (rating < 1 || rating > 5) {
    return NextResponse.json({ error: "A rating from 1 to 5 is required" }, { status: 422 });
  }

  const review = {
    rating,
    details,
    difficulty,
    sectionScore,
    page,
    submittedAt: new Date().toISOString(),
    userAgent: request.headers.get("user-agent")?.slice(0, 300) || "unknown",
  };

  const webhook = process.env.REVIEW_WEBHOOK_URL;
  if (webhook) {
    try {
      const response = await fetch(webhook, {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify(review),
        signal: AbortSignal.timeout(5000),
      });
      if (!response.ok) throw new Error("Webhook rejected review");
    } catch {
      return NextResponse.json({ error: "Review storage unavailable" }, { status: 503 });
    }
  }

  return NextResponse.json({ accepted: true, stored: Boolean(webhook) }, { status: 202 });
}

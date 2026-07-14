import { NextRequest, NextResponse } from "next/server";

export async function POST(request: NextRequest) {
  let body: unknown;
  try {
    body = await request.json();
  } catch {
    return NextResponse.json({ error: "Invalid JSON" }, { status: 400 });
  }

  const record = body as Record<string, unknown>;
  const claimId = typeof record.claimId === "string" ? record.claimId.slice(0, 120) : "";
  const reason = typeof record.reason === "string" ? record.reason.slice(0, 120) : "";
  const details = typeof record.details === "string" ? record.details.slice(0, 1200) : "";
  const page = typeof record.page === "string" ? record.page.slice(0, 500) : "";

  if (!claimId || !reason) {
    return NextResponse.json({ error: "Claim and reason are required" }, { status: 422 });
  }

  const report = {
    claimId,
    reason,
    details,
    page,
    submittedAt: new Date().toISOString(),
    userAgent: request.headers.get("user-agent")?.slice(0, 300) || "unknown",
  };

  const webhook = process.env.REPORT_WEBHOOK_URL;
  if (webhook) {
    try {
      const response = await fetch(webhook, {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify(report),
        signal: AbortSignal.timeout(5000),
      });
      if (!response.ok) throw new Error("Webhook rejected report");
    } catch {
      return NextResponse.json({ error: "Report storage unavailable" }, { status: 503 });
    }
  }

  return NextResponse.json({ accepted: true, stored: Boolean(webhook) }, { status: 202 });
}

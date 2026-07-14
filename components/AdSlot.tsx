"use client";

import { useEffect } from "react";

type Placement = "leaderboard" | "sidebar" | "verdict" | "interstitial" | "inline";

const slots: Record<Placement, string | undefined> = {
  leaderboard: process.env.NEXT_PUBLIC_ADSENSE_LEADERBOARD_SLOT,
  sidebar: process.env.NEXT_PUBLIC_ADSENSE_SIDEBAR_SLOT,
  verdict: process.env.NEXT_PUBLIC_ADSENSE_VERDICT_SLOT,
  interstitial: process.env.NEXT_PUBLIC_ADSENSE_INTERSTITIAL_SLOT,
  inline: process.env.NEXT_PUBLIC_ADSENSE_INLINE_SLOT,
};

declare global {
  interface Window {
    adsbygoogle?: Record<string, never>[];
  }
}

export function AdSlot({
  label = "Advertisement",
  compact = false,
  placement = "inline",
}: {
  label?: string;
  compact?: boolean;
  placement?: Placement;
}) {
  const client = process.env.NEXT_PUBLIC_GOOGLE_ADSENSE_CLIENT;
  const slot = slots[placement];

  useEffect(() => {
    if (!client || !slot) return;
    try {
      (window.adsbygoogle = window.adsbygoogle || []).push({});
    } catch {
      // Ad blockers and unfilled inventory must not break gameplay.
    }
  }, [client, slot]);

  if (!client || !slot) {
    return (
      <aside className={`ad-slot detective-ad ad-${placement} ${compact ? "ad-slot-compact" : ""}`} aria-label={label}>
        <span>{label}</span>
        <p>Reserved sponsor placement</p>
      </aside>
    );
  }

  return (
    <aside className={`ad-slot detective-ad ad-${placement} ${compact ? "ad-slot-compact" : ""}`} aria-label={label}>
      <span className="ad-disclosure">{label}</span>
      <ins
        className="adsbygoogle"
        style={{ display: "block", width: "100%" }}
        data-ad-client={client}
        data-ad-slot={slot}
        data-ad-format="auto"
        data-full-width-responsive="true"
      />
    </aside>
  );
}

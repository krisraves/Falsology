import type { Claim } from "@/lib/types";

const SITE_ORIGIN = (process.env.NEXT_PUBLIC_SITE_URL || "https://falsology.vercel.app").replace(/\/$/, "");

function formatTime(seconds: number) {
  const minutes = Math.floor(seconds / 60);
  return `${minutes}:${String(seconds % 60).padStart(2, "0")}`;
}

export function MediaPanel({ claim, compact = false }: { claim: Claim; compact?: boolean }) {
  const { media } = claim;
  const params = new URLSearchParams({
    start: String(media.startSeconds),
    end: String(media.endSeconds),
    playsinline: "1",
    rel: "0",
    controls: "1",
    cc_load_policy: "1",
    origin: SITE_ORIGIN,
  });

  return (
    <div className={`media-frame detective-media ${compact ? "media-frame-compact" : ""}`}>
      <iframe
        src={`https://www.youtube.com/embed/${media.youtubeId}?${params.toString()}`}
        title={`${claim.person}: ${claim.claim}`}
        allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share"
        allowFullScreen
        loading="eager"
        referrerPolicy="strict-origin-when-cross-origin"
      />
      <div className="clip-window" aria-label="Selected clip timeframe">
        <span>CLIP</span> {formatTime(media.startSeconds)}–{formatTime(media.endSeconds)}
      </div>
      <a className="direct-media-link" href={media.url} target="_blank" rel="noreferrer">
        Full source ↗
      </a>
    </div>
  );
}

import type { Claim } from "@/lib/types";

export function MediaPanel({ claim, compact = false }: { claim: Claim; compact?: boolean }) {
  const { media } = claim;
  if (media.type === "youtube" && media.youtubeId) {
    const params = new URLSearchParams({
      rel: "0",
      modestbranding: "1",
      playsinline: "1",
    });
    if (media.startSeconds) params.set("start", String(media.startSeconds));
    if (media.endSeconds) params.set("end", String(media.endSeconds));
    return (
      <div className={`media-frame ${compact ? "media-frame-compact" : ""}`}>
        <iframe
          src={`https://www.youtube-nocookie.com/embed/${media.youtubeId}?${params}`}
          title={`${claim.person}: ${claim.claim}`}
          allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share"
          allowFullScreen
          loading="lazy"
        />
      </div>
    );
  }

  return (
    <div className={`quote-media ${compact ? "quote-media-compact" : ""}`}>
      <div className="signal-lines" aria-hidden="true"><i /><i /><i /><i /><i /></div>
      <div className="quote-chip">ARCHIVED CLAIM</div>
      <blockquote>“{claim.claim}”</blockquote>
      <div className="quote-meta">
        <span>{claim.person}</span>
        <span>{new Date(`${claim.date}T00:00:00`).getFullYear()}</span>
      </div>
      {media.url ? (
        <a href={media.url} target="_blank" rel="noreferrer" className="button button-light button-small">
          {media.label || "Open source media"} <span aria-hidden="true">↗</span>
        </a>
      ) : null}
    </div>
  );
}

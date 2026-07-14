import type { Claim } from "@/lib/types";

const SITE_ORIGIN = (process.env.NEXT_PUBLIC_SITE_URL || "https://falsology.vercel.app").replace(/\/$/, "");

const directLinkStyle = {
  position: "absolute" as const,
  left: 12,
  bottom: 12,
  zIndex: 4,
  padding: "8px 12px",
  borderRadius: 999,
  background: "rgba(11, 13, 15, .82)",
  color: "white",
  fontSize: ".72rem",
  fontWeight: 800,
  backdropFilter: "blur(6px)",
};

function DirectMediaLink({ url, label }: { url?: string; label?: string }) {
  if (!url) return null;
  return (
    <a href={url} target="_blank" rel="noreferrer" style={directLinkStyle}>
      {label || "Open source media"} <span aria-hidden="true">↗</span>
    </a>
  );
}

export function MediaPanel({ claim, compact = false }: { claim: Claim; compact?: boolean }) {
  const { media } = claim;

  if (media.type === "youtube" && media.youtubeId) {
    const params = new URLSearchParams({
      rel: "0",
      playsinline: "1",
      origin: SITE_ORIGIN,
    });
    if (media.startSeconds) params.set("start", String(media.startSeconds));
    if (media.endSeconds) params.set("end", String(media.endSeconds));

    return (
      <div className={`media-frame ${compact ? "media-frame-compact" : ""}`}>
        <iframe
          src={`https://www.youtube.com/embed/${media.youtubeId}?${params.toString()}`}
          title={`${claim.person}: ${claim.claim}`}
          allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share"
          allowFullScreen
          loading="lazy"
          referrerPolicy="strict-origin-when-cross-origin"
        />
        <DirectMediaLink url={media.url} label="Open directly on YouTube" />
      </div>
    );
  }

  if (media.type === "video" && media.url) {
    const end = media.endSeconds ? `,${media.endSeconds}` : "";
    const src = media.startSeconds ? `${media.url}#t=${media.startSeconds}${end}` : media.url;
    return (
      <div className={`media-frame ${compact ? "media-frame-compact" : ""}`}>
        <video
          controls
          playsInline
          preload="metadata"
          style={{ width: "100%", height: "100%", objectFit: "contain" }}
          aria-label={`${claim.person}: ${claim.claim}`}
        >
          <source src={src} type={media.mimeType || "video/webm"} />
          Your browser cannot play this archived video.
        </video>
      </div>
    );
  }

  if (media.type === "audio" && media.url) {
    return (
      <div className={`quote-media ${compact ? "quote-media-compact" : ""}`}>
        <div className="quote-chip">ARCHIVAL AUDIO</div>
        <blockquote>“{claim.claim}”</blockquote>
        <audio controls preload="metadata" style={{ width: "100%" }}>
          <source src={media.url} type={media.mimeType || "audio/mpeg"} />
          Your browser cannot play this archived audio.
        </audio>
      </div>
    );
  }

  if (media.type === "archive" && media.url) {
    return (
      <div className={`media-frame ${compact ? "media-frame-compact" : ""}`}>
        <iframe
          src={media.url}
          title={`${claim.person}: ${claim.claim}`}
          allow="autoplay; fullscreen"
          allowFullScreen
          loading="lazy"
          referrerPolicy="strict-origin-when-cross-origin"
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
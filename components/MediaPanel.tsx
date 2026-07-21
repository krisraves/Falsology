import { ClipPlayer } from "@/components/ClipPlayer";
import { GeneratedClipPlayer } from "@/components/GeneratedClipPlayer";
import type { Claim } from "@/lib/types";

export function MediaPanel({
  claim,
  compact = false,
  onUnavailable,
}: {
  claim: Claim;
  compact?: boolean;
  onUnavailable?: () => boolean;
}) {
  const { media } = claim;
  const title = `${claim.person}: ${claim.claim}`;

  return (
    <div className={`media-frame detective-media ${compact ? "media-frame-compact" : ""}`}>
      {media.type === "youtube" ? (
        <ClipPlayer
          videoId={media.youtubeId}
          title={title}
          startSeconds={media.startSeconds}
          endSeconds={media.endSeconds}
          sourceUrl={media.url}
          onUnavailable={onUnavailable}
        />
      ) : (
        <GeneratedClipPlayer
          src={media.src}
          title={title}
          startSeconds={media.startSeconds}
          endSeconds={media.endSeconds}
          sourceUrl={media.url}
          onUnavailable={onUnavailable}
        />
      )}
    </div>
  );
}

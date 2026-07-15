import { ClipPlayer } from "@/components/ClipPlayer";
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

  return (
    <div className={`media-frame detective-media ${compact ? "media-frame-compact" : ""}`}>
      <ClipPlayer
        videoId={media.youtubeId}
        title={`${claim.person}: ${claim.claim}`}
        startSeconds={media.startSeconds}
        endSeconds={media.endSeconds}
        sourceUrl={media.url}
        onUnavailable={onUnavailable}
      />
    </div>
  );
}

"use client";

import { useEffect, useRef, useState } from "react";

export function GeneratedClipPlayer({
  src,
  title,
  startSeconds,
  endSeconds,
  sourceUrl,
  onUnavailable,
}: {
  src: string;
  title: string;
  startSeconds: number;
  endSeconds: number;
  sourceUrl: string;
  onUnavailable?: () => boolean;
}) {
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const [ready, setReady] = useState(false);
  const [playing, setPlaying] = useState(false);
  const [ended, setEnded] = useState(false);
  const [progress, setProgress] = useState(0);
  const [failed, setFailed] = useState(false);
  const duration = Math.max(0.1, endSeconds - startSeconds);

  useEffect(() => {
    const video = videoRef.current;
    if (!video) return;
    video.pause();
    setPlaying(false);
    setEnded(false);
    setProgress(0);
    setReady(false);
    setFailed(false);
    video.load();
  }, [src, startSeconds, endSeconds]);

  function seekToStart() {
    const video = videoRef.current;
    if (!video) return;
    video.currentTime = startSeconds;
    setProgress(0);
    setEnded(false);
  }

  async function togglePlayback() {
    const video = videoRef.current;
    if (!video || failed) return;
    if (video.paused) {
      if (ended || video.currentTime < startSeconds || video.currentTime >= endSeconds) seekToStart();
      try {
        await video.play();
      } catch {
        setFailed(true);
      }
    } else {
      video.pause();
    }
  }

  return (
    <div className="clip-player">
      <div className="clip-player-stage">
        <video
          ref={videoRef}
          className="generated-clip-video"
          src={src}
          preload="metadata"
          playsInline
          aria-label={title}
          onLoadedMetadata={() => {
            seekToStart();
            setReady(true);
          }}
          onSeeked={() => setReady(true)}
          onPlay={() => setPlaying(true)}
          onPause={() => setPlaying(false)}
          onTimeUpdate={(event) => {
            const video = event.currentTarget;
            if (video.currentTime >= endSeconds - 0.05) {
              video.pause();
              video.currentTime = startSeconds;
              setEnded(true);
              setProgress(100);
              return;
            }
            const elapsed = Math.max(0, video.currentTime - startSeconds);
            setProgress(Math.min(100, (elapsed / duration) * 100));
          }}
          onError={() => {
            setFailed(true);
            onUnavailable?.();
          }}
        />

        {!ready && !failed ? <div className="clip-player-loading">Loading generated claim clip…</div> : null}
        {failed ? <div className="clip-player-error">This generated clip is temporarily unavailable. Use the source link below.</div> : null}
        {ready && !playing && !failed ? (
          <button className="clip-player-hitbox" type="button" onClick={togglePlayback} aria-label={ended ? "Replay clip" : "Play clip"}>
            <span className="clip-player-play-icon" aria-hidden="true">▶</span>
          </button>
        ) : null}
      </div>

      <div className="clip-player-controls">
        <button type="button" onClick={togglePlayback} disabled={!ready || failed}>
          {playing ? "Pause" : ended ? "Replay" : "Play"}
        </button>
        <progress value={progress} max="100" aria-label="Shortened clip progress" />
        <span>Original Falsology narration</span>
      </div>

      <div className="clip-player-meta">
        <span>Ten seconds before and after the spoken claim</span>
        <a href={sourceUrl} target="_blank" rel="noreferrer">Full 500-claim reel ↗</a>
      </div>
    </div>
  );
}

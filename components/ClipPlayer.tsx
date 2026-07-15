"use client";

import { useEffect, useId, useRef, useState } from "react";

type VideoRange = {
  videoId: string;
  title: string;
  startSeconds: number;
  endSeconds: number;
  sourceUrl: string;
};

type VideoIdOptions = {
  videoId: string;
  startSeconds: number;
  endSeconds: number;
};

type YouTubePlayer = {
  cueVideoById(options: VideoIdOptions): void;
  loadVideoById(options: VideoIdOptions): void;
  playVideo(): void;
  pauseVideo(): void;
  stopVideo(): void;
  getCurrentTime(): number;
  destroy(): void;
};

type PlayerEvent = { target: YouTubePlayer };
type StateEvent = PlayerEvent & { data: number };
type ErrorEvent = { data: number };

type YouTubeApi = {
  Player: new (
    element: HTMLElement,
    options: {
      videoId: string;
      playerVars: Record<string, number | string>;
      events: {
        onReady(event: PlayerEvent): void;
        onStateChange(event: StateEvent): void;
        onError(event: ErrorEvent): void;
      };
    },
  ) => YouTubePlayer;
  PlayerState: {
    ENDED: number;
    PLAYING: number;
    PAUSED: number;
    CUED: number;
  };
};

declare global {
  interface Window {
    YT?: YouTubeApi;
    onYouTubeIframeAPIReady?: () => void;
  }
}

let apiPromise: Promise<YouTubeApi> | null = null;

function loadYouTubeApi(): Promise<YouTubeApi> {
  if (window.YT?.Player) return Promise.resolve(window.YT);
  if (apiPromise) return apiPromise;

  apiPromise = new Promise<YouTubeApi>((resolve, reject) => {
    const previousReady = window.onYouTubeIframeAPIReady;
    const timeout = window.setTimeout(() => reject(new Error("YouTube player timed out.")), 15000);

    window.onYouTubeIframeAPIReady = () => {
      previousReady?.();
      window.clearTimeout(timeout);
      if (window.YT?.Player) resolve(window.YT);
      else reject(new Error("YouTube player did not initialize."));
    };

    if (!document.querySelector('script[src="https://www.youtube.com/iframe_api"]')) {
      const script = document.createElement("script");
      script.src = "https://www.youtube.com/iframe_api";
      script.async = true;
      script.onerror = () => {
        window.clearTimeout(timeout);
        reject(new Error("YouTube player could not be loaded."));
      };
      document.head.appendChild(script);
    }
  });

  return apiPromise;
}

function formatTime(seconds: number) {
  const wholeSeconds = Math.max(0, Math.floor(seconds));
  const minutes = Math.floor(wholeSeconds / 60);
  return `${minutes}:${String(wholeSeconds % 60).padStart(2, "0")}`;
}

export function ClipPlayer({ videoId, title, startSeconds, endSeconds, sourceUrl }: VideoRange) {
  const reactId = useId();
  const mountRef = useRef<HTMLDivElement>(null);
  const playerRef = useRef<YouTubePlayer | null>(null);
  const [ready, setReady] = useState(false);
  const [playing, setPlaying] = useState(false);
  const [ended, setEnded] = useState(false);
  const [elapsed, setElapsed] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const duration = Math.max(1, endSeconds - startSeconds);
  const progress = Math.min(100, Math.max(0, (elapsed / duration) * 100));
  const mountId = `clip-player-${reactId.replace(/:/g, "")}`;

  useEffect(() => {
    let cancelled = false;

    loadYouTubeApi()
      .then((YT) => {
        if (cancelled || !mountRef.current) return;

        playerRef.current = new YT.Player(mountRef.current, {
          videoId,
          playerVars: {
            controls: 0,
            disablekb: 1,
            playsinline: 1,
            rel: 0,
            fs: 0,
            iv_load_policy: 3,
            cc_load_policy: 1,
            origin: window.location.origin,
          },
          events: {
            onReady: ({ target }) => {
              target.cueVideoById({ videoId, startSeconds, endSeconds });
              setReady(true);
            },
            onStateChange: ({ data, target }) => {
              setPlaying(data === YT.PlayerState.PLAYING);
              if (data === YT.PlayerState.ENDED) {
                target.cueVideoById({ videoId, startSeconds, endSeconds });
                setEnded(true);
                setElapsed(duration);
              }
            },
            onError: ({ data }) => {
              setPlaying(false);
              setError(`This source could not be played (YouTube error ${data}).`);
            },
          },
        });
      })
      .catch((loadError: unknown) => {
        if (!cancelled) {
          setError(loadError instanceof Error ? loadError.message : "The video player could not be loaded.");
        }
      });

    return () => {
      cancelled = true;
      playerRef.current?.destroy();
      playerRef.current = null;
    };
  }, [duration, endSeconds, startSeconds, videoId]);

  useEffect(() => {
    if (!playing) return;

    const interval = window.setInterval(() => {
      const player = playerRef.current;
      if (!player) return;

      const current = player.getCurrentTime();
      const clipElapsed = Math.max(0, current - startSeconds);
      setElapsed(Math.min(duration, clipElapsed));

      if (current >= endSeconds - 0.15) {
        player.stopVideo();
        player.cueVideoById({ videoId, startSeconds, endSeconds });
        setPlaying(false);
        setEnded(true);
        setElapsed(duration);
      }
    }, 150);

    return () => window.clearInterval(interval);
  }, [duration, endSeconds, playing, startSeconds, videoId]);

  function playOrPause() {
    const player = playerRef.current;
    if (!player || !ready) return;

    if (playing) {
      player.pauseVideo();
      setPlaying(false);
      return;
    }

    if (ended || elapsed === 0) {
      setEnded(false);
      setElapsed(0);
      player.loadVideoById({ videoId, startSeconds, endSeconds });
      return;
    }

    player.playVideo();
  }

  function replay() {
    const player = playerRef.current;
    if (!player || !ready) return;
    setEnded(false);
    setElapsed(0);
    player.loadVideoById({ videoId, startSeconds, endSeconds });
  }

  return (
    <div className="clip-player" data-ready={ready ? "true" : "false"}>
      <div className="clip-player-stage">
        <div id={mountId} ref={mountRef} className="clip-player-mount" />
        <button
          type="button"
          className="clip-player-hitbox"
          onClick={playOrPause}
          disabled={!ready || Boolean(error)}
          aria-label={playing ? "Pause shortened clip" : ended ? "Replay shortened clip" : "Play shortened clip"}
        >
          {!playing ? <span className="clip-player-play-icon" aria-hidden="true">{ended ? "↻" : "▶"}</span> : null}
        </button>
        {!ready && !error ? <div className="clip-player-loading">Preparing clip…</div> : null}
        {error ? <div className="clip-player-error">{error}</div> : null}
      </div>

      <div className="clip-player-controls">
        <button type="button" onClick={ended ? replay : playOrPause} disabled={!ready || Boolean(error)}>
          {playing ? "Pause" : ended ? "Replay" : "Play"}
        </button>
        <progress value={progress} max="100" aria-label="Shortened clip progress" />
        <span>{formatTime(elapsed)} / {formatTime(duration)}</span>
      </div>

      <div className="clip-player-meta">
        <span>Selected excerpt: {formatTime(startSeconds)}–{formatTime(endSeconds)}</span>
        <a href={sourceUrl} target="_blank" rel="noreferrer">Full source ↗</a>
      </div>
      <span className="sr-only">{title}</span>
    </div>
  );
}

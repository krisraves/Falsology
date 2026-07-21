#!/usr/bin/env python3
"""Generate one seekable MP4 containing 500 fixed-length Falsology claim clips.

Each case occupies exactly 32 seconds:
- 10 seconds of setup
- 12 seconds containing the spoken claim, padded or time-compressed as needed
- 10 seconds of decision time

The website seeks into this master reel using the offsets stored in all-500-cases.json.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import tempfile
import wave
from pathlib import Path

SAMPLE_RATE = 22_050
CONTEXT_SECONDS = 10
STATEMENT_SECONDS = 12
SEGMENT_SECONDS = CONTEXT_SECONDS + STATEMENT_SECONDS + CONTEXT_SECONDS
EXPECTED_CASES = 500


def run(command: list[str]) -> None:
    subprocess.run(command, check=True)


def duration(path: Path) -> float:
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=nw=1:nk=1", str(path)],
        check=True,
        capture_output=True,
        text=True,
    )
    return float(result.stdout.strip())


def atempo_chain(speed: float) -> str:
    factors: list[float] = []
    while speed > 2.0:
        factors.append(2.0)
        speed /= 2.0
    while speed < 0.5:
        factors.append(0.5)
        speed /= 0.5
    factors.append(speed)
    return ",".join(f"atempo={factor:.8f}" for factor in factors)


def render_voice_slot(espeak: str, text: str, work: Path, index: int) -> bytes:
    raw = work / f"voice-{index:03d}.wav"
    slot = work / f"slot-{index:03d}.wav"
    run([espeak, "-v", "en-us", "-s", "165", "-w", str(raw), text])
    raw_duration = max(0.1, duration(raw))
    filters: list[str] = []
    if raw_duration > STATEMENT_SECONDS - 0.35:
        filters.append(atempo_chain(raw_duration / (STATEMENT_SECONDS - 0.35)))
    filters.extend([f"apad=pad_dur={STATEMENT_SECONDS}", f"atrim=0:{STATEMENT_SECONDS}"])
    run([
        "ffmpeg", "-y", "-loglevel", "error", "-i", str(raw),
        "-af", ",".join(filters), "-ar", str(SAMPLE_RATE), "-ac", "1", "-sample_fmt", "s16", str(slot),
    ])
    with wave.open(str(slot), "rb") as reader:
        frames = reader.readframes(reader.getnframes())
    expected_bytes = SAMPLE_RATE * STATEMENT_SECONDS * 2
    frames = frames[:expected_bytes]
    if len(frames) < expected_bytes:
        frames += b"\x00" * (expected_bytes - len(frames))
    raw.unlink(missing_ok=True)
    slot.unlink(missing_ok=True)
    return frames


def build_audio(claims: list[dict], output: Path, work: Path, espeak: str) -> None:
    silence = b"\x00\x00" * SAMPLE_RATE * CONTEXT_SECONDS
    with wave.open(str(output), "wb") as writer:
        writer.setnchannels(1)
        writer.setsampwidth(2)
        writer.setframerate(SAMPLE_RATE)
        for index, claim in enumerate(claims, start=1):
            writer.writeframesraw(silence)
            writer.writeframesraw(render_voice_slot(espeak, str(claim["claim"]), work, index))
            writer.writeframesraw(silence)
            if index % 25 == 0:
                print(f"Rendered narration {index}/{len(claims)}", flush=True)


def build_template(output: Path, work: Path) -> None:
    font = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
    if not Path(font).exists():
        font = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    vf = ",".join([
        f"drawtext=fontfile={font}:text='FALSOLOGY':fontcolor=0xBAFF53:fontsize=58:x=(w-text_w)/2:y=78",
        f"drawtext=fontfile={font}:text='LISTEN CLOSELY':fontcolor=white:fontsize=34:x=(w-text_w)/2:y=180:enable='between(t,0,10)'",
        f"drawtext=fontfile={font}:text='CLAIM PLAYING':fontcolor=white:fontsize=34:x=(w-text_w)/2:y=180:enable='between(t,10,22)'",
        f"drawtext=fontfile={font}:text='TRUTH OR LIE?':fontcolor=white:fontsize=38:x=(w-text_w)/2:y=180:enable='between(t,22,32)'",
        f"drawtext=fontfile={font}:text='Check the evidence after your answer':fontcolor=0xAEB5AC:fontsize=20:x=(w-text_w)/2:y=270",
    ])
    run([
        "ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi",
        "-i", f"color=c=0x08111f:s=640x360:r=15:d={SEGMENT_SECONDS}",
        "-vf", vf, "-c:v", "libx264", "-preset", "veryfast", "-crf", "34",
        "-g", "15", "-keyint_min", "15", "-sc_threshold", "0", "-pix_fmt", "yuv420p", str(output),
    ])


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--catalog", default="data/all-500-cases.json")
    parser.add_argument("--output", default="dist/falsology-500-claim-reel.mp4")
    parser.add_argument("--manifest", default="dist/falsology-500-claim-reel.json")
    args = parser.parse_args()

    catalog = Path(args.catalog)
    claims = json.loads(catalog.read_text(encoding="utf-8"))
    if len(claims) != EXPECTED_CASES:
        raise SystemExit(f"Expected {EXPECTED_CASES} claims, found {len(claims)}")

    espeak = shutil.which("espeak-ng") or shutil.which("espeak")
    if not espeak:
        raise SystemExit("espeak-ng or espeak is required")
    if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
        raise SystemExit("ffmpeg and ffprobe are required")

    output = Path(args.output)
    manifest_path = Path(args.manifest)
    output.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="falsology-reel-") as directory:
        work = Path(directory)
        master_wav = work / "master.wav"
        master_audio = work / "master.m4a"
        template = work / "template.mp4"
        build_audio(claims, master_wav, work, espeak)
        run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(master_wav), "-c:a", "aac", "-b:a", "32k", str(master_audio)])
        build_template(template, work)
        total_seconds = len(claims) * SEGMENT_SECONDS
        run([
            "ffmpeg", "-y", "-loglevel", "error", "-stream_loop", str(len(claims) - 1), "-i", str(template),
            "-i", str(master_audio), "-t", str(total_seconds), "-map", "0:v:0", "-map", "1:a:0",
            "-c:v", "copy", "-c:a", "copy", "-movflags", "+faststart", str(output),
        ])

    actual_duration = duration(output)
    expected_duration = len(claims) * SEGMENT_SECONDS
    if abs(actual_duration - expected_duration) > 0.25:
        raise SystemExit(f"Unexpected reel duration {actual_duration}; expected {expected_duration}")

    manifest = {
        "caseCount": len(claims),
        "truthCount": sum(claim["verdict"] == "truth" for claim in claims),
        "lieCount": sum(claim["verdict"] == "lie" for claim in claims),
        "segmentSeconds": SEGMENT_SECONDS,
        "contextSecondsBefore": CONTEXT_SECONDS,
        "statementSlotSeconds": STATEMENT_SECONDS,
        "contextSecondsAfter": CONTEXT_SECONDS,
        "durationSeconds": actual_duration,
        "bytes": output.stat().st_size,
        "sha256": sha256(output),
        "assetName": output.name,
    }
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

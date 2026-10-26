"""Phase 0 benchmark: build one complete video end to end and record timings.

Steps: narration (Kokoro) -> keyframes (matplotlib) -> segments (FFmpeg zoom + fades)
-> join -> add audio -> subtitles (faster-whisper) -> preview -> benchmark.json

Usage:
    python phase0/run_benchmark.py --models models --out out/run1
    python phase0/run_benchmark.py --models models --out out/test --scenes 2   # quick test
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from yt_auto import render  # noqa: E402
from yt_auto.bench import Bench  # noqa: E402
from yt_auto.tts import Narrator  # noqa: E402
from yt_auto.visuals import render_keyframe  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--script", default=str(ROOT / "phase0" / "sample_script.json"))
    ap.add_argument("--models", default=str(ROOT / "models"))
    ap.add_argument("--out", default=str(ROOT / "out" / "run"))
    ap.add_argument("--scenes", type=int, default=0, help="limit number of scenes (0 = all)")
    ap.add_argument("--voice", default="af_heart")
    ap.add_argument("--skip-subtitles", action="store_true")
    args = ap.parse_args()

    script = json.loads(Path(args.script).read_text())
    scenes = script["scenes"][: args.scenes or None]
    out = Path(args.out)
    for sub in ("audio", "frames", "segments"):
        (out / sub).mkdir(parents=True, exist_ok=True)
    models = Path(args.models)
    bench = Bench()

    # 1. Narration, one file per scene
    with bench.stage("narration"):
        narrator = Narrator(models / "kokoro-v1.0.int8.onnx", models / "voices-v1.0.bin", voice=args.voice)
        scene_durations, wavs = [], []
        for sc in scenes:
            wav = out / "audio" / f"{sc['id']}.wav"
            scene_durations.append(narrator.speak(sc["narration"], wav))
            wavs.append(wav)
        render.concat_audio(wavs, out / "narration.wav")

    # 2. Keyframe images
    with bench.stage("keyframes"):
        frames = []  # (scene_index, path)
        for si, sc in enumerate(scenes):
            for ki, spec in enumerate(sc["keyframes"]):
                path = out / "frames" / f"{sc['id']}_{ki:02}.png"
                render_keyframe(spec, path)
                frames.append((si, path))

    # 3. Video segments: each scene's time is split equally across its keyframes
    with bench.stage("segments"):
        segments = []
        for si, sc in enumerate(scenes):
            scene_frames = [p for (s, p) in frames if s == si]
            each = scene_durations[si] / len(scene_frames)
            for i, img in enumerate(scene_frames):
                seg = out / "segments" / f"{img.stem}.mp4"
                render.make_segment(img, each, seg, zoom_in=(i % 2 == 0))
                segments.append(seg)

    # 4. Join segments and add the narration
    with bench.stage("assemble"):
        render.concat_video(segments, out / "video_noaudio.mp4")
        render.mux(out / "video_noaudio.mp4", out / "narration.wav", out / "video.mp4")

    # 5. Subtitles
    if not args.skip_subtitles:
        with bench.stage("subtitles"):
            from yt_auto.subtitles import make_srt

            n_subs = make_srt(out / "narration.wav", out / "subtitles.srt")
            bench.info["subtitle_lines"] = n_subs

    # 6. Small preview for quick checking
    with bench.stage("preview"):
        render.preview(out / "video.mp4", out / "preview_480p.mp4")

    video = out / "video.mp4"
    bench.info.update({
        "video_seconds": round(render.probe_duration(video), 1),
        "video_mb": round(video.stat().st_size / 1e6, 1),
        "scenes": len(scenes),
        "keyframes": len(frames),
        "voice": args.voice,
    })
    data = bench.save(out / "benchmark.json")
    print(json.dumps(data, indent=2))


if __name__ == "__main__":
    main()

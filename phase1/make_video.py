"""Phase 1: topic in, upload-ready video package out (owner reviews and uploads by hand).

Stages (each saves its result in --out; re-running with the same --out skips finished
stages, so a failed run does not spend free API quota twice):
  plan -> sources (Wikipedia) -> script -> fact-check -> narration (Kokoro)
  -> visual plan -> photos (NASA + Commons) -> keyframes -> segments (Ken Burns)
  -> video -> subtitles (our text, forced alignment) -> preview -> package

Usage:
    python phase1/make_video.py --topic "How does GPS know where you are?" --out out/gps
    python phase1/make_video.py --topic "..." --out out/test --scenes 2      # small test
"""
from __future__ import annotations

import argparse
import faulthandler
import json
import subprocess
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from yt_auto import align, gate, llm, owner_voice, package, render, research, shots, writer  # noqa: E402
from yt_auto.bench import Bench  # noqa: E402
from yt_auto.tts import Narrator  # noqa: E402
from yt_auto.visuals import render_keyframe  # noqa: E402

PHOTO_MOTIONS = ["zoom_in", "pan_right", "zoom_out", "pan_left"]


def cached(path: Path, make):
    """Load a stage's JSON result if it exists, else make and save it."""
    if path.exists():
        print(f"[resume] using saved {path.name}", flush=True)
        return json.loads(path.read_text(encoding="utf-8"))
    data = make()
    path.write_text(json.dumps(data, indent=1, ensure_ascii=False), encoding="utf-8")
    return data


def card_spec(card: dict, fallback_title: str) -> dict:
    """Turn a planned card into a renderer spec; fall back to a title card if it's incomplete."""
    t = card.get("type")
    ok = {
        "title": bool(card.get("title")),
        "stat": bool(card.get("value")) and bool(card.get("label")),
        "bullets": bool(card.get("items")),
        "flow": len(card.get("steps") or []) >= 2,
        "bars": len(card.get("labels") or []) >= 2 and len(card.get("labels") or []) == len(card.get("values") or []),
        "timeline": len(card.get("events") or []) >= 2,
        "compare": bool(card.get("left_points")) and bool(card.get("right_points")),
    }.get(t, False)
    if not ok:
        return {"type": "title", "title": card.get("title") or fallback_title, "subtitle": card.get("subtitle", "")}
    spec = {k: v for k, v in card.items() if v not in (None, "", [])}
    spec.setdefault("title", fallback_title)
    return spec


def short_credit(p: dict) -> str:
    if p["source"] == "nasa_image_library":
        return "Image: NASA"
    author = p["author"] if len(p["author"]) <= 40 else p["author"][:38] + "…"
    return f"Image: {author} / {p['licence']} / Wikimedia Commons"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--topic", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--models", default=str(ROOT / "models"))
    ap.add_argument("--scenes", type=int, default=0, help="keep only the first N scenes (small test); 0 = all")
    ap.add_argument("--voice", default="af_heart")
    ap.add_argument("--speed", type=float, default=0.9)
    ap.add_argument("--owner-audio", default="", help="folder with the owner's recordings (Phase 5 own-voice videos)")
    ap.add_argument("--stop-after-script", action="store_true",
                    help="stop after the fact-checked script and recording script (owner records next)")
    args = ap.parse_args()

    # Print every thread's stack before the workflow step's 45-minute limit kills us silently.
    faulthandler.dump_traceback_later(40 * 60, exit=True)
    out = Path(args.out)
    for sub in ("audio", "frames", "segments", "photos", "ffmpeg_logs", "llm"):
        (out / sub).mkdir(parents=True, exist_ok=True)
    render.LOG_DIR = out / "ffmpeg_logs"
    llm.LOG_DIR = out / "llm"
    bench = Bench()
    print(f"[diag] machine: {bench.report()['machine']}", flush=True)

    try:
        run(args, out, bench)
    finally:
        bench.info["llm_calls"] = llm.LOG
        bench.info["llm_calls_ok_by_model"] = dict(Counter(e["model"] for e in llm.LOG if e.get("status") == 200))
        if render.DIAGNOSTICS:
            (out / "diagnostics.json").write_text(json.dumps(render.DIAGNOSTICS, indent=2))
        bench.save(out / "report.json")


def run(args, out: Path, bench: Bench) -> None:
    # 1-4. Words: plan, sources, script, fact-check
    with bench.stage("script"):
        the_plan = cached(out / "plan.json", lambda: writer.plan(args.topic))
        sources = cached(out / "sources.json", lambda: research.gather(the_plan["wikipedia_titles"], out / "sources.json"))
        if not sources["articles"]:
            raise RuntimeError("No Wikipedia sources found; cannot write a sourced script")
        draft = cached(out / "script_draft.json", lambda: writer.write_script(args.topic, the_plan, sources))
        if (out / "script.json").exists():
            script = json.loads((out / "script.json").read_text(encoding="utf-8"))
            report = json.loads((out / "factcheck.json").read_text(encoding="utf-8"))
        else:
            script = json.loads(json.dumps(draft))
            writer.number_sentences(script)
            report = writer.fact_check(script, sources)
            (out / "script.json").write_text(json.dumps(script, indent=1, ensure_ascii=False), encoding="utf-8")
            (out / "factcheck.json").write_text(json.dumps(report, indent=1, ensure_ascii=False), encoding="utf-8")
        print(f"[script] {script['title']!r}: {writer.word_count(script)} words; fact-check: "
              f"{report['supported_first_pass']}/{report['checked']} passed first time, "
              f"{len(report['fixed'])} fixed, {len(report['dropped'])} dropped", flush=True)
        if args.scenes:
            script["scenes"] = script["scenes"][: args.scenes]
        owner_voice.recording_script(script, out / "recording_script.md")
    if args.stop_after_script:
        bench.info.update({"stopped_after": "script", "title": script["title"], "words": writer.word_count(script)})
        print(f"[script] stopped after the script: recording_script.md is ready", flush=True)
        return

    # 5. Narration with exact sentence times: Kokoro, or the owner's own recording (Phase 5)
    heard = None
    with bench.stage("narration"):
        if args.owner_audio:
            ov = owner_voice.prepare(Path(args.owner_audio), script, out, ROOT)
            sentences, scenes, total, heard = ov["sentences"], ov["scenes"], ov["total"], ov["heard"]
            bench.info["voice"] = "owner"
            bench.info["voice_match"] = {k: v for k, v in ov["match"].items() if k != "by_scene"}
        else:
            narrator = Narrator(Path(args.models) / "kokoro-v1.0.int8.onnx", Path(args.models) / "voices-v1.0.bin",
                                voice=args.voice, speed=args.speed)
            sentences, scenes, wavs, offset = [], [], [], 0.0
            for sc in script["scenes"]:
                wav = out / "audio" / f"{sc['id']}.wav"
                dur, spans = narrator.speak_timed([s["text"] for s in sc["sentences"]], wav)
                scenes.append({"id": sc["id"], "heading": sc["heading"], "start": offset, "end": offset + dur})
                for s, (a, b) in zip(sc["sentences"], spans):
                    sentences.append({"id": s["id"], "scene": sc["id"], "text": s["text"],
                                      "start": round(offset + a, 3), "end": round(offset + b, 3)})
                wavs.append(wav)
                offset += dur
            render.concat_audio(wavs, out / "narration.wav")
            total = render.probe_duration(out / "narration.wav")
            bench.info["voice"] = "kokoro"
        (out / "timing.json").write_text(json.dumps({"sentences": sentences, "scenes": scenes, "total": total}, indent=1))

    # 6-7. Visual plan and photos
    headings = {sc["id"]: sc["heading"] for sc in script["scenes"]}
    scene_text = {sc["id"]: " ".join(s["text"] for s in sc["sentences"]) for sc in script["scenes"]}
    with bench.stage("visual_plan"):
        visuals = cached(out / "visual_plan.json",
                         lambda: shots.plan_visuals(script["title"], shots.slots(sentences, total), headings))
    with bench.stage("photos"):
        if (out / "visuals.json").exists():
            visuals = json.loads((out / "visuals.json").read_text(encoding="utf-8"))
            photo_log = json.loads((out / "photo_log.json").read_text())
        else:
            photo_log = {"card_number_fixes": shots.check_card_numbers(visuals, scene_text)}
            shots.find_photos(visuals, out / "photos", photo_log)
            (out / "visuals.json").write_text(json.dumps(visuals, indent=1, ensure_ascii=False), encoding="utf-8")
            (out / "photo_log.json").write_text(json.dumps(photo_log, indent=1, ensure_ascii=False))

    # 8. Keyframes
    with bench.stage("keyframes"):
        for v in visuals:
            path = out / "frames" / f"{v['id']}.png"
            v["frame"] = str(path)
            if v.get("photo"):
                spec = {"type": "photo", "path": v["photo"]["path"], "credit": short_credit(v["photo"])}
            else:
                spec = card_spec(v.get("card") or {}, headings[v["scene"]])
            try:
                render_keyframe(spec, path)
            except Exception as e:  # noqa: BLE001 — one bad card must not stop the video
                print(f"[keyframes] {v['id']} {spec.get('type')} failed ({e!r}); using a title card", flush=True)
                render_keyframe({"type": "title", "title": headings[v["scene"]]}, path)

    # 9. Segments: timed from the exact slot boundaries; fades only at scene changes
    with bench.stage("segments"):
        segments, n_photo = [], 0
        for i, v in enumerate(visuals):
            frames = round(v["end"] * render.FPS) - round(v["start"] * render.FPS)
            if v.get("photo"):
                motion = PHOTO_MOTIONS[n_photo % len(PHOTO_MOTIONS)]
                n_photo += 1
            else:
                motion = "zoom_in" if i % 2 == 0 else "zoom_out"
            last = i + 1 == len(visuals)
            seg = out / "segments" / f"{v['id']}.mp4"
            render.make_segment(Path(v["frame"]), frames / render.FPS, seg, motion=motion,
                                fade_in=v["scene_start"], fade_out=last or visuals[i + 1]["scene_start"])
            segments.append(seg)

    # 10. Join and add narration
    with bench.stage("assemble"):
        render.concat_video(segments, out / "video_noaudio.mp4")
        render.mux(out / "video_noaudio.mp4", out / "narration.wav", out / "video.mp4")

    # 11. Subtitles from our own text (whisper only gives word timing, in its own process)
    with bench.stage("subtitles"):
        if heard is None:  # Kokoro videos: whisper word times now (own-voice videos already have them)
            r = subprocess.run([sys.executable, "-m", "yt_auto.subtitles", "--words", str(out / "narration.wav"),
                                str(out / "heard_words.json")], cwd=ROOT, capture_output=True, text=True,
                               stdin=subprocess.DEVNULL, timeout=900)
            heard = json.loads((out / "heard_words.json").read_text()) if r.returncode == 0 else []
            if r.returncode:
                print(f"[subtitles] whisper word timing failed, using sentence timing only:\n{r.stderr[-1500:]}",
                      flush=True)
        bench.info["subtitle_cues"] = align.write_srt(sentences, heard, out / "subtitles.srt")
        bench.info["whisper_words"] = len(heard)

    # 12. Preview
    with bench.stage("preview"):
        render.preview(out / "video.mp4", out / "preview_480p.mp4")

    # 13. Package for review
    n_photos = sum(1 for v in visuals if v.get("photo"))
    bench.info.update({
        "topic": args.topic, "title": script["title"], "words": writer.word_count(script),
        "video_seconds": round(render.probe_duration(out / "video.mp4"), 1),
        "visuals": len(visuals), "photos": n_photos, "cards": len(visuals) - n_photos,
        "seconds_per_visual": round(total / max(len(visuals), 1), 2),
        "photo_log": {k: v for k, v in photo_log.items() if k != "candidates"},
    })
    package.write(out, script, the_plan, sources, visuals, scenes, report, bench.info)
    package.contact_sheet([Path(v["frame"]) for v in visuals], out / "contact_sheet.jpg")

    # 14. Quality gate (Phase 3): technical + editorial checks; results lead the review sheet
    with bench.stage("gate"):
        result = gate.run(out, ROOT / "library", use_ai=True, media=True, script=script)
        review = (out / "review.md").read_text(encoding="utf-8")
        (out / "review.md").write_text(gate.markdown(result) + "\n" + review, encoding="utf-8")
        bench.info["gate"] = {"verdict": result["verdict"],
                              "not_pass": {c["check"]: c["status"] for c in result["checks"] if c["status"] != "PASS"}}
        print(f"[gate] {result['verdict']}: {bench.info['gate']['not_pass']}", flush=True)
    print(json.dumps({k: bench.info[k] for k in ("title", "words", "video_seconds", "visuals", "photos", "cards",
                                                 "seconds_per_visual")}, indent=2), flush=True)


if __name__ == "__main__":
    main()

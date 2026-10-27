"""Phase 3: test the quality gate on planted faults.

Blueprint "done when": planted faults (silent gap, unlicensed image, wrong title promise,
near-duplicate script) are ALL caught. Our own rule on top: a clean package gets no FAIL.

Cases are built from the approved GPS package (phase3/fixtures/gps) plus short test media
made with FFmpeg (a tone instead of a voice). Only the two AI cases spend quota (one request each);
--no-ai skips them.

    python phase3/eval_gate.py --out out/gate_eval            # needs GEMINI_API_KEY for the AI cases
    python phase3/eval_gate.py --out out/gate_eval --no-ai
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from yt_auto import gate, llm, package, render  # noqa: E402
from yt_auto.tts import split_sentences  # noqa: E402
from yt_auto.visuals import render_keyframe  # noqa: E402

FIX = ROOT / "phase3" / "fixtures"
BRIEF = {"answer": "Your phone times radio signals from at least four satellites and turns the delays into distances.",
         "evidence": "Signal travel time, the speed of light, trilateration, relativity corrections.",
         "unique_examples": "1 nanosecond = 30 cm; the fourth satellite fixes the cheap phone clock.",
         "why_watch": "Explains the clock trick most videos skip, with numbers you can picture."}


def ff(args, log: Path):
    r = subprocess.run(["ffmpeg", "-nostdin", "-y", "-hide_banner", "-loglevel", "error", *args],
                       stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=300)
    log.write_text(r.stderr)
    if r.returncode:
        raise RuntimeError(f"ffmpeg failed: {r.stderr[-500:]}")


# ---------- test media ----------

def make_media(work: Path) -> dict[str, Path]:
    """Clean 24 s video and four broken versions. Visuals: our dark title card and a bright 'photo'."""
    work.mkdir(parents=True, exist_ok=True)
    render.LOG_DIR = work
    card = work / "card.png"
    render_keyframe({"type": "title", "title": "How does GPS know where you are?", "subtitle": "test"}, card)
    photo = work / "photo.png"
    ff(["-f", "lavfi", "-i", "testsrc2=s=2304x1296", "-frames:v", "1", str(photo)], work / "photo.log")
    segs = []
    for i, img in enumerate([card, photo, card, photo, card, photo]):  # 6 x 4 s, scene fade between 3 and 4
        seg = work / f"seg{i}.mp4"
        render.make_segment(img, 4.0, seg, motion="zoom_in", fade_in=(i in (0, 3)), fade_out=(i in (2, 5)))
        segs.append(seg)
    render.concat_video(segs, work / "v_clean.mp4")
    black = work / "black.mp4"
    ff(["-f", "lavfi", "-i", "color=c=black:s=1920x1080:r=30:d=4", "-c:v", "libx264", "-pix_fmt", "yuv420p",
        str(black)], work / "black.log")
    render.concat_video(segs[:3] + [black] + segs[4:], work / "v_black.mp4")

    # "Narration": 0.6 s tone bursts with 0.4 s gaps (like speech with sentence pauses), 24 s
    speech = "sine=f=220:d=24,volume='if(lt(mod(t,1),0.6),1,0)':eval=frame"
    ff(["-f", "lavfi", "-i", speech, "-ar", "24000", str(work / "a_clean.wav")], work / "a.log")
    gap = "sine=f=220:d=24,volume='if(between(t,10,13.5),0,if(lt(mod(t,1),0.6),1,0))':eval=frame"
    ff(["-f", "lavfi", "-i", gap, "-ar", "24000", str(work / "a_gap.wav")], work / "a2.log")
    longer = "sine=f=220:d=27,volume='if(lt(mod(t,1),0.6),1,0)':eval=frame"
    ff(["-f", "lavfi", "-i", longer, "-ar", "24000", str(work / "a_long.wav")], work / "a3.log")

    out = {}
    render.mux(work / "v_clean.mp4", work / "a_clean.wav", work / "clean.mp4")
    out["clean"] = work / "clean.mp4"
    render.mux(work / "v_clean.mp4", work / "a_gap.wav", work / "silent_gap.mp4")
    out["silent_gap"] = work / "silent_gap.mp4"
    render.mux(work / "v_black.mp4", work / "a_clean.wav", work / "black_frames.mp4")
    out["black_frames"] = work / "black_frames.mp4"
    # audio 3 s longer than the video (no -shortest)
    ff(["-i", str(work / "v_clean.mp4"), "-i", str(work / "a_long.wav"), "-map", "0:v", "-map", "1:a", "-c:v", "copy",
        "-af", "loudnorm=I=-16:TP=-1.5:LRA=11", "-c:a", "aac", "-ar", "48000", str(work / "length.mp4")],
       work / "len.log")
    out["length_mismatch"] = work / "length.mp4"
    ff(["-i", str(work / "v_clean.mp4"), "-i", str(work / "a_clean.wav"), "-map", "0:v", "-map", "1:a", "-c:v", "copy",
        "-af", "volume=-30dB", "-c:a", "aac", "-ar", "48000", "-shortest", str(work / "quiet.mp4")], work / "q.log")
    out["too_quiet"] = work / "quiet.mp4"
    return out


# ---------- packages ----------

def base_pkg(dst: Path, with_brief: bool = True) -> Path:
    shutil.rmtree(dst, ignore_errors=True)
    shutil.copytree(FIX / "gps", dst)
    plan = json.loads((dst / "plan.json").read_text())
    if with_brief:
        plan.update(BRIEF)
    (dst / "plan.json").write_text(json.dumps(plan, indent=1))
    # Rebuild the description's credits the current way (the approved video's own description was
    # 9,850 characters, over YouTube's 5,000: that original is kept as a planted fault below).
    old = (dst / "description.txt").read_text(encoding="utf-8")
    head, tail = old.split("Image credits:")[0], old.split("NASA images are used")[1]
    photos = [v["photo"] for v in json.loads((dst / "visuals.json").read_text()) if v.get("photo")]
    new = head + "Image credits:\n" + "\n".join(package.credit_lines(photos)["short"]) + "\n\nNASA images are used" + tail
    (dst / "description.txt").write_text(new, encoding="utf-8")
    return dst


def edit(pkg: Path, name: str, fn):
    p = pkg / name
    data = json.loads(p.read_text(encoding="utf-8")) if name.endswith(".json") else p.read_text(encoding="utf-8")
    data = fn(data)
    p.write_text(json.dumps(data, indent=1, ensure_ascii=False) if name.endswith(".json") else data, encoding="utf-8")


def drop_first_photo_record(lic):
    photos = [r for r in lic if r.get("kind") == "photo"]
    return [r for r in lic if r is not photos[0]]


def make_nc(lic):
    for r in lic:
        if r.get("kind") == "photo" and r.get("source") == "wikimedia_commons":
            r["licence"] = "CC BY-NC 4.0"
            break
    return lic


def unsupported_fact(script):
    for sc in script["scenes"]:
        for s in sc["sentences"]:
            if s["kind"] == "fact":
                s["check"] = "unsupported"
                return script


def drop_scene_visuals(vis):
    last = vis[-1]["scene"]
    return [v for v in vis if v["scene"] != last]


def phase0_as_script():
    p0 = json.loads((ROOT / "phase0" / "sample_script.json").read_text())
    return {"title": p0["title"], "scenes": [
        {"id": s["id"], "heading": s["id"], "sentences": [
            {"id": f"{s['id']}.{i}", "text": t, "kind": "framing", "sources": []}
            for i, t in enumerate(split_sentences(s["narration"]))]} for s in p0["scenes"]]}


def library(work: Path, scripts: dict[str, dict]) -> Path:
    lib = work / "library"
    shutil.rmtree(lib, ignore_errors=True)
    lib.mkdir(parents=True)
    for name, s in scripts.items():
        (lib / f"{name}.json").write_text(json.dumps({"script": s}, ensure_ascii=False))
    return lib


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--no-ai", action="store_true")
    args = ap.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    llm.LOG_DIR = out / "llm"

    gps = json.loads((FIX / "gps" / "script.json").read_text())
    orbit = json.loads((FIX / "other" / "orbit_script.json").read_text())
    micro = json.loads((FIX / "other" / "microwave_script.json").read_text())
    lib_gps = library(out / "lib1", {"2026-10-27-gps": gps})
    lib_other = library(out / "lib2", {"orbit": orbit, "microwave": micro})
    media = make_media(out / "media")

    # (case, expected FAIL checks, how to build, run options). expected [] = control: no FAIL allowed.
    cases = []

    def media_case(name, expect, video_key):
        pkg = base_pkg(out / "cases" / name)
        shutil.copy(media[video_key], pkg / "video.mp4")
        (pkg / "frames").mkdir()
        for v in json.loads((pkg / "visuals.json").read_text()):
            (pkg / "frames" / f"{v['id']}.png").write_bytes(b"")
        cases.append((name, expect, pkg, {"library_dir": lib_other, "media": True, "use_ai": False}))

    # blueprint faults
    media_case("silent_gap", ["audio_silence"], "silent_gap")
    pkg = base_pkg(out / "cases" / "unlicensed_image")
    edit(pkg, "licences.json", drop_first_photo_record)
    cases.append(("unlicensed_image", ["rights"], pkg, {"library_dir": lib_other, "media": False, "use_ai": False}))
    for name, script in [("near_duplicate_template", json.loads((FIX / "dup_template_script.json").read_text())),
                         ("near_duplicate_shuffled", json.loads((FIX / "dup_shuffled_script.json").read_text())),
                         ("near_duplicate_same_topic", phase0_as_script())]:
        pkg = base_pkg(out / "cases" / name)
        sc = script
        if name == "near_duplicate_same_topic":  # keep facts linked so only originality is under test
            sc = json.loads(json.dumps(gps))
            sc["title"] = script["title"] + " (rewrite)"
            sc["scenes"] = script["scenes"]
        (pkg / "script.json").write_text(json.dumps(sc, indent=1, ensure_ascii=False))
        cases.append((name, ["originality"], pkg, {"library_dir": lib_gps, "media": False, "use_ai": False}))
    # extra faults
    media_case("black_frames", ["video_black"], "black_frames")
    media_case("length_mismatch", ["av_length"], "length_mismatch")
    media_case("too_quiet", ["audio_loudness"], "too_quiet")
    for name, expect, fname, fn in [
        ("nc_licence", ["rights"], "licences.json", make_nc),
        ("title_too_long", ["metadata"], "script.json", lambda s: {**s, "title": "How GPS Works " * 10}),
        ("title_angle_brackets", ["metadata"], "script.json", lambda s: {**s, "title": "GPS <explained>"}),
        ("no_sources_in_description", ["metadata"], "description.txt", lambda d: d.split("Sources")[0]),
        ("description_too_long_real", ["metadata"], "description.txt",
         lambda d: (FIX / "gps" / "description.txt").read_text(encoding="utf-8")),
        ("unsupported_fact", ["facts_linked"], "script.json", unsupported_fact),
        ("missing_scene", ["scenes_complete"], "visuals.json", drop_scene_visuals),
    ]:
        pkg = base_pkg(out / "cases" / name)
        edit(pkg, fname, fn)
        cases.append((name, expect, pkg, {"library_dir": lib_other, "media": False, "use_ai": False}))
    pkg = base_pkg(out / "cases" / "no_brief", with_brief=False)
    cases.append(("no_brief", ["editorial_brief"], pkg, {"library_dir": lib_other, "media": False, "use_ai": False}))

    # controls: must get no FAIL
    media_case("clean_media", [], "clean")
    pkg = base_pkg(out / "cases" / "clean_files")
    cases.append(("clean_files", [], pkg, {"library_dir": lib_other, "media": False, "use_ai": False}))
    for name, script in [("different_topic_orbit", orbit), ("different_topic_microwave", micro)]:
        pkg = base_pkg(out / "cases" / name)
        (pkg / "script.json").write_text(json.dumps(script, indent=1))
        # only originality matters here; other checks see a script that doesn't match the GPS files
        cases.append((name, [], pkg, {"library_dir": lib_gps, "media": False, "use_ai": False, "only": "originality"}))

    # AI cases (one request each)
    if not args.no_ai:
        pkg = base_pkg(out / "cases" / "wrong_title_promise")
        edit(pkg, "script.json", lambda s: {**s, "title": "How GPS Secretly Tracks Everything You Do"})
        cases.append(("wrong_title_promise", ["title_promise"], pkg, {"library_dir": lib_other, "media": False,
                                                                     "use_ai": True}))
        pkg = base_pkg(out / "cases" / "clean_ai")
        cases.append(("clean_ai", [], pkg, {"library_dir": lib_other, "media": False, "use_ai": True}))

    rows = []
    for name, expect, pkg, opt in cases:
        only = opt.pop("only", None)
        res = gate.run(pkg, **opt)
        checks = [c for c in res["checks"] if not only or c["check"] == only]
        fails = sorted(c["check"] for c in checks if c["status"] == gate.FAIL)
        flags = sorted(c["check"] for c in checks if c["status"] == gate.FLAG)
        if expect:
            ok = all(e in fails for e in expect)
            extra = [f for f in fails if f not in expect]
        else:
            ok, extra = not fails, fails
        rows.append({"case": name, "expect": expect, "fails": fails, "flags": flags, "ok": ok, "extra_fails": extra,
                     "details": {c["check"]: c["detail"] for c in checks if c["status"] != gate.PASS}})

    faults = [r for r in rows if r["expect"]]
    controls = [r for r in rows if not r["expect"]]
    blueprint = ["silent_gap", "unlicensed_image", "wrong_title_promise", "near_duplicate_template",
                 "near_duplicate_shuffled", "near_duplicate_same_topic"]
    bp = [r for r in rows if r["case"] in blueprint]
    passed = all(r["ok"] for r in bp) and all(r["ok"] for r in controls) and \
        (args.no_ai or any(r["case"] == "wrong_title_promise" for r in bp))
    summary = {"pass": passed, "faults_caught": f"{sum(r['ok'] for r in faults)}/{len(faults)}",
               "blueprint_faults_caught": f"{sum(r['ok'] for r in bp)}/{len(bp)}",
               "controls_clean": f"{sum(r['ok'] for r in controls)}/{len(controls)}", "ai_skipped": args.no_ai,
               "llm_calls": llm.LOG}
    (out / "results.json").write_text(json.dumps({"summary": summary, "cases": rows}, indent=1, ensure_ascii=False))

    md = ["# Quality gate test (Phase 3)", "",
          "Done when: every planted fault from the blueprint is caught (silent gap, unlicensed image, wrong title "
          "promise, near-duplicate script) and clean packages get no FAIL.", "",
          f"**Result: {'PASS' if passed else 'FAIL'}** · blueprint faults {summary['blueprint_faults_caught']} · "
          f"all faults {summary['faults_caught']} · clean controls {summary['controls_clean']}"
          + (" · AI cases skipped" if args.no_ai else ""), "",
          "| Case | Expected FAIL | Got FAIL | FLAG | OK |", "| --- | --- | --- | --- | --- |"]
    for r in rows:
        md.append(f"| {r['case']} | {', '.join(r['expect']) or '(none: control)'} | {', '.join(r['fails']) or '-'} | "
                  f"{', '.join(r['flags']) or '-'} | {'✅' if r['ok'] else '❌'} |")
    md += ["", "## Details of non-PASS checks", ""]
    for r in rows:
        for k, v in r["details"].items():
            md.append(f"- `{r['case']}` {k}: {v[:220]}")
    (out / "report.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print("\n".join(md[:8 + len(rows)]))


if __name__ == "__main__":
    main()

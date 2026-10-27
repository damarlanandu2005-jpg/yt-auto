# Your recordings (Phase 5 own-voice videos)

1. Claude runs step 1 and tells you the folder name, e.g. `voice/v2-cosmic-web/`.
2. Read `recording_script.md` for that video (link from Claude) and record on your phone:
   one file per scene named `s01`, `s02`, ... (m4a, mp3 or wav are all fine), or one file for the whole video.
3. On GitHub: open this repo → **Add file → Upload files** → type the folder name before the file names
   (e.g. `voice/v2-cosmic-web/`) → drag the files in → **Commit changes**.
4. Tell Claude "uploaded". Step 2 builds the video around your voice.

The pipeline removes low rumble, light background noise, long pauses (over 1 second) and silence at the
start and end of each file. It then checks that you read every sentence: skipped or changed sentences fail
the quality gate, because each sentence was fact-checked as written.

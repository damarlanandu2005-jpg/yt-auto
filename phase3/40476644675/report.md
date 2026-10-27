# Quality gate test (Phase 3)

Done when: every planted fault from the blueprint is caught (silent gap, unlicensed image, wrong title promise, near-duplicate script) and clean packages get no FAIL.

**Result: FAIL** · blueprint faults 6/6 · all faults 17/17 · clean controls 4/5

| Case | Expected FAIL | Got FAIL | FLAG | OK |
| --- | --- | --- | --- | --- |
| silent_gap | audio_silence | audio_silence | video_minutes | ✅ |
| unlicensed_image | rights | rights | - | ✅ |
| near_duplicate_template | originality | originality | - | ✅ |
| near_duplicate_shuffled | originality | originality | - | ✅ |
| near_duplicate_same_topic | originality | originality, scenes_complete | - | ✅ |
| black_frames | video_black | video_black | video_minutes | ✅ |
| length_mismatch | av_length | av_length | video_minutes | ✅ |
| too_quiet | audio_loudness | audio_loudness | video_minutes | ✅ |
| nc_licence | rights | rights | - | ✅ |
| title_too_long | metadata | metadata | - | ✅ |
| title_angle_brackets | metadata | metadata | - | ✅ |
| no_sources_in_description | metadata | metadata | - | ✅ |
| description_too_long_real | metadata | metadata | - | ✅ |
| unsupported_fact | facts_linked | facts_linked | - | ✅ |
| missing_scene | scenes_complete | scenes_complete | - | ✅ |
| no_brief | editorial_brief | editorial_brief | - | ✅ |
| clean_media | (none: control) | - | video_minutes | ✅ |
| clean_files | (none: control) | - | - | ✅ |
| different_topic_orbit | (none: control) | - | - | ✅ |
| different_topic_microwave | (none: control) | - | - | ✅ |
| wrong_title_promise | title_promise | hook, title_promise | - | ✅ |
| clean_ai | (none: control) | hook | - | ❌ |

## Details of non-PASS checks

- `silent_gap` audio_silence: silent gaps over 2 s at [(9.6, 13.5)]
- `silent_gap` video_minutes: 0.4 min (target 5-8)
- `unlicensed_image` rights: v004: picture v004.jpg has no licence record
- `near_duplicate_template` originality: same topic as 2026-10-27-gps (word similarity 0.64 ≥ 0.45); 100% of sentences follow 2026-10-27-gps with only numbers/words changed; 54% of 5-word phrases copied from 2026-10-27-gps
- `near_duplicate_shuffled` originality: same topic as 2026-10-27-gps (word similarity 0.62 ≥ 0.45); 100% of sentences follow 2026-10-27-gps with only numbers/words changed; 46% of 5-word phrases copied from 2026-10-27-gps
- `near_duplicate_same_topic` scenes_complete: scenes with no visuals: ['s01_hook', 's02_constellation', 's03_signal', 's04_time_to_distance', 's05_one_sphere', 's06_intersection', 's07_clock_problem', 's08_fourth_satellite', 's09_atomic_clocks', 's10_relativity', 's
- `near_duplicate_same_topic` originality: same topic as 2026-10-27-gps (word similarity 0.57 ≥ 0.45)
- `black_frames` video_black: black frames at [(12.0, 16.0)]
- `black_frames` video_minutes: 0.4 min (target 5-8)
- `length_mismatch` av_length: audio 27.0 s, video 24.0 s (differ by 3.0 s)
- `length_mismatch` video_minutes: 0.4 min (target 5-8)
- `too_quiet` audio_loudness: -53.8 LUFS (target -16 ± 2), true peak -47.2 dBTP
- `too_quiet` video_minutes: 0.4 min (target 5-8)
- `nc_licence` rights: v004: licence 'CC BY-NC 4.0' is not allowed
- `title_too_long` metadata: title is 140 characters (1-100 allowed)
- `title_angle_brackets` metadata: title contains < or >, which YouTube rejects
- `no_sources_in_description` metadata: description lists no sources
- `description_too_long_real` metadata: description is 9850 characters (max 5000)
- `unsupported_fact` facts_linked: unlinked or unsupported: ["s01.03 (unsupported, sources ['A1.1'])"]
- `missing_scene` scenes_complete: scenes with no visuals: ['s06']; visuals with no frame: []
- `no_brief` editorial_brief: brief is missing ['answer', 'evidence', 'unique_examples', 'why_watch']
- `clean_media` video_minutes: 0.4 min (target 5-8)
- `wrong_title_promise` hook: The first 30 seconds state the viewer's question but do not explain why it matters, jumping immediately into technical background facts about satellite ownership and orbital planes.
- `wrong_title_promise` title_promise: The title claims to show how GPS secretly tracks everything you do, but the script explicitly states that GPS is a passive broadcast network that does not track you or receive signals from your phone.
- `clean_ai` hook: The first 30 seconds present the core question about how a smartphone pinpoints location, but fail to explain why this capability matters to the viewer.

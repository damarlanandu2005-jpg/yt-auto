# Stickman Thoughts: the video template (frozen 29 Oct 2026, owner approved)

Reference video: release `cartoon-40827775250` ("What happens if you fall into a black hole?").
Every new Short follows these rules. Only the story, the scenes and the props change from video to video
(YouTube's inauthentic-content rule and our rule R3: never the same video with new numbers).

## 1. Format

| Item | Rule |
| --- | --- |
| Size | 1080 x 1920, plain `9:16` (no safe-area margins: the scene fills the whole screen) |
| Length | 40-60 seconds, about 110-140 spoken words |
| Language | English (Telugu and Hindi later, on their own channels) |
| Watermark | none (`"watermark": false`) |

## 2. Story (rule R2: honest emotion)

1. **Hook** (1 sentence): the big "what if...?" question, true, with a strong feeling (fear, shock, wonder, sadness).
2. **4-5 steps**, one idea each, 1-3 short sentences per step. The stickman lives through each step.
3. **The answer**: the hook is answered inside the video, never "watch part 2".
4. **Last line**: one plain sentence that sums it up.

No fake urgency ("scientists are terrified") unless a source says it. No health, money or legal advice,
no accusations against named companies or people, no tragedies from the last 12 months.

## 3. Facts

- Every spoken fact has a source note under its scene in `script.md` (`> source: article, revision id, quote`).
- Sources are saved first (Wikipedia via `fetch-pages.yml` or `research.py`), never written from memory.
- The description lists every source with its revision link.

## 4. Character and drawings

- ONE recurring stickman (`cartoon/character.js`): 12 poses, 9 faces, smooth changes, blink, breathing.
  He shows the feeling of each step (scared when falling, shocked at the twist, sad at the end...).
- On dark scenes he gets a white sticker edge (`outline: '#ffffff'`); never use canvas `filter` (too slow).
- Props are simple flat drawings in code (`cartoon/props.js`). Each topic adds its own props.
- One idea per picture; something new every 2-4 seconds; pictures change on the spoken word.

## 5. Layout (9:16 frame)

| Zone | y range (px) | Use |
| --- | --- | --- |
| Pictures | 150-1300 | character, props, labels |
| Caption | about 1380 (72 %) | one word at a time |
| YouTube buttons | below 1450, and right of x = 930 | nothing important here |

## 6. Captions

- Our own one-word captions (`words(s)` in `props.js`): bold white, black edge, no box, pop in on the word.
- Numbers in yellow. explainroo's own captions are off (`"captions": false`).

## 7. Sound

- Voice: Kokoro `af_heart` (text-to-speech). The description says "Voice: text-to-speech".
- Music and click/whoosh sounds: made by explainroo itself. Final loudness about -14 LUFS.

## 8. Look

- Space topics: `cartoon/space-look.json` (dark navy, stars).
- Other topics need their own backgrounds (ocean, land, city, sky, inside the body, history). To build.

## 9. Checks before "ready for review"

- explainroo `check`: 0 errors (nothing cut off or overlapping).
- Voice check: every word understood.
- Every source note present; the hook is answered (R2).
- Release title: "Ready for your review" only if all pass, otherwise "DRAFT - do not upload" (R1).

## 10. Upload package

Title (the hook question), description (2 lines + sources + "Voice: text-to-speech" + hashtags),
not made for kids, altered/synthetic content: No, category Education, first Private/Unlisted.

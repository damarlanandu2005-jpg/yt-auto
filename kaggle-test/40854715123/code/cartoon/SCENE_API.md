# Scene writing rules (given to the AI scene writer)

You write `scenes.js` for one YouTube Short in the "Stickman Thoughts" style (see TEMPLATE.md).
explainroo calls each scene function for every frame with a fresh `s`; everything must depend only on time.
Never keep state, never use timers, never use `Math.random()` (use `s.rand(i)`), never import anything except
`./character.js` and `./props.js`, never use `fetch`, `eval`, `document`, `window` or `ctx.filter`.

```js
import { hero } from './character.js';
import { background, thing, label, words, blackHole } from './props.js';
export default {
  sceneId(s) { background(s, 'ocean'); /* ...pictures... */ words(s); },  // one function per "## sceneId"
};
```

Every scene: FIRST `background(s, kind)`, LAST `words(s)` (the one-word captions).

## Frame (1080 x 1920, the whole screen is the picture)

- Pictures between y = 150 and y = 1300. Captions sit at y ~ 1380: put nothing important at y 1330-1440.
- YouTube's buttons cover x > 930 and y > 1450: nothing important there.
- On ground backgrounds (land, city, desert, snow, room) the ground line is at y ~ 1300: feet go at y 1300.
- Keep every label fully inside x 90-990.

## Timing

`at` and `out` take seconds (`1.2`), a spoken word of THIS scene (`'ocean'`, exact word, any case), or a marker
(`'#name'`, written as `[#name]` in script.md). A word that is not spoken in the scene is an error.
`at: -1` = already there from the start (for things carried over from the previous scene).
`s.p(at, dur)` gives 0..1 progress for your own motion; `s.t` = seconds since the scene started.
Something new should appear every 2-4 seconds, on the word it belongs to.

## The character (one stickman, the same in every video)

```js
hero(s, { x: 540, y: 1300, scale: 1.4, outline: '#ffffff', at: 0,
  moves: [{ at: 0, pose: 'stand', face: 'happy' }, { at: 'deep', pose: 'scared', face: 'scared' }] });
```

- poses: stand, wave, point, shrug, scared, think, cheer, fall, float, run, sit, sad
- faces: neutral, happy, wow, scared, shocked, confused, thinking, sad, angry
- options: x, y (feet), scale (0.4 small ... 1.9 big; his height is about 340 x scale px), flip (face left),
  helmet (space suit), float (gentle drift), outline (ALWAYS '#ffffff'), at, out,
  stretch (1 normal ... 2.2; number or `() => ...`), alpha (0..1), color (line colour).
- He shows the FEELING of each step. Usually one stickman; a second one (a friend) only when the story needs it.

## Props, labels, captions (from props.js)

- `background(s, kind)`: space, night, ocean, deep, sky, land, city, body, desert, snow, fire, room.
- `thing(s, name, { x, y, size, at, out, rotate })`: sun, earth, moon, ship, wave, mountain, volcano, tree, house,
  fire, drop, heart, brain, clock, rock, fish, rocket, question. `size` = width in px (60-400).
- `blackHole(s, { x, y, r, at })`.
- `label(s, 'SHORT TEXT', { x, y, size, color, at, out })`: bold text with a black edge, readable on any
  background. color: yellow, red, green, blue or white. Max 3-4 words. Never repeat the narration sentence.
- `words(s)`: the captions. Call it last in EVERY scene.

## explainroo shapes you may also use

- `s.arrow([x1, y1], [x2, y2], { color: 'red', width: 12, label: 'text', labelSize: 50, bend: 0.3, dashed, at })`
- `s.circle({ x, y, r, fill, color, at })`, `s.box('text', { x, y, w, h, color, at })`
- `s.path('M0 0 L100 0', { x, y, color, width, fill, at })`, `s.line([[x1, y1], [x2, y2]], { color, width, at })`
- `s.number(1500, { x, y, size, suffix: ' metres', at })` counts up with ticks. Only numbers from the script.
- `s.icon(name, { x, y, size, color, at })`: Lucide icons (e.g. 'skull', 'anchor', 'thermometer', 'wind',
  'zap', 'clock', 'eye', 'shield', 'snowflake', 'waves', 'mountain', 'bug', 'bird', 'dog', 'fish', 'heart-pulse').
- `s.draw({ x, y, at }, (ctx) => { ... })` for a small custom drawing with the canvas (thick black outline,
  flat colours, like the props). No `ctx.filter`, no images.

## Show, don't write (the most important rule)

- The story is told by DRAWINGS and the stickman's feelings, not by text. The voice and the captions already
  say every word.
- At most ONE `label` per scene, at most 4 words, and ONLY words the voice says in that scene (checked in code:
  a label that says "crushed" when the voice says "injure" is rejected). No `s.text`, `s.note`, `s.title`, `s.list`.
- Every scene shows the stickman (`hero`, scale 0.9-1.8) AND a drawing of what the voice talks about:
  `thing(...)`, `blackHole(...)`, an icon, arrows, or your own simple `s.draw` drawing (a lung, a trench, a
  wave, a body outline: flat colours and a thick black outline, like the props).

## Good pictures

- One idea per picture. The picture shows what the voice says at that moment.
- Big and simple: the main thing at least 300 px. The stickman at scale 1.0-1.8 most of the time.
- Every scene looks different from the one before (new background, distance, prop or pose).
- Honest: never draw something the narration doesn't say. Numbers on screen only if they are in the script.

## Mistakes seen in test videos (do not repeat)

- Text on top of the stickman: a label must never cross his body or head. He fills a box of about
  (x - 110*scale ... x + 110*scale) by (y - 340*scale ... y). Put labels above that box or beside it.
- Counting numbers that make no sense ("172x pressure"): use `s.number` only for a plain quantity spoken in the
  scene (depth, years, degrees), never for "x times" or percentages; write those with `label`.
- Abbreviations on screen ("ATM/10m", "km"): write words ("1 MORE ATMOSPHERE", "EVERY 10 METRES").
- The background must follow the story: deeper or darker as the story goes deeper, never jump back.
- Every scene's main picture must be different from the last: change the background, the distance (scale),
  the prop or the pose. Do not draw the same stickman in the same spot scene after scene.
- explainroo arrow labels are light grey text: on light backgrounds (sky, land, desert, snow, room) use
  `label()` next to the arrow instead of the arrow's own `label`.

# Scene writing rules (given to the AI scene writer)

You write `scenes.js` for one YouTube Short in the "Stickman Thoughts" style (see TEMPLATE.md).
explainroo calls each scene function for every frame with a fresh `s`; everything must depend only on time.
Never keep state, never use timers, never use `Math.random()` (use `s.rand(i)`), never import anything except
`./character.js` and `./props.js`, never use `fetch`, `eval`, `document`, `window` or `ctx.filter`.

```js
import { hero, crowd } from './character.js';
import { place, stand, art, fire, smoke, lava, bubbles, waterRise, weather, explosion, pieces, glow, speedLines,
  background, thing, emoji, label, words, blackHole } from './props.js';
export default {
  sceneId(s) { background(s, 'ocean'); /* ...pictures... */ words(s); },  // one function per "## sceneId"
};
```

Every scene: FIRST `place(s, name)` or `background(s, kind)` (it also keeps the camera still, so captions are never cut off),
LAST `words(s)` (the one-word captions). Never call `s.camera` or `s.focus` yourself.

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

## The characters (the stickman, the same in every video, plus other people)

```js
hero(s, { x: 540, y: 1300, scale: 1.4, outline: '#ffffff', at: 0,
  look: { outfit: 'passenger_1912', hat: 'bowler', hair: 'short' },
  moves: [{ at: 0, pose: 'walk', face: 'happy' }, { at: 'iceberg', pose: 'point', face: 'shocked' }] });
crowd(s, { n: 6, x0: 120, x1: 960, y: 1500, scale: 0.8, depth: 40, seed: 4, outfits: ['passenger_1912', 'dress'],
  faces: ['scared', 'shocked'], poses: ['panic', 'scared'], outline: '#ffffff', at: 'panic' });
```

- poses: stand, wave, point, shrug, scared, think, cheer, fall, float, run, sit, sad,
  moving: walk, sprint, swim, climb, jump, panic, shiver, tumble; still: kneel, crouch, lie, hold, carry, push,
  pull, look_up, look_down, cover_ears
- faces: neutral, happy, wow, scared, shocked, confused, thinking, sad, angry, worried, crying, sweating, sleepy,
  smug, determined, disgusted, laughing, pain, dizzy, cold, relieved
- look (all optional; WITHOUT look he is the plain logo stickman, which is right for space/abstract stories):
  - body: normal, thin, round, muscle, short, child, old (never make fun of a body type)
  - outfit: shirt, tshirt, suit, passenger_1912, dress, doctor, scientist, police, firefighter, astronaut, diver,
    sailor, soldier_free, farmer, cowboy, chef, worker, student, explorer, hospital_gown
  - hat: cap, police_cap, cowboy, top_hat, hard_hat, straw, chef, beanie, fire_helmet, sailor_cap, bowler, explorer
  - hair: short, long, curly, bun, spiky, bald; hairColor; glasses, moustache, beard: true
- options: x, y (feet; on a place use floorY), scale (0.4 small ... 1.9 big; his height is about 340 x scale px),
  flip (face left), helmet (space suit), float (gentle drift), outline (ALWAYS '#ffffff'), at, out,
  stretch (1 normal ... 2.2; number or `() => ...`), alpha (0..1), color (line colour).
- The main stickman shows the FEELING of each step and keeps the SAME look all video. Dress him for the story
  (a 1912 passenger on the Titanic, a diver underwater). Other people: a second hero, or crowd() for groups.

## Props, labels, captions (from props.js)

- `place(s, name, { shot, focus, mood, flash })`: a REAL PLACE from the LIBRARY list below (a detailed picture:
  Titanic deck, hospital room, volcano crater, city street...). PREFER a place over `background` whenever one fits.
  `shot`: 'wide' (the whole place, people small), 'medium' (people ~40 % of the screen: the usual shot),
  'close' (a face fills the screen, cut at the waist: for strong feelings). Change the shot often, like a film:
  wide to show where we are, then medium, then close on the feeling. `focus`: 0 = left part of the place ... 1 =
  right part. `mood`: night, dark, fire, cold, storm, dusk, underwater (lights the place AND the people).
  `flash: ['boom']` = a white flash on that word.
- `stand(s, depth)`: where a person stands in the current shot and how big they are (depth 0 = far back, 1 =
  front). ALWAYS place people on a place with it: `hero(s, { x: 300, ...stand(s, 0.8), look: {...}, moves })`,
  `crowd(s, { n: 4, x0: 500, x1: 980, ...stand(s, 0.3) })`. On a place, people get a floor shadow and no white
  edge automatically (they stand IN the room, not pasted on it).
- `art(s, name, { x, y, scale, size, at, flip, rotate })`: a detailed library object (lifeboat, bed, car, bomb
  timer...) drawn at its REAL size next to the stickman; `y` = where it stands (its bottom), `scale` = the same
  as the stickman's scale beside it. `size` (px of height) only for a close-up of the object.
- `background(s, kind)`: a plain sky only when no place fits: space, night, ocean, deep, sky, land, city, body,
  desert, snow, fire, room.
- `thing(s, name, { x, y, size, at, out, rotate })`: sun, earth, moon, ship, wave, mountain, volcano, tree, house,
  fire, drop, heart, brain, clock, rock, fish, rocket, question. `size` = width in px (60-400).
- `blackHole(s, { x, y, r, at })`.
- `emoji(s, name, { x, y, size, at, out, rotate, flip })`: a colourful cartoon drawing (Twemoji) with a white
  sticker edge, for animals and objects that `thing` does not have: 'shark', 'whale', 't_rex', 'lungs',
  'passenger_ship', 'skull', 'volcano'... ONLY names from the EMOJI NAMES list below (checked in code). `size` =
  width in px (120-500). `flip: true` turns it to face the other way. Use a `thing` when one fits, an emoji when not.
- `label(s, 'SHORT TEXT', { x, y, size, color, at, out })`: bold text with a black edge, readable on any
  background. color: yellow, red, green, blue or white. Max 3-4 words. Never repeat the narration sentence.
- `words(s)`: the captions. Call it last in EVERY scene.

## Effects (moving, from props.js): use them to make the story happen, not just to decorate

- `fire(s, { x, y, size, at, out })` flames standing on (x, y); `smoke(s, { x, y, size, dark, at })` rising puffs
- `lava(s, { y, at })` a glowing lava pool from y down; `bubbles(s, { x, y, width, n, at })` rising bubbles
- `waterRise(s, { from, to, at, until })` water filling up the screen (flooding, sinking); y values on screen
- `weather(s, { kind: 'rain' | 'snow', heavy, at })`; `place(..., { flash: ['boom'] })` lightning / blast flash
- `explosion(s, { x, y, size, at })` a cartoon blast (no gore); `pieces(s, { x, y, at, kind: 'ice' | 'rock' |
  'spark' | 'glass' })` bits flying out and falling
- `glow(s, { x, y, r, color: '255,220,140', cone, pulse, at })` a soft light, or a lamp cone pointing down
- `speedLines(s, { dir: 'down' | 'up' | 'side', at })` action lines (falling, rushing)
- `place(..., { quake: { at: 'shakes', until: 'stops' } })` the whole place shakes (earthquake, crash)
- motion on art: `art(s, 'ship_front_half', { ..., water: 1180, sink: { by: 300, tilt: -20, at: 'sinks',
  until: 'gone' }, move: { to: [x, y], at, until }, shake: { at, until } })`: `water` hides everything below
  that screen line, so a ship can go under; on people: `hero(s, { ..., move: { to: [x, y], at, until, scale } })`

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
  `thing(...)`, `emoji(...)`, `blackHole(...)`, an icon, arrows, or your own simple `s.draw` drawing (a lung, a trench, a
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

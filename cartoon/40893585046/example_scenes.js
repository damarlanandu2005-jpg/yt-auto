// STYLE EXAMPLE for the AI scene writer (follows SCENE_API.md: drawings tell the story, at most one label
// of spoken words per scene, cues are spoken words). Narration of this example:
//   hook:   "Imagine you fall into a black hole, feet first. What would you feel?"
//   step1:  "Gravity pulls much harder on your feet than on your head. So your body is stretched long and thin."
//   step2:  "Scientists call this spaghettification."
//   step3:  "A small black hole stretches you apart before you even reach its edge."
//   answer: "A giant one lets you cross the edge without feeling much at all."
//   end:    "Once you cross the edge, nothing, not even light, can escape."
import { hero } from './character.js';
import { background, blackHole, label, thing, words } from './props.js';

export default {
  hook(s) {
    background(s, 'space');
    blackHole(s, { x: 540, y: 1080, r: 190, at: 0, enter: 'none' });
    hero(s, { x: 540, y: 780, scale: 1.7, helmet: true, float: true, outline: '#ffffff', at: 0, enter: 'none',
      moves: [{ at: 0, pose: 'float', face: 'happy' }, { at: 'feet', pose: 'fall', face: 'scared' },
        { at: 'feel', pose: 'shrug', face: 'confused' }] });
    words(s);
  },

  step1(s) {
    background(s, 'space');
    blackHole(s, { x: 540, y: 1230, r: 120, at: -1 });
    hero(s, { x: 540, y: 1100, scale: 1.3, helmet: true, outline: '#ffffff', at: -1,
      stretch: () => 1 + 1.0 * s.p(s.cue('stretched'), 2.2),
      moves: [{ at: 0, pose: 'fall', face: 'scared' }, { at: 'thin', pose: 'fall', face: 'shocked' }] });
    s.arrow([340, 780], [340, 1100], { color: 'red', width: 16, at: 'feet' });   // strong pull on the feet
    s.arrow([340, 250], [340, 330], { color: 'muted', width: 8, at: 'head' });   // weak pull on the head
    label(s, 'STRETCHED', { x: 760, y: 300, size: 80, color: 'yellow', at: 'stretched' });
    words(s);
  },

  step2(s) {
    background(s, 'space');
    hero(s, { x: 540, y: 1250, scale: 1.0, helmet: true, outline: '#ffffff', at: -1, stretch: 2.0,
      moves: [{ at: 0, pose: 'fall', face: 'shocked' }] });
    s.icon('utensils', { x: 540, y: 500, size: 170, color: 'orange', at: 'spaghettification' });
    label(s, 'SPAGHETTIFICATION', { y: 300, size: 96, color: 'yellow', at: 'spaghettification' });
    words(s);
  },

  step3(s) {
    background(s, 'space');
    blackHole(s, { x: 720, y: 700, r: 110, at: 0.2 });
    hero(s, { x: 330, y: 900, scale: 0.9, helmet: true, outline: '#ffffff', at: 'small',
      stretch: () => 1 + 1.2 * s.p(s.cue('apart'), 2.0), moves: [{ at: 0, pose: 'fall', face: 'scared' }] });
    label(s, 'SMALL', { x: 720, y: 450, size: 80, color: 'red', at: 'small' });
    words(s);
  },

  answer(s) {
    background(s, 'space');
    blackHole(s, { x: 540, y: 1000, r: 300, at: 0 });
    hero(s, { x: 540, y: 900, scale: 1.1, helmet: true, float: true, outline: '#ffffff', at: 'cross',
      moves: [{ at: 0, pose: 'float', face: 'happy' }] });
    label(s, 'GIANT', { y: 330, size: 96, color: 'green', at: 'giant' });
    words(s);
  },

  end(s) {
    background(s, 'space');
    blackHole(s, { x: 540, y: 860, r: 320, at: 0 });
    hero(s, { x: 540, y: 990, scale: 0.95, helmet: true, color: '#ffffff', at: 0.3,
      moves: [{ at: 0, pose: 'scared', face: 'scared' }, { at: 'light', pose: 'sad', face: 'sad' }] });
    for (let i = 0; i < 3; i++) { // light tries to get out and bends back in
      const a = -0.9 + i * 0.9;
      s.arrow([540 + 60 * a, 700], [540 + 260 * a, 600], { bend: 1.2, color: 'yellow', dashed: true, width: 8, at: s.cue('light') + 0.2 * i });
    }
    label(s, 'NOT EVEN LIGHT', { y: 260, size: 90, color: 'red', at: 'light' });
    words(s);
  },
};

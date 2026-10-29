// STYLE EXAMPLE 2 for the AI scene writer: a story in REAL PLACES from the library, with shots that change every
// ~2 seconds (cut), people standing IN the place (stand), a costume kept the same all video, crowds and effects.
// Use this style for every Earth story (places, history, disasters, the body); use example 1 (space) for space.
// Narration of this example (an example only, not a real Short):
//   hook:   "What if you were standing on a volcano when it erupted?"
//   step1:  "The ground starts to shake, and smoke pours out of the crater."
//   step2:  "Then hot ash and rocks fly into the sky, and everyone runs."
//   answer: "The real danger is the fast cloud of hot gas and ash, which can race down the slope."
//   end:    "Would you still climb to the top?"
import { hero, crowd } from './character.js';
import { place, stand, cut, smoke, lava, pieces, explosion, speedLines, glow, words } from './props.js';

const ME = { outfit: 'explorer', hat: 'explorer', hair: 'short' };  // the same look in every shot

export default {
  hook(s) {
    const k = cut(s, ['volcano', 'erupted']);
    if (k === 0) {  // wide: where we are
      place(s, 'volcano_crater', { shot: 'wide' });
      hero(s, { x: 360, ...stand(s, 0.75), look: ME, at: 0, moves: [{ at: 0, pose: 'walk', face: 'happy' }] });
    } else if (k === 1) {  // medium: he is right at the edge
      place(s, 'volcano_crater', { shot: 'medium', focus: 0.4 });
      smoke(s, { x: 700, y: 760, size: 150, dark: true });
      hero(s, { x: 420, ...stand(s, 0.8), look: ME, at: 0, moves: [{ at: 0, pose: 'look_down', face: 'wow' }] });
    } else {  // close: the feeling
      place(s, 'volcano_crater', { shot: 'close', focus: 0.4, mood: 'fire' });
      hero(s, { x: 500, ...stand(s, 0.8), look: ME, at: 0, moves: [{ at: 0, pose: 'scared', face: 'shocked' }] });
    }
    words(s);
  },

  step1(s) {
    const k = cut(s, ['smoke']);
    if (k === 0) {
      place(s, 'volcano_crater', { shot: 'medium', quake: { at: 'shake', until: 'smoke' } });
      hero(s, { x: 400, ...stand(s, 0.8), look: ME, at: 0, moves: [{ at: 0, pose: 'shiver', face: 'worried' }] });
    } else {
      place(s, 'volcano_crater', { shot: 'wide', mood: 'fire' });
      smoke(s, { x: 540, y: 820, size: 260, dark: true, at: 'smoke' });
      glow(s, { x: 540, y: 900, r: 420, color: '255,140,40', pulse: true });
      hero(s, { x: 300, ...stand(s, 0.7), look: ME, at: 0, moves: [{ at: 0, pose: 'point', face: 'scared' }] });
    }
    words(s);
  },

  step2(s) {
    const k = cut(s, ['runs']);
    if (k === 0) {
      place(s, 'volcano_crater', { shot: 'wide', mood: 'fire', flash: ['rocks'] });
      explosion(s, { x: 540, y: 700, size: 260, at: 'ash' });
      pieces(s, { x: 540, y: 700, at: 'rocks', kind: 'rock', n: 18, spread: 420 });
      hero(s, { x: 300, ...stand(s, 0.8), look: ME, at: 0, moves: [{ at: 0, pose: 'cover_ears', face: 'shocked' }] });
    } else {  // everyone runs: a crowd and our stickman sprinting out of the frame
      place(s, 'volcano_crater', { shot: 'medium', mood: 'fire' });
      crowd(s, { n: 4, x0: 560, x1: 980, ...stand(s, 0.35), seed: 11, outfits: ['explorer', 'tshirt', 'worker'],
        faces: ['scared', 'shocked'], poses: ['sprint'] });
      hero(s, { x: 360, ...stand(s, 0.85), look: ME, at: 0, move: { to: [-200], at: 'runs' },
        moves: [{ at: 0, pose: 'sprint', face: 'scared' }] });
      speedLines(s, { dir: 'side', at: 'runs' });
    }
    words(s);
  },

  answer(s) {
    const k = cut(s, ['race']);
    if (k === 0) {
      place(s, 'volcano_crater', { shot: 'wide', mood: 'dark' });
      smoke(s, { x: 540, y: 1100, size: 340, dark: true });
      lava(s, { y: 1700 });
    } else {
      place(s, 'volcano_crater', { shot: 'close', focus: 0.5, mood: 'fire' });
      smoke(s, { x: 900, y: 1400, size: 300, dark: true });
      hero(s, { x: 460, ...stand(s, 0.8), look: ME, at: 0, moves: [{ at: 0, pose: 'panic', face: 'sweating' }] });
    }
    words(s);
  },

  end(s) {
    place(s, 'volcano_crater', { shot: 'medium', focus: 0.4 });
    hero(s, { x: 420, ...stand(s, 0.8), look: ME, at: 0, moves: [{ at: 0, pose: 'think', face: 'thinking' }] });
    words(s);
  },
};

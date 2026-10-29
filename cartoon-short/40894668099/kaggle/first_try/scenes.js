import { hero } from './character.js';
import { background, thing, label, words } from './props.js';

export default {
  hook(s) {
    background(s, 'ocean');
    thing(s, 'ship', { x: 540, y: 1300, size: 300, at: 0 });
    hero(s, { x: 540, y: 1300, scale: 1.4, at: 0, moves: [{ at: 0, pose: 'wave', face: 'happy' }] });
    thing(s, 'mountain', { x: 900, y: 400, size: 150, at: 0 });
    words(s);
  },

  step1(s) {
    background(s, 'ocean');
    thing(s, 'ship', { x: 540, y: 1300, size: 300, at: -1 });
    hero(s, { x: 540, y: 1300, scale: 1.4, at: -1, moves: [{ at: 0, pose: 'stand', face: 'neutral' }] });
    thing(s, 'mountain', { x: 900, y: 400, size: 150, at: 'iceberg' });
    words(s);
  },

  step2(s) {
    background(s, 'ocean');
    thing(s, 'ship', { x: 540, y: 1300, size: 300, at: -1 });
    thing(s, 'mountain', { x: 600, y: 900, size: 180, at: 'struck' });
    hero(s, { x: 540, y: 1250, scale: 1.4, at: -1, moves: [{ at: 0, pose: 'scared', face: 'shocked' }] });
    words(s);
  },

  step3(s) {
    background(s, 'ocean');
    thing(s, 'ship', { x: 540, y: 1350, size: 300, rotate: -0.2, at: -1 });
    hero(s, { x: 540, y: 1200, scale: 1.2, at: -1, moves: [{ at: 0, pose: 'sad', face: 'sad' }] });
    s.line([[400, 1100], [700, 1100]], { color: 'black', width: 12, at: 0 });
    label(s, 'D DECK', { x: 540, y: 1050, size: 60, color: 'white', at: 0 });
    words(s);
  }
};
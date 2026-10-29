import { hero } from './character.js';
import { background, thing, label, words, icon, arrow } from './props.js';
export default {
  hook(s) {
    background(s, 'ocean');
    hero(s, { x: 540, y: 1300, scale: 1.4, outline: '#ffffff', at: 0,
      moves: [{ at: 0, pose: 'stand', face: 'happy' }]});
    thing(s, 'wave', { x: 540, y: 1200, size: 400, at: -1 });
    words(s);
  },

  step1(s) {
    background(s, 'ocean');
    hero(s, { x: 540, y: 1100, scale: 1.4, outline: '#ffffff', at: 0,
      moves: [{ at: 0, pose: 'fall', face: 'scared' }]});
    thing(s, 'wave', { x: 540, y: 1200, size: 400, at: -1 });
    icon(s, 'thermometer', { x: 540, y: 800, size: 200, color: 'blue', at: 'cold' });
    words(s);
  },

  step2(s) {
    background(s, 'deep');
    hero(s, { x: 540, y: 900, scale: 1.4, outline: '#ffffff', at: 0,
      moves: [{ at: 0, pose: 'fall', face: 'confused' }]});
    icon(s, 'shield', { x: 540, y: 500, size: 200, color: 'red', at: 'pressure' });
    s.arrow([540, 1100], [540, 900], { color: 'blue', width: 12, at: 'pressure' });
    words(s);
  },

  step3(s) {
    background(s, 'deep');
    hero(s, { x: 540, y: 700, scale: 1.4, outline: '#ffffff', at: 0,
      moves: [{ at: 0, pose: 'fall', face: 'sad' }]});
    icon(s, 'shield', { x: 540, y: 300, size: 200, color: 'red', at: 'lungs' });
    words(s);
  },

  answer(s) {
    background(s, 'deep');
    hero(s, { x: 540, y: 1100, scale: 1.4, outline: '#ffffff', at: 0,
      moves: [{ at: 0, pose: 'stand', face: 'sad' }]});
    icon(s, 'thermometer', { x: 540, y: 800, size: 200, color: 'blue', at: 'cold' });
    icon(s, 'shield', { x: 540, y: 500, size: 200, color: 'red', at: 'injure' });
    label(s, 'INJURE', { x: 540, y: 600, size: 80, color: 'yellow', at: 'injure' });
    words(s);
  },

  end(s) {
    background(s, 'deep');
    hero(s, { x: 540, y: 1300, scale: 1.4, outline: '#ffffff', at: 0,
      moves: [{ at: 0, pose: 'stand', face: 'confused' }]});
    icon(s, 'fish', { x: 540, y: 900, size: 200, color: 'white', at: 'deeps' });
    words(s);
  },
};
import { hero } from './character.js';
import { background, thing, label, words, s } from './props.js';

export default {
  hook(s) {
    background(s, 'ocean');
    hero(s, { x: 540, y: 1300, scale: 1.4, outline: '#ffffff', at: 0, moves: [{ at: 0, pose: 'fall', face: 'scared' }] });
    thing(s, 'wave', { x: 540, y: 1300, size: 100, at: 0 });
    words(s);
  },

  step1(s) {
    background(s, 'ocean');
    hero(s, { x: 540, y: 1300, scale: 1.4, outline: '#ffffff', at: -1, moves: [{ at: 0, pose: 'fall', face: 'scared' }] });
    s.number(10935, { x: 540, y: 1380, size: 60, suffix: 'metres', at: 'depth' });
    label(s, 'COLD SHOCK', { x: 540, y: 300, size: 80, color: 'yellow', at: 'cold' });
    words(s);
  },

  step2(s) {
    background(s, 'deep');
    hero(s, { x: 540, y: 1300, scale: 1.4, outline: '#ffffff', at: -1, moves: [{ at: 0, pose: 'fall', face: 'scared' }] });
    s.arrow([540, 150], [540, 1300], { color: 'red', width: 12, label: 'PRESSURE', labelSize: 50, bend: 0.3, at: 'pressure' });
    label(s, 'DROWNING', { x: 540, y: 300, size: 80, color: 'yellow', at: 'drowning' });
    words(s);
  },

  step3(s) {
    background(s, 'deep');
    hero(s, { x: 540, y: 1300, scale: 1.4, outline: '#ffffff', at: -1, moves: [{ at: 0, pose: 'sad', face: 'sad' }] });
    s.icon('lungs', { x: 300, y: 700, size: 100, color: 'red', at: 'lungs' });
    s.icon('ear', { x: 780, y: 700, size: 100, color: 'red', at: 'ears' });
    label(s, 'INJURIES', { x: 540, y: 300, size: 80, color: 'yellow', at: 'injuries' });
    words(s);
  },

  answer(s) {
    background(s, 'deep');
    hero(s, { x: 540, y: 1300, scale: 1.4, outline: '#ffffff', at: -1, moves: [{ at: 0, pose: 'sad', face: 'sad' }] });
    label(s, 'COLD SHOCK & PRESSURE INJURIES', { x: 540, y: 300, size: 80, color: 'yellow', at: 'answer' });
    words(s);
  },

  end(s) {
    background(s, 'ocean');
    hero(s, { x: 540, y: 1300, scale: 1.4, outline: '#ffffff', at: 0, moves: [{ at: 0, pose: 'think', face: 'thinking' }] });
    label(s, 'WOULD YOU DARE TO EXPLORE?', { x: 540, y: 300, size: 80, color: 'yellow', at: 'end' });
    words(s);
  },
};
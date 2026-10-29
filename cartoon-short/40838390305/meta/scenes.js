import { hero } from './character.js';
import { background, thing, label, words } from './props.js';

export default {
  hook(s) {
    background(s, 'ocean');
    thing(s, 'wave', { x: 540, y: 1100, size: 900, at: 0 });
    hero(s, {
      x: 540,
      y: 850,
      scale: 1.4,
      outline: '#ffffff',
      at: 0,
      moves: [
        { at: 0, pose: 'fall', face: 'scared' },
        { at: 'Mariana', pose: 'scared', face: 'shocked' }
      ]
    });
    label(s, 'MARIANA TRENCH', { x: 540, y: 300, size: 70, color: 'yellow', at: 'Mariana' });
    words(s);
  },

  step1(s) {
    background(s, 'deep');
    hero(s, {
      x: 540,
      y: 750,
      scale: 1.3,
      outline: '#ffffff',
      at: 0,
      moves: [
        { at: 0, pose: 'fall', face: 'scared' },
        { at: '200', pose: 'fall', face: 'confused' }
      ]
    });
    s.number(200, { x: 540, y: 350, size: 90, suffix: ' metres', color: 'yellow', at: '200' });
    s.icon('sun', { x: 540, y: 180, size: 100, color: 'orange', at: 0, out: 'fade' });
    words(s);
  },

  step2(s) {
    background(s, 'deep');
    hero(s, {
      x: 540,
      y: 800,
      scale: 1.3,
      outline: '#ffffff',
      at: 0,
      moves: [
        { at: 0, pose: 'scared', face: 'shocked' }
      ]
    });
    s.number(1000, { x: 540, y: 320, size: 90, suffix: 'x pressure', color: 'red', at: '1,000' });
    s.arrow([200, 800], [400, 800], { color: 'red', width: 16, at: 'water' });
    s.arrow([880, 800], [680, 800], { color: 'red', width: 16, at: 'water' });
    s.arrow([540, 500], [540, 680], { color: 'red', width: 16, at: 'pressure' });
    words(s);
  },

  answer(s) {
    background(s, 'ocean');
    hero(s, {
      x: 300,
      y: 900,
      scale: 1.3,
      outline: '#ffffff',
      at: 0,
      moves: [
        { at: 0, pose: 'point', face: 'thinking' },
        { at: '10', pose: 'point', face: 'neutral' }
      ]
    });
    label(s, '+1 ATM / 10m', { x: 680, y: 400, size: 70, color: 'green', at: '1' });
    s.arrow([680, 550], [680, 950], { color: 'blue', width: 14, label: 'depth', labelSize: 45, at: 'depth' });
    s.number(10, { x: 680, y: 1100, size: 70, suffix: ' metres', color: 'yellow', at: '10' });
    words(s);
  },

  end(s) {
    background(s, 'deep');
    hero(s, {
      x: 540,
      y: 850,
      scale: 1.4,
      outline: '#ffffff',
      float: true,
      at: 0,
      moves: [
        { at: 0, pose: 'think', face: 'thinking' },
        { at: 'explored', pose: 'shrug', face: 'confused' }
      ]
    });
    s.icon('eye', { x: 540, y: 350, size: 140, color: 'yellow', at: 'explored' });
    label(s, 'UNEXPLORED DEEP', { x: 540, y: 200, size: 65, color: 'white', at: 'deep' });
    words(s);
  }
};

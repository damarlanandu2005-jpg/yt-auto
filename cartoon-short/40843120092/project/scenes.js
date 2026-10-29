import { hero } from './character.js';
import { background, thing, label, words } from './props.js';

export default {
  hook(s) {
    background(s, 'ocean');
    label(s, 'MARIANA TRENCH', { x: 540, y: 260, size: 68, color: 'yellow', at: 'Mariana' });
    thing(s, 'question', { x: 540, y: 440, size: 160, at: 0.2 });
    hero(s, {
      x: 540,
      y: 1100,
      scale: 1.5,
      outline: '#ffffff',
      at: 0,
      moves: [
        { at: 0, pose: 'stand', face: 'confused' },
        { at: 'body', pose: 'shrug', face: 'confused' },
        { at: 'fell', pose: 'fall', face: 'scared' },
      ],
    });
    words(s);
  },

  step1(s) {
    background(s, 'ocean');
    label(s, 'PACIFIC OCEAN DEPTH', { x: 540, y: 170, size: 50, color: 'yellow', at: 'Pacific' });
    s.number(10935, { x: 540, y: 260, size: 76, suffix: ' metres', at: 'depth' });
    s.icon('snowflake', { x: 260, y: 440, size: 100, color: 'cyan', at: 'Cold' });
    label(s, 'COLD SHOCK', { x: 540, y: 440, size: 60, color: 'blue', at: 'Cold' });
    s.icon('skull', { x: 800, y: 440, size: 100, color: 'red', at: 'kill' });
    label(s, 'LETHAL IN 2 MINUTES', { x: 540, y: 540, size: 50, color: 'red', at: 'kill' });
    hero(s, {
      x: 540,
      y: 1180,
      scale: 1.4,
      outline: '#ffffff',
      at: 0,
      moves: [
        { at: 0, pose: 'fall', face: 'scared' },
        { at: 'Cold', pose: 'scared', face: 'shocked' },
      ],
    });
    words(s);
  },

  step2(s) {
    background(s, 'ocean');
    label(s, 'WATER ENTERS LUNGS', { x: 540, y: 220, size: 54, color: 'blue', at: 'drowning' });
    label(s, 'PRESSURE SHRINKS GAS', { x: 540, y: 320, size: 50, color: 'yellow', at: 'shrinks' });
    thing(s, 'drop', { x: 540, y: 460, size: 120, at: 'water' });
    const sink = s.p('sinks', 2.0);
    hero(s, {
      x: 540,
      y: 780 + 340 * sink,
      scale: 1.3,
      outline: '#ffffff',
      at: 0,
      moves: [
        { at: 0, pose: 'fall', face: 'scared' },
        { at: 'drowning', pose: 'scared', face: 'sad' },
        { at: 'shrinks', pose: 'fall', face: 'shocked' },
      ],
    });
    words(s);
  },

  step3(s) {
    background(s, 'deep');
    label(s, 'PRESSURE SQUEEZE', { x: 540, y: 220, size: 60, color: 'red', at: 'difference' });
    label(s, 'LUNGS & EARS CRUSHED', { x: 540, y: 340, size: 52, color: 'yellow', at: 'organs' });
    s.arrow([200, 680], [420, 700], { color: 'red', width: 12, at: 'ears' });
    s.arrow([880, 680], [660, 700], { color: 'red', width: 12, at: 'ears' });
    s.arrow([180, 860], [420, 860], { color: 'red', width: 14, at: 'lungs' });
    s.arrow([900, 860], [660, 860], { color: 'red', width: 14, at: 'lungs' });
    hero(s, {
      x: 540,
      y: 1140,
      scale: 1.4,
      outline: '#ffffff',
      at: 0,
      moves: [
        { at: 0, pose: 'scared', face: 'shocked' },
        { at: 'injuries', pose: 'scared', face: 'sad' },
      ],
    });
    words(s);
  },

  answer(s) {
    background(s, 'deep');
    label(s, 'TWO FATAL THREATS', { x: 540, y: 190, size: 56, color: 'red', at: 'short' });
    s.icon('snowflake', { x: 690, y: 350, size: 74, color: 'cyan', at: 'shock' });
    label(s, '1. COLD SHOCK & DROWNING', { x: 670, y: 440, size: 38, color: 'blue', at: 'shock' });
    label(s, 'DEADLY IN MINUTES', { x: 670, y: 510, size: 34, color: 'white', at: 'minutes' });
    s.icon('heart-pulse', { x: 690, y: 700, size: 74, color: 'red', at: 'pressure' });
    label(s, '2. WATER PRESSURE', { x: 670, y: 790, size: 38, color: 'yellow', at: 'pressure' });
    label(s, 'INJURES INTERNAL ORGANS', { x: 670, y: 860, size: 34, color: 'white', at: 'organs' });
    hero(s, {
      x: 250,
      y: 1060,
      scale: 1.15,
      outline: '#ffffff',
      at: 0,
      moves: [
        { at: 0, pose: 'fall', face: 'scared' },
        { at: 'descend', pose: 'float', face: 'sad' },
      ],
    });
    words(s);
  },

  end(s) {
    background(s, 'ocean');
    label(s, 'WOULD YOU DARE?', { x: 540, y: 280, size: 70, color: 'yellow', at: 0 });
    thing(s, 'question', { x: 540, y: 460, size: 150, at: 'dare' });
    hero(s, {
      x: 540,
      y: 1200,
      scale: 1.5,
      outline: '#ffffff',
      at: 0,
      moves: [
        { at: 0, pose: 'shrug', face: 'thinking' },
        { at: 'explore', pose: 'point', face: 'wow' },
      ],
    });
    words(s);
  },
};

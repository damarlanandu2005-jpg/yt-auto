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
    s.number(10935, { x: 540, y: 250, size: 76, suffix: ' METRES DEEP', at: 'depth' });
    s.icon('snowflake', { x: 260, y: 450, size: 120, color: 'cyan', at: 'Cold' });
    label(s, 'COLD SHOCK', { x: 540, y: 450, size: 64, color: 'blue', at: 'triggers' });
    s.icon('skull', { x: 800, y: 450, size: 110, color: 'red', at: 'kill' });
    hero(s, {
      x: 540,
      y: 1150,
      scale: 1.4,
      outline: '#ffffff',
      at: 0,
      moves: [
        { at: 0, pose: 'fall', face: 'scared' },
        { at: 'Cold', pose: 'scared', face: 'shocked' },
        { at: 'gasping', pose: 'scared', face: 'scared' },
      ],
    });
    words(s);
  },

  step2(s) {
    background(s, 'deep');
    thing(s, 'drop', { x: 540, y: 320, size: 120, at: 'water' });
    label(s, 'HYDROSTATIC PRESSURE', { x: 540, y: 220, size: 54, color: 'yellow', at: 'hydrostatic' });
    s.arrow([190, 800], [380, 800], { color: 'blue', width: 14, at: 'pressure' });
    s.arrow([890, 800], [700, 800], { color: 'blue', width: 14, at: 'pressure' });
    hero(s, {
      x: 540,
      y: 1080,
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
    label(s, 'PRESSURE SQUEEZE', { x: 540, y: 240, size: 60, color: 'red', at: 'difference' });
    label(s, 'LUNGS & EARS CRUSHED', { x: 540, y: 380, size: 52, color: 'yellow', at: 'lungs' });
    s.arrow([260, 680], [420, 710], { color: 'red', width: 12, at: 'ears' });
    s.arrow([820, 680], [660, 710], { color: 'red', width: 12, at: 'ears' });
    s.arrow([240, 850], [430, 850], { color: 'red', width: 14, at: 'lungs' });
    s.arrow([840, 850], [650, 850], { color: 'red', width: 14, at: 'lungs' });
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
    s.icon('skull', { x: 260, y: 280, size: 100, color: 'red', at: 'short' });
    label(s, 'MINUTES TO LIVE', { x: 580, y: 280, size: 56, color: 'red', at: 'kill' });
    label(s, 'MASSIVE PRESSURE', { x: 540, y: 420, size: 54, color: 'yellow', at: 'pressure' });
    hero(s, {
      x: 540,
      y: 1120,
      scale: 1.3,
      outline: '#ffffff',
      at: 0,
      moves: [
        { at: 0, pose: 'fall', face: 'sad' },
        { at: 'descend', pose: 'float', face: 'scared' },
      ],
    });
    words(s);
  },

  end(s) {
    background(s, 'ocean');
    label(s, 'WOULD YOU DARE?', { x: 540, y: 320, size: 70, color: 'yellow', at: 0 });
    thing(s, 'question', { x: 540, y: 480, size: 140, at: 'dare' });
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

import { hero } from './character.js';
import { place, floorY, art, thing, label, words } from './props.js';

export default {
  hook(s) {
    place(s, 'titanic_deck_night', { mood: 'night' });
    art(s, 'ship_front_half', {
      x: 760,
      y: floorY(s, 'titanic_deck_night', 0.5),
      scale: 0.8,
      at: 0,
      rotate: 0.2
    });
    hero(s, {
      x: 380,
      y: floorY(s, 'titanic_deck_night', 0.8),
      scale: 1.3,
      outline: '#ffffff',
      at: 0,
      moves: [
        { at: 0, pose: 'stand', face: 'wow' },
        { at: 'sink', pose: 'scared', face: 'scared' }
      ]
    });
    label(s, 'TITANIC', { x: 540, y: 280, size: 84, color: 'yellow', at: 'Titanic' });
    words(s);
  },

  step1(s) {
    place(s, 'ocean_surface', { mood: 'dark' });
    hero(s, {
      x: 280,
      y: floorY(s, 'ocean_surface', 0.8),
      scale: 1.2,
      outline: '#ffffff',
      at: 0,
      moves: [
        { at: 0, pose: 'point', face: 'shocked' },
        { at: 'lifeboats', pose: 'think', face: 'thinking' }
      ]
    });
    s.draw({ x: 740, y: 640, at: 'iceberg' }, (ctx) => {
      ctx.fillStyle = '#d0f0ff';
      ctx.strokeStyle = '#000000';
      ctx.lineWidth = 4;
      ctx.beginPath();
      ctx.moveTo(-90, 80);
      ctx.lineTo(0, -90);
      ctx.lineTo(40, -40);
      ctx.lineTo(90, 80);
      ctx.closePath();
      ctx.fill();
      ctx.stroke();
    });
    art(s, 'lifeboat_crowded', {
      x: 740,
      y: floorY(s, 'ocean_surface', 0.7),
      scale: 1.1,
      at: 'lifeboats'
    });
    label(s, '1,178 PEOPLE', { x: 740, y: 320, size: 76, color: 'white', at: '1,178' });
    words(s);
  },

  step2(s) {
    place(s, 'titanic_deck_night', { mood: 'dark', zoom: 1.4, focus: [0.5, 0.7] });
    hero(s, {
      x: 420,
      y: floorY(s, 'titanic_deck_night', 0.75),
      scale: 1.3,
      outline: '#ffffff',
      at: 0,
      moves: [
        { at: 0, pose: 'stand', face: 'scared' },
        { at: 'plunge', pose: 'fall', face: 'shocked' }
      ]
    });
    thing(s, 'drop', { x: 720, y: 880, size: 80, at: 'water' });
    label(s, 'MINUS 2 DEGREES', { x: 540, y: 280, size: 76, color: 'blue', at: 'minus' });
    words(s);
  },

  answer(s) {
    place(s, 'deep_sea', { mood: 'underwater' });
    hero(s, {
      x: 540,
      y: floorY(s, 'deep_sea', 0.85),
      scale: 1.2,
      float: true,
      outline: '#ffffff',
      at: 0,
      moves: [
        { at: 0, pose: 'float', face: 'scared' },
        { at: 'unable', pose: 'sad', face: 'sad' }
      ]
    });
    s.icon('snowflake', { x: 300, y: 550, size: 80, color: '#a0e0ff', at: 'Cold' });
    s.icon('snowflake', { x: 780, y: 620, size: 70, color: '#a0e0ff', at: 'Cold' });
    label(s, 'UNABLE TO SWIM', { x: 540, y: 300, size: 80, color: 'red', at: 'unable' });
    words(s);
  },

  end(s) {
    place(s, 'ocean_surface', { mood: 'night' });
    hero(s, {
      x: 320,
      y: floorY(s, 'ocean_surface', 0.8),
      scale: 1.3,
      outline: '#ffffff',
      at: 0,
      moves: [
        { at: 0, pose: 'shrug', face: 'confused' },
        { at: 'sinking', pose: 'sad', face: 'sad' }
      ]
    });
    art(s, 'ship_front_half', {
      x: 740,
      y: floorY(s, 'ocean_surface', 0.5),
      scale: 1.1,
      at: 0,
      rotate: 0.15
    });
    label(s, 'SINKING', { x: 540, y: 280, size: 84, color: 'yellow', at: 'sinking' });
    words(s);
  }
};

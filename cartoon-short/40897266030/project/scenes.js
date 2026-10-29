import { hero, crowd } from './character.js';
import { place, stand, cut, art, waterRise, bubbles, label, words, emoji, pieces } from './props.js';

const ME = { outfit: 'passenger_1912', hat: 'bowler', hair: 'short' };

export default {
  hook(s) {
    const k = cut(s, ['sink']);
    if (k === 0) {
      place(s, 'titanic_deck_night', { shot: 'wide', mood: 'night' });
      hero(s, {
        x: 360,
        ...stand(s, 0.75),
        look: ME,
        at: 0,
        moves: [{ at: 0, pose: 'walk', face: 'happy' }]
      });
    } else {
      place(s, 'titanic_deck_night', { shot: 'close', focus: 0.4, mood: 'night' });
      hero(s, {
        x: 520,
        ...stand(s, 0.85),
        look: ME,
        at: 0,
        moves: [{ at: 0, pose: 'look_down', face: 'shocked' }]
      });
    }
    words(s);
  },

  step1(s) {
    const k = cut(s, ['lifeboats']);
    if (k === 0) {
      place(s, 'titanic_deck_night', { shot: 'wide', mood: 'cold' });
      emoji(s, 'snow_capped_mountain', { x: 800, y: 720, size: 280, at: 0 });
      pieces(s, { x: 780, y: 760, at: 'struck', kind: 'ice', n: 16, spread: 260 });
      hero(s, {
        x: 280,
        ...stand(s, 0.75),
        look: ME,
        at: 0,
        moves: [{ at: 0, pose: 'stand', face: 'neutral' }, { at: 'struck', pose: 'point', face: 'shocked' }]
      });
    } else {
      place(s, 'titanic_deck_night', { shot: 'medium', mood: 'night' });
      art(s, 'lifeboat_crowded', { x: 560, y: 1200, scale: 1.1, at: 'lifeboats' });
      hero(s, {
        x: 320,
        ...stand(s, 0.8),
        look: ME,
        at: 'lifeboats',
        moves: [{ at: 'lifeboats', pose: 'shrug', face: 'worried' }]
      });
      label(s, '1,178 PEOPLE', { x: 540, y: 380, size: 76, color: 'yellow', at: '1,178' });
    }
    words(s);
  },

  step2(s) {
    const k = cut(s, ['under']);
    if (k === 0) {
      place(s, 'titanic_deck_night', { shot: 'wide', mood: 'storm', quake: { at: 'sank', until: 'under' } });
      crowd(s, {
        n: 5,
        x0: 160,
        x1: 920,
        y: 1300,
        scale: 0.7,
        seed: 7,
        outfits: ['passenger_1912', 'dress', 'worker'],
        faces: ['scared', 'shocked'],
        poses: ['panic', 'scared'],
        outline: '#ffffff',
        at: 0
      });
      hero(s, {
        x: 480,
        ...stand(s, 0.8),
        look: ME,
        at: 0,
        moves: [{ at: 0, pose: 'panic', face: 'scared' }]
      });
    } else {
      place(s, 'titanic_deck_night', { shot: 'medium', mood: 'cold' });
      waterRise(s, { from: 1800, to: 1000, at: 'under' });
      emoji(s, 'snowflake', { x: 260, y: 500, size: 120, at: 'minus' });
      emoji(s, 'snowflake', { x: 800, y: 540, size: 130, at: 'degrees' });
      hero(s, {
        x: 520,
        ...stand(s, 0.85),
        look: ME,
        at: 'under',
        moves: [{ at: 'under', pose: 'fall', face: 'pain' }]
      });
      label(s, 'MINUS 2 DEGREES', { x: 540, y: 360, size: 74, color: 'blue', at: 'minus' });
    }
    words(s);
  },

  answer(s) {
    const k = cut(s, ['limbs']);
    if (k === 0) {
      place(s, 'underwater', { shot: 'medium', mood: 'cold' });
      bubbles(s, { x: 540, y: 1200, width: 300, n: 12, at: 0 });
      hero(s, {
        x: 500,
        ...stand(s, 0.8),
        look: ME,
        at: 0,
        moves: [{ at: 0, pose: 'shiver', face: 'cold' }]
      });
    } else {
      place(s, 'underwater', { shot: 'close', mood: 'cold' });
      bubbles(s, { x: 540, y: 1100, width: 220, n: 8, at: 'limbs' });
      hero(s, {
        x: 520,
        ...stand(s, 0.85),
        look: ME,
        at: 'limbs',
        moves: [{ at: 'limbs', pose: 'float', face: 'sad' }]
      });
      label(s, 'UNABLE TO SWIM', { x: 540, y: 380, size: 78, color: 'red', at: 'unable' });
    }
    words(s);
  },

  end(s) {
    place(s, 'deep_sea', { shot: 'wide', mood: 'dark' });
    art(s, 'ship_wreck', { x: 620, y: 1320, scale: 1.3, at: 0 });
    hero(s, {
      x: 320,
      ...stand(s, 0.75),
      look: ME,
      at: 0,
      moves: [{ at: 0, pose: 'think', face: 'thinking' }]
    });
    label(s, 'TITANIC', { x: 540, y: 340, size: 84, color: 'white', at: 'Titanic' });
    words(s);
  }
};

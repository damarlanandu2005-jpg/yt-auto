import { hero, crowd } from './character.js';
import { place, stand, cut, art, waterRise, label, words } from './props.js';

const ME = { outfit: 'passenger_1912', hat: 'bowler', hair: 'short' };

export default {
  hook(s) {
    const k = cut(s, ['Titanic', 'sink']);
    if (k === 0) {
      place(s, 'titanic_deck_night', { shot: 'wide', mood: 'night' });
      hero(s, { x: 380, ...stand(s, 0.75), look: ME, at: 0, moves: [{ at: 0, pose: 'walk', face: 'happy' }] });
    } else if (k === 1) {
      place(s, 'titanic_deck_night', { shot: 'medium', focus: 0.4, mood: 'night' });
      hero(s, { x: 440, ...stand(s, 0.8), look: ME, at: 0, moves: [{ at: 0, pose: 'stand', face: 'shocked' }] });
    } else {
      place(s, 'titanic_deck_night', { shot: 'close', focus: 0.5, mood: 'night' });
      waterRise(s, { from: 1920, to: 1400, at: 'sink' });
      hero(s, { x: 500, ...stand(s, 0.85), look: ME, at: 0, moves: [{ at: 0, pose: 'panic', face: 'scared' }] });
    }
    words(s);
  },

  step1(s) {
    const k = cut(s, ['iceberg', 'lifeboats']);
    if (k === 0) {
      place(s, 'ocean_surface', { shot: 'wide', mood: 'night' });
      art(s, 'ocean_liner', { x: 320, y: 1100, scale: 0.8, at: 0 });
      art(s, 'iceberg', { x: 780, y: 1120, scale: 0.9, at: 'struck' });
    } else if (k === 1) {
      place(s, 'titanic_deck_night', { shot: 'medium', focus: 0.3, mood: 'night' });
      hero(s, { x: 360, ...stand(s, 0.8), look: ME, at: 0, moves: [{ at: 0, pose: 'point', face: 'worried' }] });
    } else {
      place(s, 'ocean_surface', { shot: 'medium', mood: 'night' });
      art(s, 'lifeboat_crowded', { x: 380, y: 1180, scale: 1.1, at: 'lifeboats' });
      hero(s, { x: 800, y: 1220, scale: 1.1, outline: '#ffffff', look: ME, at: 'lifeboats',
        moves: [{ at: 0, pose: 'sad', face: 'sad' }] });
      label(s, '1,178 PEOPLE', { x: 540, y: 350, size: 76, color: 'yellow', at: '1,178' });
    }
    words(s);
  },

  step2(s) {
    const k = cut(s, ['sank', 'plunge']);
    if (k === 0) {
      place(s, 'titanic_deck_night', { shot: 'wide', mood: 'night' });
      crowd(s, { n: 5, x0: 480, x1: 960, ...stand(s, 0.45), seed: 7,
        outfits: ['passenger_1912', 'dress', 'worker'], faces: ['scared', 'shocked'], poses: ['panic', 'scared'] });
      hero(s, { x: 320, ...stand(s, 0.8), look: ME, at: 0, moves: [{ at: 0, pose: 'crouch', face: 'scared' }] });
    } else if (k === 1) {
      place(s, 'titanic_deck_night', { shot: 'medium', mood: 'night' });
      waterRise(s, { from: 1920, to: 1050, at: 'under' });
      hero(s, { x: 420, ...stand(s, 0.85), look: ME, at: 0, moves: [{ at: 0, pose: 'panic', face: 'shocked' }] });
    } else {
      place(s, 'storm_sea', { shot: 'close', mood: 'cold' });
      hero(s, { x: 540, y: 1220, scale: 1.3, outline: '#ffffff', look: ME, at: 'plunge',
        moves: [{ at: 0, pose: 'fall', face: 'cold' }, { at: 'water', pose: 'shiver', face: 'pain' }] });
      label(s, 'MINUS 2 DEGREES', { x: 540, y: 320, size: 74, color: 'blue', at: 'minus' });
    }
    words(s);
  },

  answer(s) {
    const k = cut(s, ['limbs', 'swim']);
    if (k === 0) {
      place(s, 'storm_sea', { shot: 'medium', mood: 'cold' });
      hero(s, { x: 500, y: 1200, scale: 1.25, outline: '#ffffff', look: ME, at: 0,
        moves: [{ at: 0, pose: 'shiver', face: 'cold' }] });
      s.icon('snowflake', { x: 320, y: 650, size: 100, color: '#70d6ff', at: 'Cold' });
      s.icon('snowflake', { x: 740, y: 690, size: 85, color: '#70d6ff', at: 'incapacitation' });
    } else if (k === 1) {
      place(s, 'ocean_surface', { shot: 'close', mood: 'night' });
      hero(s, { x: 520, y: 1260, scale: 1.5, outline: '#ffffff', look: ME, at: 0,
        moves: [{ at: 0, pose: 'shiver', face: 'pain' }] });
    } else {
      place(s, 'deep_sea', { shot: 'medium', mood: 'cold' });
      hero(s, { x: 540, y: 920, scale: 1.2, outline: '#ffffff', look: ME, at: 'swim',
        moves: [{ at: 0, pose: 'fall', face: 'sad' }] });
      label(s, 'UNABLE TO SWIM', { x: 540, y: 340, size: 78, color: 'red', at: 'swim' });
    }
    words(s);
  },

  end(s) {
    place(s, 'ocean_surface', { shot: 'medium', mood: 'dusk' });
    hero(s, { x: 520, y: 1240, scale: 1.2, outline: '#ffffff', look: ME, at: 0,
      moves: [{ at: 0, pose: 'think', face: 'sad' }, { at: 'Titanic', pose: 'sad', face: 'thinking' }] });
    words(s);
  },
};

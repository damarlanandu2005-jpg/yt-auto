import { BODIES, FACES, HAIRS, HATS, OUTFITS, POSES, crowd, hero } from './character.js';
import { THING_NAMES, art, background, blackHole, bubbles, cut, emoji, explosion, fire, floorY, glow, label, lava, pieces, place, smoke, speedLines, stand, stars, thing, waterRise, weather, words } from './props.js';
const ME = { outfit: 'passenger_1912', hat: 'bowler', hair: 'short' };

export default {
  hook(s) {
    const k = cut(s, ['Titanic', 'iceberg']);
    if (k === 0) {
      background(s, 'ocean', { mood: 'night' });
      art('iceberg', { x: 200, y: 1100, scale: 0.3 });
      hero(s, { x: 540, y: 800, scale: 1.4, outline: '#ffffff', at: 0,
        look: ME,
        moves: [{ at: 0, pose: 'float', face: 'happy' }, { at: 'iceberg', pose: 'point', face: 'shocked' }]
      });
    } else {
      place(s, 'titanic_deck_night', { shot: 'medium' });
      art('iceberg', { x: 100, y: 1100, scale: 0.3 });
      hero(s, { x: 480, ...stand(s, 0.8), look: ME, moves: [{ at: 0, pose: 'walk', face: 'happy' }] });
    }
    words(s);
  },

  step1(s) {
    const k = cut(s, ['iceberg']);
    if (k === 0) {
      place(s, 'titanic_deck_night', { shot: 'medium' });
      art('iceberg', { x: 100, y: 1100, scale: 0.3 });
      hero(s, { x: 480, ...stand(s, 0.8), look: ME, moves: [{ at: 0, pose: 'point', face: 'shocked' }] });
    } else {
      place(s, 'titanic_deck_night', { shot: 'medium' });
      waterRise(s, { from: 1920, to: 1300, at: 'water' });
      hero(s, { x: 480, ...stand(s, 0.8), look: ME, moves: [{ at: 0, pose: 'scared', face: 'shocked' }] });
    }
    words(s);
  },

  step2(s) {
    const k = cut(s, ['lifeboats']);
    if (k === 0) {
      place(s, 'titanic_deck_night', { shot: 'wide' });
      crowd(s, { n: 10, x0: 100, x1: 900, y: 1500, scale: 0.6, depth: 40, seed: 4, outfits: ['passenger_1912', 'dress'],
        faces: ['scared', 'shocked'], poses: ['panic'], outline: '#ffffff', at: 'panic' });
      hero(s, { x: 540, ...stand(s, 0.8), look: ME, moves: [{ at: 0, pose: 'sprint', face: 'scared' }] });
    } else {
      background(s, 'ocean', { mood: 'night' });
      waterRise(s, { from: 1920, to: 1300, at: 'water' });
      hero(s, { x: 540, y: 1400, scale: 1.0, outline: '#ffffff', moves: [{ at: 0, pose: 'fall', face: 'scared' }] });
    }
    words(s);
  },

  step3(s) {
    const k = cut(s, ['cold']);
    if (k === 0) {
      background(s, 'ocean', { mood: 'night' });
      emoji(s, 'thermometer', { x: 800, y: 1000, size: 150 });
      hero(s, { x: 540, y: 1400, scale: 1.2, outline: '#ffffff', moves: [{ at: 0, pose: 'swim', face: 'scared' },
        { at: 'cold', pose: 'shiver', face: 'scared' }]
      });
    } else {
      background(s, 'ocean', { mood: 'night' });
      hero(s, { x: 540, y: 1400, scale: 0.9, outline: '#ffffff', moves: [{ at: 0, pose: 'lie', face: 'sad' }] });
    }
    words(s);
  },

  answer(s) {
    const k = cut(s, ['heart']);
    if (k === 0) {
      background(s, 'ocean', { mood: 'night' });
      hero(s, { x: 540, y: 1400, scale: 1.1, outline: '#ffffff', moves: [{ at: 0, pose: 'fall', face: 'scared' }] });
    } else {
      background(s, 'ocean', { mood: 'night' });
      emoji(s, 'heart', { x: 600, y: 800, size: 120 });
      hero(s, { x: 540, y: 1400, scale: 1.1, outline: '#ffffff', moves: [{ at: 0, pose: 'lie', face: 'sad' }] });
    }
    words(s);
  },

  end(s) {
    background(s, 'ocean', { mood: 'night' });
    art('lifeboat', { x: 100, y: 1400, scale: 0.5 });
    hero(s, { x: 540, y: 900, scale: 1.4, outline: '#ffffff', moves: [{ at: 0, pose: 'think', face: 'thinking' }] });
    words(s);
  },
};

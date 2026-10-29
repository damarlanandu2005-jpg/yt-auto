import { BODIES, FACES, HAIRS, HATS, OUTFITS, POSES, crowd, hero } from './character.js';
import { THING_NAMES, art, background, blackHole, bubbles, cut, emoji, explosion, fire, floorY, glow, label, lava, pieces, place, smoke, speedLines, stand, stars, thing, waterRise, weather, words } from './props.js';
const ME = { outfit: 'passenger_1912', hat: 'bowler', hair: 'short' };

export default {
  hook(s) {
    const k = cut(s, ['iceberg']);
    if (k === 0) {
      place(s, 'titanic_deck_night', { shot: 'wide', mood: 'night' });
      hero(s, { x: 360, ...stand(s, 0.7), look: ME, moves: [{ at: 0, pose: 'walk', face: 'happy' }, { at: 'iceberg', pose: 'point', face: 'shocked' }] });
    } else {
      place(s, 'titanic_deck_night', { shot: 'close', focus: 0.3, mood: 'night' });
      art(s, 'iceberg', { x: 720, y: 1200, scale: 2.5 });
      hero(s, { x: 480, ...stand(s, 0.8), look: ME, moves: [{ at: 0, pose: 'point', face: 'shocked' }] });
    }
    words(s);
  },

  step1(s) {
    const k = cut(s, ['water']);
    if (k === 0) {
      place(s, 'ocean_surface', { shot: 'medium' });
      art(s, 'iceberg', { x: 540, y: 1200, scale: 2.5 });
      label(s, '1/10 ABOVE WATER', { x: 540, y: 300, size: 60, color: 'yellow', at: 'water' });
      emoji(s, 'snowflake', { x: 100, y: 1000, size: 120, at: 'water' });
      hero(s, { x: 300, ...stand(s, 0.8), look: ME, moves: [{ at: 0, pose: 'think', face: 'confused' }] });
    } else {
      place(s, 'ocean_surface', { shot: 'close' });
      art(s, 'iceberg', { x: 720, y: 1100, scale: 3.0 });
      hero(s, { x: 420, ...stand(s, 0.8), look: ME, moves: [{ at: 0, pose: 'shrug', face: 'worried' }] });
    }
    words(s);
  },

  step2(s) {
    const k = cut(s, ['lifeboats']);
    if (k === 0) {
      place(s, 'titanic_deck_night', { shot: 'wide', mood: 'night' });
      art(s, 'lifeboat', { x: 800, y: 1100, scale: 1.2 });
      crowd(s, { n: 6, x0: 120, x1: 960, y: 1300, scale: 0.8, depth: 40, seed: 4, outfits: ['passenger_1912', 'dress'], poses: ['panic'], faces: ['scared'], at: 0 });
      hero(s, { x: 540, ...stand(s, 0.7), look: ME, moves: [{ at: 0, pose: 'wave', face: 'neutral' }] });
    } else {
      place(s, 'titanic_deck_night', { shot: 'medium', mood: 'night' });
      art(s, 'lifeboat', { x: 700, y: 1000, scale: 1.2 });
      label(s, 'ONLY 1/3 LIFEBOATS', { x: 540, y: 300, size: 60, color: 'red', at: 'lifeboats' });
      hero(s, { x: 420, ...stand(s, 0.8), look: ME, moves: [{ at: 0, pose: 'point', face: 'shocked' }] });
    }
    words(s);
  },

  step3(s) {
    const k = cut(s, ['freezing']);
    if (k === 0) {
      place(s, 'titanic_deck_night', { shot: 'medium', mood: 'night' });
      art(s, 'lifeboat', { x: 700, y: 1000, scale: 1.2 });
      crowd(s, { n: 4, x0: 560, x1: 980, ...stand(s, 0.35), seed: 11, outfits: ['passenger_1912', 'tshirt', 'worker'], faces: ['scared', 'shocked'], poses: ['sprint'] });
      hero(s, { x: 360, ...stand(s, 0.85), look: ME, at: 0, move: { to: [540, 1300], at: 'freezing' }, moves: [{ at: 0, pose: 'sprint', face: 'scared' }] });
    } else {
      place(s, 'ocean_surface', { shot: 'medium' });
      emoji(s, 'snowflake', { x: 100, y: 1000, size: 120, at: 'freezing' });
      label(s, '-2°C', { x: 100, y: 900, size: 50, color: 'white', at: 'freezing' });
      hero(s, { x: 540, y: 1300, ...stand(s, 0.8), look: ME, moves: [{ at: 0, pose: 'float', face: 'scared' }] });
    }
    words(s);
  },

  answer(s) {
    const k = cut(s, ['incapacitation']);
    if (k === 0) {
      place(s, 'ocean_surface', { shot: 'medium' });
      hero(s, { x: 540, y: 1300, ...stand(s, 0.8), look: ME, moves: [{ at: 0, pose: 'float', face: 'shocked' }] });
      label(s, 'COLD SHOCK', { x: 540, y: 300, size: 70, color: 'blue', at: 'shock' });
    } else {
      place(s, 'ocean_surface', { shot: 'close' });
      hero(s, { x: 540, y: 1300, ...stand(s, 0.8), look: ME, moves: [{ at: 0, pose: 'fall', face: 'determined' }] });
      // No second label - shown through pose/face
    }
    words(s);
  },

  end(s) {
    place(s, 'ocean_surface', { shot: 'medium' });
    art(s, 'lifeboat', { x: 700, y: 1000, scale: 1.2 });
    hero(s, { x: 300, ...stand(s, 0.8), look: ME, moves: [{ at: 0, pose: 'wave', face: 'determined' }] });
    label(s, 'PLACE IN LIFEBOAT?', { x: 540, y: 300, size: 70, color: 'yellow' });
    words(s);
  }
};
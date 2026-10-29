import { BODIES, FACES, HAIRS, HATS, OUTFITS, POSES, crowd, hero } from './character.js';
import { THING_NAMES, art, background, blackHole, bubbles, cut, emoji, explosion, fire, floorY, glow, label, lava, pieces, place, smoke, speedLines, stand, stars, thing, waterRise, weather, words } from './props.js';
export default {
  hook(s) {
    const k = cut(s, ['iceberg']);
    if (k === 0) {
      place(s, 'titanic_deck_night', { shot: 'wide', mood: 'night' });
      hero(s, { x: 360, ...stand(s, 0.7), look: { outfit: 'passenger_1912', hat: 'bowler', hair: 'short' },
        moves: [{ at: 0, pose: 'walk', face: 'happy' }] });
    } else {
      place(s, 'titanic_deck_night', { shot: 'close', focus: 0.3, mood: 'night' });
      hero(s, { x: 480, ...stand(s, 0.8), look: { outfit: 'passenger_1912', hat: 'bowler', hair: 'short' },
        moves: [{ at: 0, pose: 'point', face: 'shocked' }] });
      art(s, 'iceberg', { x: 800, y: 1100, scale: 0.5, at: 0 });
    }
    words(s);
  },

  step1(s) {
    const k = cut(s, ['surface']);
    if (k === 0) {
      place(s, 'ocean_surface', { shot: 'wide', mood: 'night' });
      hero(s, { x: 360, ...stand(s, 0.7), look: { outfit: 'passenger_1912', hat: 'bowler', hair: 'short' },
        moves: [{ at: 0, pose: 'stand', face: 'neutral' }] });
      art(s, 'iceberg', { x: 900, y: 1300, scale: 1.0, at: 0 });
    } else {
      place(s, 'ocean_surface', { shot: 'close', focus: 0.7, mood: 'night' });
      hero(s, { x: 480, ...stand(s, 0.8), look: { outfit: 'passenger_1912', hat: 'bowler', hair: 'short' },
        moves: [{ at: 0, pose: 'point', face: 'neutral' }] });
      art(s, 'iceberg', { x: 900, y: 1300, scale: 1.0, at: 0 });
    }
    words(s);
  },

  step2(s) {
    const k = cut(s, ['lifeboats']);
    if (k === 0) {
      place(s, 'ship_corridor', { shot: 'medium' });
      waterRise(s, { from: 1920, to: 1300, at: 'foundering', until: 'foundering' });
      hero(s, { x: 300, ...stand(s, 0.8), look: { outfit: 'passenger_1912', hat: 'bowler', hair: 'short' },
        moves: [{ at: 0, pose: 'run', face: 'scared' }] });
    } else {
      place(s, 'titanic_deck_night', { shot: 'medium', mood: 'night' });
      art(s, 'lifeboat', { x: 600, y: 1200, scale: 0.6, at: 'lifeboats' });
      hero(s, { x: 400, ...stand(s, 0.8), look: { outfit: 'passenger_1912', hat: 'bowler', hair: 'short' },
        moves: [{ at: 0, pose: 'look_up', face: 'worried' }] });
    }
    words(s);
  },

  step3(s) {
    const k = cut(s, ['sea']);
    if (k === 0) {
      place(s, 'titanic_deck_night', { shot: 'medium', mood: 'night' });
      hero(s, { x: 400, ...stand(s, 0.8), look: { outfit: 'passenger_1912', hat: 'bowler', hair: 'short' },
        moves: [{ at: 0, pose: 'stand', face: 'sad' }] });
    } else {
      place(s, 'storm_sea', { shot: 'medium', mood: 'storm' });
      hero(s, { x: 600, y: 1100, scale: 0.8, look: { outfit: 'passenger_1912', hat: 'bowler', hair: 'short' },
        pose: 'shiver', face: 'pain' });
    }
    words(s);
  },

  answer(s) {
    place(s, 'storm_sea', { shot: 'close', mood: 'storm' });
    hero(s, { x: 480, y: 1000, scale: 1.0, look: { outfit: 'passenger_1912', hat: 'bowler', hair: 'short' },
      pose: 'panic', face: 'pain' });
    words(s);
  },

  end(s) {
    place(s, 'titanic_deck_night', { shot: 'medium', mood: 'night' });
    hero(s, { x: 400, ...stand(s, 0.8), look: { outfit: 'passenger_1912', hat: 'bowler', hair: 'short' },
      moves: [{ at: 0, pose: 'think', face: 'thinking' }] });
    words(s);
  }
};
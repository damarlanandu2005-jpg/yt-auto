import { BODIES, FACES, HAIRS, HATS, OUTFITS, POSES, crowd, hero } from './character.js';
import { THING_NAMES, art, background, blackHole, bubbles, cut, emoji, explosion, fire, floorY, glow, label, lava, pieces, place, smoke, speedLines, stand, stars, thing, waterRise, weather, words } from './props.js';
const ME = { outfit: 'passenger_1912', hat: 'bowler', hair: 'short' };

export default {
  hook(s) {
    const k = cut(s, ['titanic', 'iceberg']);
    if (k === 0) {
      // wide: Titanic deck at night, hero walking
      place(s, 'titanic_deck_night', { shot: 'wide', mood: 'night' });
      hero(s, { x: 320, y: 1300, scale: 1.2, outline: '#ffffff', look: ME,
        moves: [{ at: 0, pose: 'walk', face: 'happy' }] });
    } else {
      // close: hero points at iceberg, shocked
      place(s, 'titanic_deck_night', { shot: 'close', focus: 0.4, mood: 'night' });
      hero(s, { x: 540, y: 1300, scale: 1.4, outline: '#ffffff', look: ME,
        moves: [{ at: 0, pose: 'point', face: 'shocked' }] });
      art(s, 'iceberg', { x: 860, y: 800, scale: 1.2, at: 0 });
    }
    words(s);
  },

  step1(s) {
    const k = cut(s, ['iceberg']);
    if (k === 0) {
      // wide: massive iceberg, only tip visible above water
      place(s, 'titanic_deck_night', { shot: 'wide', mood: 'night' });
      art(s, 'iceberg', { x: 540, y: 900, scale: 1.5, at: 0 });
      hero(s, { x: 260, y: 1300, scale: 1.2, outline: '#ffffff', look: ME,
        moves: [{ at: 0, pose: 'stand', face: 'neutral' }] });
    } else {
      // close: tip above water, hero points shocked
      place(s, 'titanic_deck_night', { shot: 'close', focus: 0.5, mood: 'night' });
      art(s, 'iceberg', { x: 540, y: 820, scale: 0.9, at: 0 });
      hero(s, { x: 460, y: 1300, scale: 1.4, outline: '#ffffff', look: ME,
        moves: [{ at: 0, pose: 'point', face: 'shocked' }] });
    }
    words(s);
  },

  step2(s) {
    const k = cut(s, ['ice', 'lifeboats', 'one-third']);
    if (k === 0) {
      // medium: collision on open water, ship front half hits iceberg
      place(s, 'ocean_surface', { shot: 'medium', mood: 'storm' });
      art(s, 'ship_front_half', { x: 300, y: 900, scale: 1.0, at: 0 });
      art(s, 'iceberg', { x: 720, y: 880, scale: 0.8, at: 0 });
      hero(s, { x: 540, y: 1300, scale: 1.3, outline: '#ffffff', look: ME,
        moves: [{ at: 0, pose: 'stand', face: 'shocked' }] });
    } else {
      // close: lifeboats on deck, label ONE‑THIRD
      place(s, 'titanic_deck_night', { shot: 'close', focus: 0.3, mood: 'night' });
      art(s, 'lifeboat', { x: 460, y: 1150, scale: 0.9, at: 0 });
      art(s, 'lifeboat', { x: 620, y: 1150, scale: 0.9, at: 0 });
      label(s, 'ONE‑THIRD', { x: 540, y: 1000, size: 80, color: 'yellow', at: 0 });
      hero(s, { x: 540, y: 1300, scale: 1.4, outline: '#ffffff', look: ME,
        moves: [{ at: 0, pose: 'sad', face: 'sad' }] });
    }
    words(s);
  },

  step3(s) {
    const k = cut(s, ['deck', 'freezing', 'water']);
    if (k === 0) {
      // medium: raised poop deck, icy water rising
      place(s, 'titanic_deck_night', { shot: 'medium', mood: 'cold' });
      // use wave emoji to suggest ship hull, not floating object
      emoji(s, 'water_wave', { x: 540, y: 950, size: 300, at: 0 });
      waterRise(s, { from: 1920, to: 1300, at: 'water', until: 'water' });
      hero(s, { x: 540, y: 1300, scale: 1.3, outline: '#ffffff', look: ME,
        moves: [{ at: 0, pose: 'stand', face: 'neutral' }] });
    } else {
      // close: hero plunges into freezing water, splash
      place(s, 'titanic_deck_night', { shot: 'close', focus: 0.5, mood: 'cold' });
      hero(s, { x: 540, y: 1190, scale: 1.2, outline: '#ffffff', look: ME,
        moves: [{ at: 0, pose: 'fall', face: 'shocked' }] });
      bubbles(s, { x: 540, y: 1190, width: 200, n: 12, at: 0 });
      speedLines(s, { dir: 'down', at: 0 });
    }
    words(s);
  },

  answer(s) {
    const k = cut(s, ['cold', 'breathing', 'heart']);
    if (k === 0) {
      // underwater cold shock, label only once
      background(s, 'ocean');
      hero(s, { x: 540, y: 1100, scale: 1.2, outline: '#ffffff', look: ME,
        moves: [{ at: 0, pose: 'float', face: 'scared' }] });
      label(s, 'COLD SHOCK', { x: 760, y: 300, size: 80, color: 'red', at: 0 });
      // breath clouds
      for (let i = 0; i < 3; i++) {
        const y = 1020 - i * 30;
        s.circle({ x: 540, y, r: 20, fill: '#bbf', color: '#fff', at: i * 0.2 });
      }
      // heart pulse indicator
      glow(s, { x: 540, y: 1150, r: 80, color: '255,0,0', pulse: true, at: 0 });
    } else if (k === 1) {
      // breathing illustration
      background(s, 'ocean');
      hero(s, { x: 540, y: 1080, scale: 1.2, outline: '#ffffff', look: ME,
        moves: [{ at: 0, pose: 'float', face: 'scared' }] });
      // small breath puffs
      for (let i = 0; i < 3; i++) {
        const y = 1000 - i * 25;
        s.circle({ x: 540, y, r: 18, fill: '#ddf', color: '#fff', at: i * 0.2 });
      }
    } else {
      // heart strain illustration
      background(s, 'ocean');
      hero(s, { x: 540, y: 1080, scale: 1.2, outline: '#ffffff', look: ME,
        moves: [{ at: 0, pose: 'float', face: 'scared' }] });
      glow(s, { x: 540, y: 1150, r: 90, color: '255,0,0', pulse: true, at: 0 });
    }
    words(s);
  },

  end(s) {
    // close on a lifeboat on deck, hero thoughtful
    place(s, 'titanic_deck_night', { shot: 'close', focus: 0.3, mood: 'night' });
    art(s, 'lifeboat', { x: 540, y: 1150, scale: 1.0, at: 0 });
    hero(s, { x: 540, y: 1300, scale: 1.4, outline: '#ffffff', look: ME,
      moves: [{ at: 0, pose: 'think', face: 'thinking' }] });
    words(s);
  },
};
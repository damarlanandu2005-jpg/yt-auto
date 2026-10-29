import { BODIES, FACES, HAIRS, HATS, OUTFITS, POSES, crowd, hero } from './character.js';
import { THING_NAMES, art, background, blackHole, bubbles, cut, emoji, explosion, fire, floorY, glow, label, lava, pieces, place, smoke, speedLines, stand, stars, thing, waterRise, weather, words } from './props.js';
const ME = { outfit: 'passenger_1912', hat: 'bowler', hair: 'short' }; // same look throughout

export default {
  hook(s) {
    const k = cut(s, ['Titanic', 'iceberg']);
    if (k === 0) {
      // wide: Titanic deck at night, hero walking
      place(s, 'titanic_deck_night', { shot: 'wide', mood: 'night' });
      hero(s, { x: 300, ...stand(s, 0.7), scale: 1.2, outline: '#ffffff', look: ME,
        moves: [{ at: 0, pose: 'walk', face: 'happy' }] });
    } else {
      // close: hero points at iceberg, shocked
      place(s, 'titanic_deck_night', { shot: 'close', focus: 0.4, mood: 'night' });
      hero(s, { x: 540, ...stand(s, 0.8), scale: 1.4, outline: '#ffffff', look: ME,
        moves: [{ at: 0, pose: 'point', face: 'shocked' }] });
      art(s, 'iceberg', { x: 540, y: 1080, scale: 0.9, at: 0 });
    }
    words(s);
  },

  step1(s) {
    const k = cut(s, ['iceberg', 'water']);
    if (k === 0) {
      // wide: iceberg tip above water, hero on deck left
      place(s, 'titanic_deck_night', { shot: 'wide', mood: 'night' });
      art(s, 'iceberg', { x: 720, y: 1080, scale: 1.0, at: 0 });
      thing(s, 'wave', { x: 540, y: 950, size: 300, at: 0 });
      hero(s, { x: 240, ...stand(s, 0.6), scale: 1.2, outline: '#ffffff', look: ME,
        moves: [{ at: 0, pose: 'stand', face: 'neutral' }] });
    } else {
      // close: tip clearer, water line stronger, hero shocked
      place(s, 'titanic_deck_night', { shot: 'close', focus: 0.5, mood: 'night' });
      art(s, 'iceberg', { x: 540, y: 1020, scale: 0.8, at: 0 });
      thing(s, 'wave', { x: 540, y: 880, size: 200, at: 0 });
      hero(s, { x: 460, ...stand(s, 0.8), scale: 1.4, outline: '#ffffff', look: ME,
        moves: [{ at: 0, pose: 'point', face: 'shocked' }] });
    }
    words(s);
  },

  step2(s) {
    const k = cut(s, ['strike', 'lifeboats', 'one-third']);
    if (k === 0) {
      // medium: Titanic bow collides with iceberg on a stormy sea
      place(s, 'storm_sea', { shot: 'medium', mood: 'storm' });
      art(s, 'ship_front_half', { x: 300, y: 900, scale: 1.0, at: 0 });
      art(s, 'iceberg', { x: 720, y: 880, scale: 0.7, at: 0 });
      hero(s, { x: 540, ...stand(s, 0.8), scale: 1.3, outline: '#ffffff', look: ME,
        moves: [{ at: 0, pose: 'stand', face: 'wow' }] });
    } else {
      // close: lifeboats on deck, label ONE‑THIRD above them
      place(s, 'titanic_deck_night', { shot: 'close', focus: 0.3, mood: 'night' });
      art(s, 'lifeboat', { x: 460, y: 1150, scale: 0.9, at: 0 });
      art(s, 'lifeboat', { x: 620, y: 1150, scale: 0.9, at: 0 });
      label(s, 'ONE‑THIRD', { x: 540, y: 1000, size: 80, color: 'yellow', at: 'one-third' });
      hero(s, { x: 540, ...stand(s, 0.8), scale: 1.4, outline: '#ffffff', look: ME,
        moves: [{ at: 0, pose: 'stand', face: 'neutral' }] });
    }
    words(s);
  },

  step3(s) {
    const k = cut(s, ['deck', 'freezing', 'water']);
    if (k === 0) {
      // medium: raised poop deck, water rising, icy surface hinted by snowflake
      place(s, 'titanic_deck_night', { shot: 'medium', mood: 'cold' });
      waterRise(s, { from: 1920, to: 1300, at: 'water', until: 'water' });
      emoji(s, 'snowflake', { x: 540, y: 1240, size: 200, at: 0 });
      hero(s, { x: 540, ...stand(s, 0.8), scale: 1.3, outline: '#ffffff', look: ME,
        moves: [{ at: 0, pose: 'stand', face: 'neutral' }] });
    } else {
      // close: hero plunges into freezing water, splash effect
      place(s, 'titanic_deck_night', { shot: 'close', focus: 0.5, mood: 'cold' });
      hero(s, { x: 540, y: 1190, ...stand(s, 0.8), scale: 1.2, outline: '#ffffff', look: ME,
        moves: [{ at: 0, pose: 'fall', face: 'shocked' }] });
      bubbles(s, { x: 540, y: 1190, width: 200, n: 12, at: 0 });
      speedLines(s, { dir: 'down', at: 0 });
    }
    words(s);
  },

  answer(s) {
    const k = cut(s, ['cold', 'breathing', 'heart']);
    // single shot illustrating all three effects
    background(s, 'deep_sea');
    hero(s, { x: 540, y: 1100, ...stand(s, 0.8), scale: 1.2, outline: '#ffffff', look: ME,
      moves: [{ at: 0, pose: 'float', face: 'scared' }] });
    // label for the word "cold"
    label(s, 'COLD', { x: 760, y: 300, size: 80, color: 'red', at: 'cold' });
    // breathing illustration
    emoji(s, 'lungs', { x: 440, y: 950, size: 150, at: 'breathing' });
    // heart strain illustration
    glow(s, { x: 640, y: 950, r: 80, color: '255,0,0', pulse: true, at: 'heart' });
    words(s);
  },

  end(s) {
    const k = cut(s, ['lifeboats']);
    // close on a lifeboat with hero thinking
    place(s, 'titanic_deck_night', { shot: 'close', focus: 0.3, mood: 'night' });
    art(s, 'lifeboat', { x: 540, y: 1150, scale: 1.0, at: 0 });
    hero(s, { x: 440, ...stand(s, 0.8), scale: 1.4, outline: '#ffffff', look: ME,
      moves: [{ at: 0, pose: 'think', face: 'thinking' }] });
    label(s, 'LIFEBOATS?', { x: 540, y: 1000, size: 80, color: 'white', at: 'lifeboats' });
    words(s);
  },
};
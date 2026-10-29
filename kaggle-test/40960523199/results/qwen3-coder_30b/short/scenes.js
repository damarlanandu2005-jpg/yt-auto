import { BODIES, FACES, HAIRS, HATS, OUTFITS, POSES, crowd, hero } from './character.js';
import { THING_NAMES, art, background, blackHole, bubbles, cut, emoji, explosion, fire, floorY, glow, label, lava, pieces, place, smoke, speedLines, stand, stars, thing, waterRise, weather, words } from './props.js';
const ME = { outfit: 'passenger_1912', hat: 'bowler', hair: 'short' };

export default {
  hook(s) {
    const k = cut(s, ['iceberg']);
    if (k === 0) {  // wide: where we are
      place(s, 'titanic_deck_night', { shot: 'wide', mood: 'night' });
      hero(s, { x: 360, ...stand(s, 0.7), look: ME, moves: [{ at: 0, pose: 'walk', face: 'happy' }] });
    } else if (k === 1) {  // close: the feeling
      place(s, 'titanic_deck_night', { shot: 'close', focus: 0.3, mood: 'night' });
      hero(s, { x: 480, ...stand(s, 0.8), look: ME, moves: [{ at: 0, pose: 'point', face: 'shocked' }] });
      thing(s, 'iceberg', { x: 540, y: 1200, scale: 1.2, at: 'iceberg' });
    }
    words(s);
  },

  step1(s) {
    const k = cut(s, ['iceberg', 'above']);
    if (k === 0) {
      place(s, 'titanic_deck_night', { shot: 'wide', mood: 'night' });
      hero(s, { x: 360, ...stand(s, 0.7), look: ME, moves: [{ at: 0, pose: 'walk', face: 'happy' }] });
    } else {
      place(s, 'titanic_deck_night', { shot: 'medium', focus: 0.5, mood: 'night' });
      thing(s, 'iceberg', { x: 540, y: 1200, scale: 1.2, at: 'iceberg' });
      hero(s, { x: 300, ...stand(s, 0.8), look: ME, moves: [{ at: 0, pose: 'point', face: 'shocked' }] });
      label(s, '1/10 ABOVE', { x: 540, y: 200, size: 70, color: 'yellow', at: 'above' });
    }
    words(s);
  },

  step2(s) {
    const k = cut(s, ['strikes', 'foundering']);
    if (k === 0) {
      place(s, 'titanic_deck_night', { shot: 'wide', mood: 'night', flash: ['boom'] });
      hero(s, { x: 360, ...stand(s, 0.7), look: ME, moves: [{ at: 0, pose: 'shocked', face: 'scared' }] });
      thing(s, 'iceberg', { x: 540, y: 1200, scale: 1.2, at: 'strikes' });
    } else {
      place(s, 'ship_corridor', { shot: 'medium' });
      waterRise(s, { from: 1920, to: 1300, at: 'foundering', until: 'foundering' });
      hero(s, { x: 540, ...stand(s, 0.8), look: ME, moves: [{ at: 0, pose: 'run', face: 'scared' }] });
    }
    words(s);
  },

  step3(s) {
    const k = cut(s, ['poop', 'freezing']);
    if (k === 0) {
      place(s, 'titanic_deck_night', { shot: 'medium', mood: 'night' });
      hero(s, { x: 540, ...stand(s, 0.8), look: ME, moves: [{ at: 0, pose: 'look_up', face: 'worried' }] });
      thing(s, 'passenger_ship', { x: 540, y: 1200, size: 300, at: 'poop' });
    } else {
      place(s, 'titanic_deck_night', { shot: 'close', focus: 0.5, mood: 'night' });
      hero(s, { x: 540, ...stand(s, 0.8), look: ME, moves: [{ at: 0, pose: 'shocked', face: 'scared' }] });
      thing(s, 'wave', { x: 540, y: 1200, size: 200, at: 'freezing' });
      label(s, '-2°C', { x: 540, y: 200, size: 70, color: 'blue', at: 'freezing' });
    }
    words(s);
  },

  answer(s) {
    const k = cut(s, ['cold', 'incapacitation']);
    if (k === 0) {
      place(s, 'titanic_deck_night', { shot: 'medium', mood: 'night' });
      hero(s, { x: 540, ...stand(s, 0.8), look: ME, moves: [{ at: 0, pose: 'scared', face: 'scared' }] });
    } else {
      place(s, 'ocean_surface', { shot: 'close', mood: 'cold' });
      hero(s, { x: 540, ...stand(s, 0.8), look: ME, moves: [{ at: 0, pose: 'swim', face: 'pain' }] });
      label(s, 'INCAPACITATION', { x: 540, y: 200, size: 70, color: 'red', at: 'incapacitation' });
    }
    words(s);
  },

  end(s) {
    place(s, 'ocean_surface', { shot: 'medium' });
    hero(s, { x: 540, ...stand(s, 0.8), look: ME, moves: [{ at: 0, pose: 'think', face: 'thinking' }] });
    words(s);
  },
};
import { BODIES, FACES, HAIRS, HATS, OUTFITS, POSES, crowd, hero } from './character.js';
import { THING_NAMES, art, background, blackHole, bubbles, cut, emoji, explosion, fire, floorY, glow, label, lava, pieces, place, smoke, speedLines, stand, stars, thing, waterRise, weather, words } from './props.js';
const ME = { outfit: 'passenger_1912', hat: 'bowler', hair: 'short' };

export default {
  hook(s) {
    const k = cut(s, ['iceberg']);
    if (k === 0) {
      place(s, 'titanic_deck_night', { shot: 'medium', mood: 'night' });
      hero(s, { x: 480, ...stand(s, 0.8), look: ME, moves: [{ at: 0, pose: 'stand', face: 'neutral' }] });
    } else {
      place(s, 'titanic_deck_night', { shot: 'medium', focus: 0.8, mood: 'night' });
      art(s, 'iceberg', { x: 900, y: 800, scale: 1.5, at: 'iceberg' });
      hero(s, { x: 480, ...stand(s, 0.8), look: ME, moves: [{ at: 0, pose: 'look_up', face: 'shocked' }] });
    }
    words(s);
  },

  step1(s) {
    const k = cut(s, ['Typically']);
    if (k === 0) {
      place(s, 'ocean_surface', { shot: 'medium', mood: 'storm' });
      art(s, 'iceberg', { x: 900, y: 1100, scale: 1.5, at: 'Typically' });
      label(s, 'ONE-TENTH FLOATS', { x: 700, y: 300, size: 80, color: 'yellow', at: 'Typically' });
    } else {
      place(s, 'ship_corridor', { shot: 'medium', mood: 'dark' });
      waterRise(s, { from: 1920, to: 1300, at: 'Typically', until: 'Typically' });
      hero(s, { x: 480, ...stand(s, 0.8), look: ME, moves: [{ at: 0, pose: 'fall', face: 'worried' }] });
    }
    words(s);
  },

  step2(s) {
    const k = cut(s, ['lifeboats']);
    if (k === 0) {
      place(s, 'ship_corridor', { shot: 'medium', mood: 'dark' });
      waterRise(s, { from: 1920, to: 1300, at: -1, until: -1 });
      hero(s, { x: 480, ...stand(s, 0.8), look: ME, moves: [{ at: 0, pose: 'fall', face: 'worried' }] });
    } else {
      place(s, 'titanic_deck_night', { shot: 'medium', focus: 0.8, mood: 'night' });
      art(s, 'lifeboat', { x: 900, y: 1100, scale: 1.0, at: 'lifeboats' });
      crowd(s, { n: 4, x0: 560, x1: 980, ...stand(s, 0.35), seed: 11, outfits: ['passenger_1912', 'tshirt', 'worker'], faces: ['scared', 'shocked'], poses: ['panic'] });
      hero(s, { x: 480, ...stand(s, 0.8), look: ME, moves: [{ at: 0, pose: 'point', face: 'scared' }] });
    }
    words(s);
  },

  step3(s) {
    const k = cut(s, ['plunged']);
    if (k === 0) {
      place(s, 'titanic_deck_night', { shot: 'medium', focus: 0.8, mood: 'night' });
      hero(s, { x: 480, ...stand(s, 0.8), look: ME, moves: [{ at: 0, pose: 'point', face: 'scared' }] });
    } else {
      place(s, 'ocean_surface', { shot: 'medium', focus: 0.8, mood: 'storm' });
      hero(s, { x: 480, ...stand(s, 0.8), look: ME, at: 'plunged', moves: [{ at: 0, pose: 'float', face: 'shocked' }] });
      thing(s, 'wave', { x: 480, y: 1200, size: 400, at: 'plunged' });
    }
    words(s);
  },

  answer(s) {
    const k = cut(s, ['gasping']);
    if (k === 0) {
      place(s, 'ocean_surface', { shot: 'medium', focus: 0.8, mood: 'storm' });
      hero(s, { x: 480, ...stand(s, 0.8), look: ME, at: -1, moves: [{ at: 0, pose: 'float', face: 'shocked' }] });
    } else {
      place(s, 'ocean_surface', { shot: 'medium', focus: 0.8, mood: 'storm' });
      hero(s, { x: 480, ...stand(s, 0.8), look: ME, at: 'gasping', moves: [{ at: 0, pose: 'float', face: 'pain' }] });
      label(s, 'COLD SHOCK', { x: 700, y: 300, size: 80, color: 'yellow', at: 'gasping' });
    }
    words(s);
  },

  end(s) {
    place(s, 'ocean_surface', { shot: 'medium', focus: 0.8, mood: 'storm' });
    hero(s, { x: 300, ...stand(s, 0.8), look: ME, at: -1, moves: [{ at: 0, pose: 'think', face: 'thinking' }] });
    words(s);
  },
};
import { hero, crowd } from './character.js';
import { place, stand, cut, art, waterRise, label, words, speedLines, bubbles, s } from './props.js';

const ME = { outfit: 'passenger_1912', hat: 'bowler', hair: 'short' };

export default {
  hook(s) {
    const k = cut(s, ['Titanic', 'struck', 'iceberg']);
    if (k === 0) { // wide: Titanic deck
      place(s, 'titanic_deck_night', { shot: 'wide', mood: 'night' });
      hero(s, { x: 320, ...stand(s, 0.6), look: ME, moves: [{ at: 0, pose: 'walk', face: 'happy' }] });
    } else if (k === 1) { // medium: impact point
      place(s, 'titanic_deck_night', { shot: 'medium', focus: 0.4, mood: 'night' });
      hero(s, { x: 540, ...stand(s, 0.8), look: ME, moves: [{ at: 0, pose: 'point', face: 'shocked' }] });
      label(s, 'STRUCK', { x: 720, y: 300, size: 80, color: 'yellow', at: 'struck' });
    } else { // close: iceberg looming
      place(s, 'ocean_surface', { shot: 'close', mood: 'storm' });
      art(s, 'iceberg', { x: 540, y: 1080, scale: 1.2, at: 'iceberg' });
      hero(s, { x: 540, ...stand(s, 0.8), look: ME, moves: [{ at: 0, pose: 'think', face: 'wow' }] });
    }
    words(s);
  },

  step1(s) {
    const k = cut(s, ['iceberg', 'floats', 'water']);
    if (k === 0) { // wide: massive iceberg
      place(s, 'ocean_surface', { shot: 'wide', mood: 'storm' });
      art(s, 'iceberg', { x: 540, y: 1000, scale: 2.0, at: 'iceberg' });
      hero(s, { x: 300, ...stand(s, 0.6), look: ME, moves: [{ at: 0, pose: 'stand', face: 'neutral' }] });
    } else if (k === 1) { // medium: tip above water
      place(s, 'ocean_surface', { shot: 'medium', focus: 0.5, mood: 'storm' });
      art(s, 'iceberg', { x: 540, y: 1150, scale: 1.5, at: 'floats' });
      hero(s, { x: 540, ...stand(s, 0.8), look: ME, moves: [{ at: 0, pose: 'think', face: 'wow' }] });
      label(s, 'ONE‑TENTH', { x: 720, y: 300, size: 70, color: 'white', at: 'floats' });
    } else { // close: water line illustration
      place(s, 'ocean_surface', { shot: 'close', mood: 'storm' });
      art(s, 'iceberg', { x: 540, y: 1240, scale: 1.2, at: 'water' });
      waterRise(s, { from: 1920, to: 1240, at: 'water', until: 'water' });
      hero(s, { x: 540, ...stand(s, 0.8), look: ME, moves: [{ at: 0, pose: 'point', face: 'wow' }] });
    }
    words(s);
  },

  step2(s) {
    const k = cut(s, ['strikes', 'foundering', 'lifeboats', 'people']);
    if (k === 0) { // collision
      place(s, 'titanic_deck_night', { shot: 'wide', mood: 'night' });
      art(s, 'ship_front_half', { x: 400, y: 900, scale: 1.2, at: 'strikes' });
      art(s, 'iceberg', { x: 800, y: 1100, scale: 1.5, at: 'strikes' });
      hero(s, { x: 460, ...stand(s, 0.8), look: ME, moves: [{ at: 0, pose: 'point', face: 'shocked' }] });
    } else if (k === 1) { // water flooding
      place(s, 'titanic_deck_night', { shot: 'medium', mood: 'night' });
      hero(s, { x: 540, ...stand(s, 0.8), look: ME, moves: [{ at: 0, pose: 'shiver', face: 'worried' }] });
      waterRise(s, { from: 1920, to: 1300, at: 'foundering', until: 'foundering' });
    } else if (k === 2) { // lifeboats crowded on water
      place(s, 'ocean_surface', { shot: 'medium', mood: 'storm' });
      art(s, 'lifeboat_crowded', { x: 300, y: 1150, scale: 1.0, at: 'lifeboats' });
      art(s, 'lifeboat_crowded', { x: 780, y: 1150, scale: 1.0, at: 'lifeboats' });
      hero(s, { x: 540, ...stand(s, 0.8), look: ME, moves: [{ at: 0, pose: 'sad', face: 'sad' }] });
    } else { // panicked crowd
      place(s, 'titanic_deck_night', { shot: 'close', focus: 0.5, mood: 'night' });
      crowd(s, { n: 6, x0: 200, x1: 880, ...stand(s, 0.35), seed: 7,
        outfits: ['passenger_1912'], faces: ['scared', 'shocked'], poses: ['panic'] });
      hero(s, { x: 540, ...stand(s, 0.8), look: ME, moves: [{ at: 0, pose: 'run', face: 'scared' }] });
      speedLines(s, { dir: 'side', at: 'people' });
    }
    words(s);
  },

  step3(s) {
    const k = cut(s, ['passengers', 'deck', 'plunged', 'freezing']);
    if (k === 0) { // last stand on poop deck
      place(s, 'titanic_deck_night', { shot: 'medium', focus: 0.3, mood: 'night' });
      hero(s, { x: 540, ...stand(s, 0.8), look: ME, moves: [{ at: 0, pose: 'stand', face: 'determined' }] });
      crowd(s, { n: 4, x0: 250, x1: 830, ...stand(s, 0.4), seed: 3,
        outfits: ['passenger_1912'], faces: ['sad', 'scared'], poses: ['stand'] });
    } else if (k === 1) { // close view of raised deck
      place(s, 'titanic_deck_night', { shot: 'close', focus: 0.6, mood: 'night' });
      hero(s, { x: 540, ...stand(s, 0.8), look: ME, moves: [{ at: 0, pose: 'point', face: 'sad' }] });
      label(s, 'POOP DECK', { x: 720, y: 300, size: 70, color: 'white', at: 'deck' });
    } else if (k === 2) { // plunge into icy water
      place(s, 'ocean_surface', { shot: 'wide', mood: 'storm' });
      hero(s, { x: 540, y: 780, scale: 1.2, outline: '#ffffff', look: ME,
        moves: [{ at: 0, pose: 'fall', face: 'shocked' }],
        move: { to: [540, 1400], at: 'plunged', until: 'plunged' } });
      waterRise(s, { from: 1920, to: 1080, at: 'plunged', until: 'plunged' });
    } else { // freezing water effect
      place(s, 'ocean_surface', { shot: 'close', mood: 'storm' });
      hero(s, { x: 540, y: 1240, scale: 1.0, outline: '#ffffff', look: ME,
        moves: [{ at: 0, pose: 'float', face: 'cold' }] });
      bubbles(s, { x: 540, y: 1240, width: 300, n: 12, at: 'freezing' });
    }
    words(s);
  },

  answer(s) {
    const k = cut(s, ['cold', 'breathing', 'heart', 'minutes', 'swimming']);
    if (k === 0) { // cold shock
      place(s, 'ocean_surface', { shot: 'medium', mood: 'storm' });
      hero(s, { x: 540, y: 1100, scale: 1.1, outline: '#ffffff', look: ME,
        moves: [{ at: 0, pose: 'shiver', face: 'shocked' }] });
      label(s, 'COLD', { x: 720, y: 260, size: 80, color: 'red', at: 'cold' });
    } else if (k === 1) { // rapid breathing
      place(s, 'ocean_surface', { shot: 'close', mood: 'storm' });
      hero(s, { x: 540, y: 1150, scale: 1.0, outline: '#ffffff', look: ME,
        moves: [{ at: 0, pose: 'think', face: 'worried' }] });
      s.arrow([540, 1080], [540, 1000], { color: 'blue', width: 12, bend: 0.2, at: 'breathing' });
    } else if (k === 2) { // heart strain
      place(s, 'ocean_surface', { shot: 'medium', mood: 'storm' });
      art(s, 'heart_monitor', { x: 540, y: 800, scale: 0.9, at: 'heart' });
    } else if (k === 3) { // minutes counting
      place(s, 'ocean_surface', { shot: 'close', mood: 'storm' });
      s.number(20, { x: 540, y: 900, size: 120, suffix: ' min', at: 'minutes' });
    } else { // unable to swim
      place(s, 'ocean_surface', { shot: 'medium', mood: 'storm' });
      hero(s, { x: 540, y: 1240, scale: 0.9, outline: '#ffffff', look: ME,
        moves: [{ at: 0, pose: 'float', face: 'sad' }] });
      speedLines(s, { dir: 'down', at: 'swimming' });
    }
    words(s);
  },

  end(s) {
    const k = cut(s, ['lifeboats']);
    // single shot showing a lifeboat with few spots left
    place(s, 'titanic_deck_night', { shot: 'medium', focus: 0.5, mood: 'night' });
    art(s, 'lifeboat', { x: 540, y: 1150, scale: 1.0, at: 'lifeboats' });
    hero(s, { x: 540, ...stand(s, 0.8), look: ME,
      moves: [{ at: 0, pose: 'think', face: 'thinking' }] });
    label(s, 'LIFEBOATS?', { x: 720, y: 300, size: 80, color: 'yellow', at: 'lifeboats' });
    words(s);
  },
};
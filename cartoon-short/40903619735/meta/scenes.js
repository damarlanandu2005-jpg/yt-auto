import { hero, crowd } from './character.js';
import { place, stand, cut, art, label, waterRise, words } from './props.js';

const ME = { outfit: 'passenger_1912', hat: 'bowler', hair: 'short' };

export default {
  hook(s) {
    const k = cut(s, ['Titanic', 'iceberg']);
    if (k === 0) {
      // wide: where we are on the deck
      place(s, 'titanic_deck_night', { shot: 'wide', mood: 'night' });
      hero(s, {
        x: 340,
        ...stand(s, 0.7),
        look: ME,
        moves: [{ at: 0, pose: 'walk', face: 'happy' }],
        at: 0,
      });
    } else {
      // close: the looming iceberg
      place(s, 'titanic_deck_night', { shot: 'close', focus: 0.4, mood: 'night' });
      art(s, 'iceberg', { x: 720, y: 1000, scale: 1.2, at: 0 });
      hero(s, {
        x: 460,
        ...stand(s, 0.8),
        look: ME,
        moves: [{ at: 0, pose: 'point', face: 'shocked' }],
        at: 0,
      });
      label(s, 'ICEBERG', { x: 800, y: 300, size: 70, color: 'yellow', at: 0 });
    }
    words(s);
  },

  step1(s) {
    const k = cut(s, ['iceberg', 'floats']);
    if (k === 0) {
      // wide: iceberg in the Arctic
      place(s, 'arctic_ice', { shot: 'wide', mood: 'cold' });
      art(s, 'iceberg', { x: 540, y: 900, scale: 1.5, at: 0 });
      hero(s, {
        x: 200,
        ...stand(s, 0.5),
        look: ME,
        moves: [{ at: 0, pose: 'stand', face: 'neutral' }],
        at: 0,
      });
    } else {
      // close: how much is above water
      place(s, 'arctic_ice', { shot: 'close', focus: 0.3, mood: 'cold' });
      art(s, 'iceberg', { x: 540, y: 950, scale: 1.5, at: 0 });
      label(s, 'ONE TENTH', { x: 800, y: 300, size: 70, color: 'yellow', at: 0 });
      hero(s, {
        x: 300,
        ...stand(s, 0.6),
        look: ME,
        moves: [{ at: 0, pose: 'think', face: 'thinking' }],
        at: 0,
      });
    }
    words(s);
  },

  step2(s) {
    const k = cut(s, ['strikes', 'lifeboats']);
    if (k === 0) {
      // medium: Titanic collides with iceberg
      place(s, 'titanic_deck_night', { shot: 'medium', mood: 'night' });
      art(s, 'ship_front_half', { x: 300, y: 1100, scale: 1.2, at: 0 });
      art(s, 'iceberg', { x: 800, y: 1000, scale: 1.2, at: 0 });
      hero(s, {
        x: 420,
        ...stand(s, 0.8),
        look: ME,
        moves: [{ at: 0, pose: 'point', face: 'shocked' }],
        at: 0,
      });
    } else {
      // medium: lifeboats are insufficient
      place(s, 'titanic_deck_night', { shot: 'medium', mood: 'night' });
      art(s, 'lifeboat_crowded', { x: 540, y: 1150, scale: 1.0, at: 0 });
      crowd(s, {
        n: 5,
        x0: 200,
        x1: 880,
        ...stand(s, 0.3),
        seed: 7,
        outfits: ['passenger_1912', 'dress'],
        faces: ['scared', 'shocked'],
        poses: ['panic'],
        at: 0,
      });
      hero(s, {
        x: 540,
        ...stand(s, 0.8),
        look: ME,
        moves: [{ at: 0, pose: 'sad', face: 'sad' }],
        at: 0,
      });
      label(s, 'LIFEBOATS', { x: 800, y: 300, size: 70, color: 'white', at: 0 });
    }
    words(s);
  },

  step3(s) {
    const k = cut(s, ['poop deck', 'freezing']);
    if (k === 0) {
      // medium: last stand on the poop deck
      place(s, 'titanic_deck_night', { shot: 'medium', focus: 0.6, mood: 'night' });
      label(s, 'POOP DECK', { x: 540, y: 300, size: 80, color: 'white', at: 0 });
      hero(s, {
        x: 540,
        ...stand(s, 0.8),
        look: ME,
        moves: [{ at: 0, pose: 'stand', face: 'worried' }],
        at: 0,
      });
      crowd(s, {
        n: 4,
        x0: 250,
        x1: 830,
        ...stand(s, 0.4),
        seed: 3,
        outfits: ['passenger_1912', 'dress'],
        faces: ['sad', 'scared'],
        poses: ['stand'],
        at: 0,
      });
    } else {
      // close: freezing water rushes in
      place(s, 'titanic_deck_night', { shot: 'close', mood: 'cold' });
      waterRise(s, { from: 1920, to: 1300, at: 'water', until: 'water' });
      hero(s, {
        x: 540,
        ...stand(s, 0.8),
        look: ME,
        move: { to: [540, 1500], at: 'water' },
        moves: [{ at: 0, pose: 'fall', face: 'shocked' }],
        at: 0,
      });
      // no label here – the word "freezing" is already shown by the water effect
    }
    words(s);
  },

  answer(s) {
    const k = cut(s, ['cold', 'breathing', 'incapacitation']);
    if (k === 0) {
      // close: cold shock, hero shivers
      place(s, 'titanic_deck_night', { shot: 'close', mood: 'cold' });
      hero(s, {
        x: 540,
        ...stand(s, 0.8),
        look: ME,
        moves: [{ at: 0, pose: 'shiver', face: 'cold' }],
        at: 0,
      });
    } else if (k === 1) {
      // close: gasping for breath, label BREATHING
      place(s, 'titanic_deck_night', { shot: 'close', mood: 'cold' });
      label(s, 'BREATHING', { x: 540, y: 300, size: 70, color: 'white', at: 0 });
      hero(s, {
        x: 540,
        ...stand(s, 0.8),
        look: ME,
        moves: [{ at: 0, pose: 'cover_ears', face: 'shocked' }],
        at: 0,
      });
      art(s, 'heart_monitor', { x: 800, y: 900, scale: 0.8, at: 0 });
    } else {
      // close: incapacitation, limb muscles shut down
      place(s, 'titanic_deck_night', { shot: 'close', mood: 'cold' });
      hero(s, {
        x: 540,
        ...stand(s, 0.8),
        look: ME,
        moves: [{ at: 0, pose: 'sad', face: 'sad' }],
        at: 0,
      });
    }
    words(s);
  },

  end(s) {
    const k = cut(s, ['lifeboats']);
    // single shot: would you have a place in a lifeboat?
    place(s, 'titanic_deck_night', { shot: 'medium', mood: 'night' });
    art(s, 'lifeboat_crowded', { x: 540, y: 1150, scale: 1.0, at: 0 });
    hero(s, {
      x: 540,
      ...stand(s, 0.8),
      look: ME,
      moves: [{ at: 0, pose: 'think', face: 'thinking' }],
      at: 0,
    });
    label(s, 'LIFEBOATS', { x: 540, y: 300, size: 80, color: 'white', at: 0 });
    words(s);
  },
};
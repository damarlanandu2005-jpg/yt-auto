import { hero, crowd } from './character.js';
import { place, stand, cut, thing, art, waterRise, label, words, emoji, background } from './props.js';

const ME = { outfit: 'passenger_1912', hat: 'bowler', hair: 'short' };

export default {
  hook(s) {
    const k = cut(s, ['titanic', 'sink']);
    if (k === 0) {
      // wide view of the deck, night sky
      place(s, 'titanic_deck_night', { shot: 'wide', mood: 'night' });
      hero(s, {
        x: 340,
        ...stand(s, 0.7),
        look: ME,
        at: 0,
        moves: [{ at: 0, pose: 'walk', face: 'happy' }]
      });
    } else {
      // close‑up on the hero, ocean behind
      place(s, 'titanic_deck_night', { shot: 'close', focus: 0.4, mood: 'night' });
      hero(s, {
        x: 540,
        ...stand(s, 0.8),
        look: ME,
        at: 0,
        moves: [{ at: 0, pose: 'think', face: 'thinking' }]
      });
    }
    words(s);
  },

  step1(s) {
    const k = cut(s, ['iceberg', 'lifeboats']);
    if (k === 0) {
      // iceberg in the distance, hero points
      place(s, 'titanic_deck_night', { shot: 'wide' });
      thing(s, 'iceberg', { x: 800, y: 600, size: 320, at: 0 });
      hero(s, {
        x: 260,
        ...stand(s, 0.7),
        look: ME,
        at: 0,
        moves: [{ at: 0, pose: 'point', face: 'shocked' }]
      });
    } else {
      // lifeboats on deck, label the capacity
      place(s, 'titanic_deck_night', { shot: 'medium' });
      art(s, 'lifeboat_crowded', { x: 540, y: 1180, scale: 1.2, at: 0 });
      label(s, '1,178', { x: 540, y: 1080, size: 80, color: 'white', at: 0 });
      hero(s, {
        x: 460,
        ...stand(s, 0.8),
        look: ME,
        at: 0,
        moves: [{ at: 0, pose: 'point', face: 'shocked' }]
      });
    }
    words(s);
  },

  step2(s) {
    const k = cut(s, ['rear', 'water']);
    if (k === 0) {
      // rear poop deck crowded, ship tilting
      place(s, 'titanic_deck_night', { shot: 'wide', focus: 0.9 });
      crowd(s, {
        n: 6,
        x0: 120,
        x1: 960,
        y: 1500,
        scale: 0.8,
        depth: 30,
        seed: 3,
        outfits: ['passenger_1912', 'dress'],
        faces: ['scared', 'shocked'],
        poses: ['panic'],
        outline: '#ffffff',
        at: 0
      });
      hero(s, {
        x: 540,
        ...stand(s, 0.8),
        look: ME,
        at: 0,
        moves: [{ at: 0, pose: 'stand', face: 'shocked' }]
      });
    } else {
      // water rising, hero about to plunge
      place(s, 'titanic_deck_night', { shot: 'medium', mood: 'cold' });
      waterRise(s, { from: 1920, to: 1300, at: 0, until: 'water' });
      hero(s, {
        x: 540,
        ...stand(s, 0.8),
        look: ME,
        at: 0,
        moves: [{ at: 0, pose: 'fall', face: 'scared' }]
      });
      emoji(s, 'snowflake', { x: 720, y: 900, size: 140, at: 0 });
    }
    words(s);
  },

  answer(s) {
    const k = cut(s, ['cold', 'incapacitation']);
    if (k === 0) {
      // underwater, hero stiff in icy water
      background(s, 'deep_sea');
      hero(s, {
        x: 540,
        y: 1100,
        scale: 1.2,
        look: ME,
        at: 0,
        moves: [{ at: 0, pose: 'sad', face: 'sad' }]
      });
      // ice crystals around the hero
      for (let i = 0; i < 5; i++) {
        const dx = -200 + i * 100;
        const dy = 800 + i * 30;
        emoji(s, 'snowflake', { x: 540 + dx, y: dy, size: 100, at: 0 });
      }
      label(s, 'COLD', { x: 540, y: 300, size: 90, color: 'red', at: 0 });
    } else {
      // same view, emphasize loss of movement
      background(s, 'deep_sea');
      hero(s, {
        x: 540,
        y: 1100,
        scale: 1.2,
        look: ME,
        at: 0,
        moves: [{ at: 0, pose: 'float', face: 'worried' }]
      });
      // no label here – only one label per scene
    }
    words(s);
  },

  end(s) {
    // underwater wreck of the Titanic, hero thinking
    place(s, 'deep_sea', { shot: 'medium', mood: 'dark' });
    art(s, 'ship_wreck', { x: 540, y: 1300, scale: 1.6, at: 0 });
    hero(s, {
      x: 540,
      ...stand(s, 0.8),
      look: ME,
      at: 0,
      moves: [{ at: 0, pose: 'think', face: 'thinking' }]
    });
    label(s, 'THE SINKING', { x: 540, y: 300, size: 90, color: 'white', at: 0 });
    words(s);
  }
};
// Render test for the picture library with camera shots (wide / medium / close), stand(), costumes and a crowd.
import { hero, crowd } from './character.js';
import { place, stand, art, words } from './props.js';

const ME = { outfit: 'passenger_1912', hat: 'bowler', hair: 'short' };

export default {
  deck(s) {
    place(s, 'titanic_deck_night', { shot: 'medium', mood: 'night' });
    crowd(s, { n: 4, x0: 560, x1: 980, ...stand(s, 0.3), seed: 5, outfits: ['passenger_1912', 'dress'],
      faces: ['neutral', 'happy'], poses: ['stand', 'walk'] });
    hero(s, { x: 330, ...stand(s, 0.85), look: ME, at: 0,
      moves: [{ at: 0, pose: 'walk', face: 'happy' }, { at: 'iceberg', pose: 'point', face: 'shocked' }] });
    words(s);
  },

  sea(s) {
    place(s, 'ocean_surface', { shot: 'wide', mood: 'night', flash: ['breaks'] });
    art(s, 'ship_front_half', { x: 330, y: 1200, size: 420, rotate: -12, at: 0, enter: 'none' });
    art(s, 'ship_back_half', { x: 790, y: 1220, size: 420, rotate: 14, at: 'breaks' });
    art(s, 'lifeboat_crowded', { x: 540, y: 1600, size: 260, at: 'lifeboat' });
    words(s);
  },

  room(s) {
    place(s, 'hospital_room', { shot: 'close', focus: 0.3 });
    hero(s, { x: 480, ...stand(s, 0.8), look: { outfit: 'hospital_gown', hair: 'short' }, at: 0,
      moves: [{ at: 0, pose: 'sad', face: 'sleepy' }, { at: 'hospital', pose: 'think', face: 'confused' }] });
    words(s);
  },
};

// Render test for the picture library (place, floorY, art) with several stickmen. Not a real Short.
import { hero } from './character.js';
import { place, floorY, art, words } from './props.js';

const EDGE = '#ffffff';

export default {
  deck(s) {
    place(s, 'titanic_deck_night');
    hero(s, { x: 300, y: floorY(s, 'titanic_deck_night', 0.9), scale: 1.6, outline: EDGE, at: 0,
      moves: [{ at: 0, pose: 'run', face: 'neutral' }, { at: 'iceberg', pose: 'point', face: 'shocked' }] });
    hero(s, { x: 760, y: floorY(s, 'titanic_deck_night', 0.25), scale: 0.9, outline: EDGE, flip: true, at: 0,
      moves: [{ at: 0, pose: 'stand', face: 'neutral' }, { at: 'iceberg', pose: 'scared', face: 'scared' }] });
    words(s);
  },

  sea(s) {
    place(s, 'ocean_surface', { mood: 'night', flash: ['breaks'] });
    art(s, 'ship_front_half', { x: 380, y: 1160, size: 420, rotate: -12, at: 0, enter: 'none' });
    art(s, 'ship_back_half', { x: 760, y: 1180, size: 420, rotate: 14, at: 'breaks' });
    art(s, 'lifeboat_crowded', { x: 540, y: 1560, size: 260, at: 'lifeboat' });
    words(s);
  },

  room(s) {
    place(s, 'hospital_room');
    hero(s, { x: 360, y: floorY(s, 'hospital_room', 0.8), scale: 1.5, outline: EDGE, at: 0,
      moves: [{ at: 0, pose: 'sad', face: 'confused' }, { at: 'hospital', pose: 'think', face: 'thinking' }] });
    words(s);
  },
};

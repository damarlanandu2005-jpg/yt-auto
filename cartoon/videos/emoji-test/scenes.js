// Render test for props.emoji() (Twemoji, owner's choice 29 Oct). Not a real Short.
import { hero } from './character.js';
import { background, emoji, words } from './props.js';

export default {
  hook(s) {
    background(s, 'ocean');
    emoji(s, 'whale', { x: 300, y: 380, size: 380, at: 0 });
    emoji(s, 'shark', { x: 760, y: 760, size: 360, at: 'shark', flip: true });
    hero(s, { x: 470, y: 1180, scale: 1.4, outline: '#ffffff', at: 0,
      moves: [{ at: 0, pose: 'shrug', face: 'wow' }, { at: 'shark', pose: 'scared', face: 'shocked' }] });
    words(s);
  },

  end(s) {
    background(s, 'land');
    emoji(s, 'volcano', { x: 280, y: 520, size: 320, at: 'volcano' });
    emoji(s, 't_rex', { x: 780, y: 760, size: 440, at: 'dinosaur', flip: true });
    hero(s, { x: 430, y: 1180, scale: 1.4, outline: '#ffffff', at: 0,
      moves: [{ at: 0, pose: 'scared', face: 'scared' }] });
    words(s);
  },
};

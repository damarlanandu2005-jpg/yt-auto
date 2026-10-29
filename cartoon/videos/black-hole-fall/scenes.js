// What happens if you fall into a black hole? Style test: one character (our astronaut) carries the story
// and shows the feeling; one idea per picture; pictures change on the words.
// Full 9:16 frame (owner, 29 Oct: use the whole screen like the big Shorts channels). Pictures sit between
// y = 150 and y = 1300; the one-word caption is at y = 1380; YouTube's own buttons cover the bottom and the
// right edge, so nothing important goes below 1450 or right of x = 930.
import { hero } from './character.js';
import { blackHole, stars, words } from './props.js';

const EDGE = '#ffffff'; // white sticker edge keeps the black-line character readable on dark space

// mix two #rrggbb colours, p = 0..1
function mix(a, b, p) {
  const n = (h, i) => parseInt(h.slice(1 + i * 2, 3 + i * 2), 16);
  const c = [0, 1, 2].map((i) => Math.round(n(a, i) + (n(b, i) - n(a, i)) * p));
  return `rgb(${c.join(',')})`;
}

export default {
  hook(s) {
    stars(s, { light: true, count: 70 });
    blackHole(s, { x: 540, y: 1080, r: 190, at: 0 , enter: 'none' });
    hero(s, {
      x: 540, y: 780, scale: 1.7, helmet: true, float: true, outline: EDGE, at: 0, enter: 'none',
      moves: [{ at: 0, pose: 'float', face: 'happy' }, { at: '#feet', pose: 'fall', face: 'scared' },
        { at: '#ask', pose: 'shrug', face: 'confused' }],
    });
    words(s);
  },

  stretch(s) {
    stars(s, { light: true, count: 70 });
    blackHole(s, { x: 540, y: 1230, r: 120, at: -1 });
    const k = () => 1 + 1.0 * s.p('#long', 2.2);
    hero(s, { x: 540, y: 1100, scale: 1.3, helmet: true, outline: EDGE, at: -1, stretch: k,
      moves: [{ at: 0, pose: 'fall', face: 'scared' }, { at: '#squeeze', pose: 'fall', face: 'shocked' }] });
    s.arrow([340, 780], [340, 1100], { color: 'red', width: 16, label: 'strong pull', labelSize: 60, at: 'feet' });
    s.arrow([340, 250], [340, 340], { color: 'muted', width: 8, label: 'weak pull', labelSize: 52, at: 'head' });
    s.arrow([900, 640], [680, 640], { color: 'blue', width: 14, at: '#squeeze' });
    s.arrow([180, 640], [400, 640], { color: 'blue', width: 14, at: s.mark('squeeze') + 0.15 });
    words(s);
  },

  name(s) {
    stars(s, { light: true, count: 70 });
    s.text('*spaghettification*', { y: 260, size: 100, font: 'display', at: '#word', enter: 'type', dur: 0.9 });
    s.icon('utensils', { x: 540, y: 440, size: 150, color: 'orange', at: s.mark('word') + 0.6 });
    s.note('a word made famous by Stephen Hawking', { y: 590, size: 54, at: '#hawking' });
    hero(s, { x: 540, y: 1300, scale: 0.85, helmet: true, outline: EDGE, at: -1, stretch: 2.0,
      moves: [{ at: 0, pose: 'fall', face: 'shocked' }, { at: '#hawking', pose: 'fall', face: 'sad' }] });
    words(s);
  },

  size(s) {
    stars(s, { light: true, count: 70 });
    s.text('SIZE CHANGES *EVERYTHING*', { y: 700, size: 100, font: 'display', maxWidth: 900, at: 0.2, out: '#small' });
    // small black hole: stretched before the edge
    s.text('small black hole', { x: 600, y: 210, size: 64, color: 'red', at: '#small' });
    blackHole(s, { x: 720, y: 470, r: 95, at: '#small' });
    hero(s, { x: 270, y: 640, scale: 0.6, helmet: true, outline: EDGE, at: '#small', stretch: () => 1 + 1.0 * s.p('#small', 2.5),
      moves: [{ at: 0, pose: 'fall', face: 'scared' }] });
    // giant black hole: you cross the edge calmly
    s.text('giant black hole', { x: 540, y: 780, size: 64, color: 'green', at: '#big' });
    blackHole(s, { x: 540, y: 1090, r: 175, at: '#big' });
    hero(s, { x: 540, y: 1060, scale: 0.75, helmet: true, float: true, outline: EDGE, at: s.mark('big') + 0.3,
      moves: [{ at: 0, pose: 'float', face: 'happy' }] });
    words(s);
  },

  outside(s) {
    stars(s, { light: true, count: 70 });
    blackHole(s, { x: 680, y: 1090, r: 170, at: 0.2 });
    // the friend, far away
    hero(s, { x: 230, y: 640, scale: 1.2, outline: EDGE, at: 0,
      moves: [{ at: 0, pose: 'point', face: 'neutral' }, { at: '#slow', pose: 'point', face: 'shocked' },
        { at: '#gone', pose: 'shrug', face: 'confused' }] });
    // you: the fall slows down near the edge, turns red and dim, then fades
    const fall = s.p(0.3, Math.max(1, s.mark('gone') - 0.3), 'out');
    hero(s, {
      x: 680, y: 640 + 260 * fall, scale: 0.8, helmet: true, outline: EDGE, at: 0.3,
      moves: [{ at: 0, pose: 'fall', face: 'scared' }],
      color: () => mix('#1d1d1f', '#d0342c', s.p('#red', 1.2)),
      alpha: () => 1 - 0.55 * s.p('#red', 1.2) - 0.45 * s.p('#gone', 1.2),
    });
    s.icon('hourglass', { x: 860, y: 420, size: 130, color: 'muted', at: '#slow', out: '#gone' });
    words(s);
  },

  trapped(s) {
    stars(s, { light: true, count: 70 });
    blackHole(s, { x: 540, y: 860, r: 320, at: 0 });
    hero(s, { x: 540, y: 990, scale: 0.9, helmet: true, at: 0.4, color: '#ffffff',
      moves: [{ at: 0, pose: 'scared', face: 'scared' }, { at: '#light', pose: 'sad', face: 'sad' }] });
    for (let i = 0; i < 3; i++) { // light tries to get out and bends back in
      const a = -0.9 + i * 0.9;
      s.arrow([540 + 60 * a, 700], [540 + 260 * a, 600], { bend: 1.2, color: 'yellow', dashed: true, width: 8, at: s.mark('light') + 0.2 * i });
    }
    s.text('NO WAY BACK', { y: 230, size: 120, font: 'display', color: 'red', at: 'back' });
    words(s);
  },
};

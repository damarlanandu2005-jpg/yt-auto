// What happens if you fall into a black hole? Style test: one character (our astronaut) carries the story
// and shows the feeling; one idea per picture; pictures change on the words.
import { hero } from './character.js';
import { blackHole, stars } from './props.js';

// mix two #rrggbb colours, p = 0..1
function mix(a, b, p) {
  const n = (h, i) => parseInt(h.slice(1 + i * 2, 3 + i * 2), 16);
  const c = [0, 1, 2].map((i) => Math.round(n(a, i) + (n(b, i) - n(a, i)) * p));
  return `rgb(${c.join(',')})`;
}

export default {
  hook(s) {
    stars(s);
    blackHole(s, { x: s.cx, y: 1130, r: 110, at: 0.2 });
    hero(s, {
      x: s.cx, y: 900, scale: 0.85, helmet: true, float: true, at: 0,
      moves: [{ at: 0, pose: 'float', face: 'happy' }, { at: '#feet', pose: 'fall', face: 'scared' },
        { at: '#ask', pose: 'shrug', face: 'confused' }],
    });
  },

  stretch(s) {
    stars(s);
    blackHole(s, { x: s.cx, y: 1180, r: 100, at: -1 });
    const k = () => 1 + 1.3 * s.p('#long', 2.2);
    hero(s, { x: s.cx, y: 1040, scale: 0.72, helmet: true, at: -1, stretch: k,
      moves: [{ at: 0, pose: 'fall', face: 'scared' }, { at: '#squeeze', pose: 'fall', face: 'shocked' }] });
    s.arrow([s.cx - 250, 860], [s.cx - 250, 1080], { color: 'red', width: 9, label: 'strong pull', labelSize: 40, at: 'feet' });
    s.arrow([s.cx - 250, 520], [s.cx - 250, 590], { color: 'muted', width: 5, label: 'weak pull', labelSize: 36, at: 'head' });
    s.arrow([s.cx + 300, 760], [s.cx + 110, 760], { color: 'blue', width: 7, at: '#squeeze' });
    s.arrow([s.cx - 300, 760], [s.cx - 110, 760], { color: 'blue', width: 7, at: s.mark('squeeze') + 0.15 });
  },

  name(s) {
    stars(s);
    s.text('*spaghetti*fication', { y: 400, size: 86, font: 'display', at: '#word', enter: 'type', dur: 0.9 });
    s.icon('utensils', { x: s.cx, y: 560, size: 110, color: 'orange', at: s.mark('word') + 0.6 });
    s.note('a word made famous by Stephen Hawking', { y: 680, size: 40, at: '#hawking' });
    hero(s, { x: s.cx, y: 1200, scale: 0.6, helmet: true, at: -1, stretch: 2.3,
      moves: [{ at: 0, pose: 'fall', face: 'shocked' }, { at: '#hawking', pose: 'fall', face: 'sad' }] });
  },

  size(s) {
    stars(s);
    s.text('SIZE CHANGES *EVERYTHING*', { y: 560, size: 64, font: 'display', at: 0.2, out: '#small' });
    // small black hole: stretched before the edge
    s.text('small black hole', { x: s.cx, y: 330, size: 44, color: 'red', at: '#small' });
    blackHole(s, { x: s.cx + 190, y: 560, r: 55, at: '#small' });
    hero(s, { x: s.cx - 120, y: 660, scale: 0.5, helmet: true, at: '#small', stretch: () => 1 + 1.6 * s.p('#small', 2.5),
      moves: [{ at: 0, pose: 'fall', face: 'scared' }] });
    // giant black hole: you cross the edge calmly
    s.text('giant black hole', { x: s.cx, y: 820, size: 44, color: 'green', at: '#big' });
    blackHole(s, { x: s.cx, y: 1090, r: 140, at: '#big' });
    hero(s, { x: s.cx, y: 1030, scale: 0.5, helmet: true, float: true, at: s.mark('big') + 0.3,
      moves: [{ at: 0, pose: 'float', face: 'happy' }] });
  },

  outside(s) {
    stars(s);
    blackHole(s, { x: s.cx + 130, y: 1100, r: 120, at: 0.2 });
    // the friend, far away
    hero(s, { x: s.cx - 240, y: 640, scale: 0.55, at: 0,
      moves: [{ at: 0, pose: 'point', face: 'neutral' }, { at: '#slow', pose: 'point', face: 'shocked' },
        { at: '#gone', pose: 'shrug', face: 'confused' }] });
    // you: the fall slows down near the edge, turns red and dim, then fades
    const fall = s.p(0.3, Math.max(1, s.mark('gone') - 0.3), 'out');
    hero(s, {
      x: s.cx + 130, y: 820 + 150 * fall, scale: 0.42, helmet: true, at: 0.3,
      moves: [{ at: 0, pose: 'fall', face: 'scared' }],
      color: () => mix('#1d1d1f', '#d0342c', s.p('#red', 1.2)),
      alpha: () => 1 - 0.55 * s.p('#red', 1.2) - 0.45 * s.p('#gone', 1.2),
    });
    s.icon('hourglass', { x: s.cx + 320, y: 860, size: 80, color: 'muted', at: '#slow', out: '#gone' });
  },

  trapped(s) {
    stars(s);
    blackHole(s, { x: s.cx, y: 820, r: 250, at: 0 });
    hero(s, { x: s.cx, y: 900, scale: 0.42, helmet: true, at: 0.4, color: '#ffffff',
      moves: [{ at: 0, pose: 'scared', face: 'scared' }, { at: '#light', pose: 'sad', face: 'sad' }] });
    for (let i = 0; i < 3; i++) { // light tries to get out and bends back in
      const a = -0.9 + i * 0.9;
      s.arrow([s.cx + 40 * a, 740], [s.cx + 170 * a, 660], { bend: 1.2, color: 'yellow', dashed: true, width: 5, at: s.mark('light') + 0.2 * i });
    }
    s.text('NO WAY BACK', { y: 420, size: 72, font: 'display', color: 'red', at: 'back' });
  },
};

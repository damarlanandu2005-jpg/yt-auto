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
  // Content stays between y = 300 and y = 1020: Shorts captions sit at about y = 1090 (run 40820948770).
  hook(s) {
    stars(s);
    blackHole(s, { x: s.cx, y: 900, r: 120, at: 0.2 });
    hero(s, {
      x: s.cx, y: 700, scale: 1.1, helmet: true, float: true, at: 0,
      moves: [{ at: 0, pose: 'float', face: 'happy' }, { at: '#feet', pose: 'fall', face: 'scared' },
        { at: '#ask', pose: 'shrug', face: 'confused' }],
    });
  },

  stretch(s) {
    stars(s);
    blackHole(s, { x: s.cx, y: 1000, r: 75, at: -1 });
    const k = () => 1 + 1.0 * s.p('#long', 2.2);
    hero(s, { x: s.cx, y: 900, scale: 0.85, helmet: true, at: -1, stretch: k,
      moves: [{ at: 0, pose: 'fall', face: 'scared' }, { at: '#squeeze', pose: 'fall', face: 'shocked' }] });
    s.arrow([s.cx - 270, 700], [s.cx - 270, 930], { color: 'red', width: 12, label: 'strong pull', labelSize: 50, at: 'feet' });
    s.arrow([s.cx - 270, 360], [s.cx - 270, 430], { color: 'muted', width: 6, label: 'weak pull', labelSize: 44, at: 'head' });
    s.arrow([s.cx + 340, 640], [s.cx + 130, 640], { color: 'blue', width: 10, at: '#squeeze' });
    s.arrow([s.cx - 340, 640], [s.cx - 130, 640], { color: 'blue', width: 10, at: s.mark('squeeze') + 0.15 });
  },

  name(s) {
    stars(s);
    s.text('*spaghettification*', { y: 360, size: 84, font: 'display', at: '#word', enter: 'type', dur: 0.9 });
    s.icon('utensils', { x: s.cx, y: 480, size: 110, color: 'orange', at: s.mark('word') + 0.6 });
    s.note('a word made famous by Stephen Hawking', { y: 590, size: 44, at: '#hawking' });
    hero(s, { x: s.cx, y: 1010, scale: 0.55, helmet: true, at: -1, stretch: 2.0,
      moves: [{ at: 0, pose: 'fall', face: 'shocked' }, { at: '#hawking', pose: 'fall', face: 'sad' }] });
  },

  size(s) {
    stars(s);
    s.text('SIZE CHANGES *EVERYTHING*', { y: 600, size: 70, font: 'display', at: 0.2, out: '#small' });
    // small black hole: stretched before the edge
    s.text('small black hole', { x: s.cx + 120, y: 410, size: 48, color: 'red', at: '#small' });
    blackHole(s, { x: s.cx + 200, y: 520, r: 65, at: '#small' });
    hero(s, { x: s.cx - 170, y: 640, scale: 0.42, helmet: true, at: '#small', stretch: () => 1 + 1.0 * s.p('#small', 2.5),
      moves: [{ at: 0, pose: 'fall', face: 'scared' }] });
    // giant black hole: you cross the edge calmly
    s.text('giant black hole', { x: s.cx, y: 720, size: 48, color: 'green', at: '#big' });
    blackHole(s, { x: s.cx, y: 940, r: 115, at: '#big' });
    hero(s, { x: s.cx, y: 930, scale: 0.5, helmet: true, float: true, at: s.mark('big') + 0.3,
      moves: [{ at: 0, pose: 'float', face: 'happy' }] });
  },

  outside(s) {
    stars(s);
    blackHole(s, { x: s.cx + 150, y: 910, r: 110, at: 0.2 });
    // the friend, far away
    hero(s, { x: s.cx - 250, y: 600, scale: 0.8, at: 0,
      moves: [{ at: 0, pose: 'point', face: 'neutral' }, { at: '#slow', pose: 'point', face: 'shocked' },
        { at: '#gone', pose: 'shrug', face: 'confused' }] });
    // you: the fall slows down near the edge, turns red and dim, then fades
    const fall = s.p(0.3, Math.max(1, s.mark('gone') - 0.3), 'out');
    hero(s, {
      x: s.cx + 150, y: 620 + 170 * fall, scale: 0.55, helmet: true, at: 0.3,
      moves: [{ at: 0, pose: 'fall', face: 'scared' }],
      color: () => mix('#1d1d1f', '#d0342c', s.p('#red', 1.2)),
      alpha: () => 1 - 0.55 * s.p('#red', 1.2) - 0.45 * s.p('#gone', 1.2),
    });
    s.icon('hourglass', { x: s.cx + 360, y: 620, size: 90, color: 'muted', at: '#slow', out: '#gone' });
  },

  trapped(s) {
    stars(s);
    blackHole(s, { x: s.cx, y: 760, r: 210, at: 0 });
    hero(s, { x: s.cx, y: 830, scale: 0.6, helmet: true, at: 0.4, color: '#ffffff',
      moves: [{ at: 0, pose: 'scared', face: 'scared' }, { at: '#light', pose: 'sad', face: 'sad' }] });
    for (let i = 0; i < 3; i++) { // light tries to get out and bends back in
      const a = -0.9 + i * 0.9;
      s.arrow([s.cx + 40 * a, 640], [s.cx + 180 * a, 570], { bend: 1.2, color: 'yellow', dashed: true, width: 6, at: s.mark('light') + 0.2 * i });
    }
    s.text('NO WAY BACK', { y: 410, size: 80, font: 'display', color: 'red', at: 'back' });
  },
};

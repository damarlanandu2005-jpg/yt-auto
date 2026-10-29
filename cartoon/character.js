// Our recurring character, drawn in code so he looks exactly the same in every scene and every video.
// Owner's study (29 Oct): channels like Flippo Explains and Captain Workout win with ONE simple character
// who shows the feeling (scared, floating, confused) and one idea per picture, not with fancy graphics.
//
// Use from an explainroo scenes.js:
//   import { hero } from './character.js';   (the workflow copies this file into the project folder)
//   hero(s, { x: 960, y: 900, at: 0, moves: [{ at: 0, pose: 'stand', face: 'happy' },
//                                           { at: 'falls', pose: 'fall', face: 'scared' }] });
// `moves` changes pose and face on a word or [#marker]; between poses the limbs swing smoothly.
// Everything depends only on the time (explainroo draws each frame fresh), never on stored state.

const BLACK = '#1d1d1f';
let INK = BLACK; // the line colour of the character being drawn (see the `color` option)
const SKIN = '#ffffff';
const RED = '#e5484d';
const GLASS = 'rgba(150, 200, 235, 0.28)';

// Body sizes in design pixels at scale 1 (feet at y = 0, so the character stands on `y`).
const L = { head: 66, body: 100, upper: 50, fore: 46, thigh: 54, shin: 52, width: 9, hand: 7 };

// Limb angles in degrees: 0 = hanging straight down, 90 = pointing right, -90 = left, 180 = straight up.
// Each limb is [upper part, lower part]. a = arms (left, right), g = legs. lean tilts the upper body.
export const POSES = {
  stand: { a: [[-24, -14], [24, 14]], g: [[-9, -4], [9, 4]], lean: 0 },
  wave: { a: [[-24, -14], [105, 125]], g: [[-9, -4], [9, 4]], lean: 0 },
  point: { a: [[-14, -8], [92, 90]], g: [[-9, -4], [9, 4]], lean: 4 },
  shrug: { a: [[-62, -150], [62, 150]], g: [[-9, -4], [9, 4]], lean: 0 },
  scared: { a: [[-48, -168], [48, 168]], g: [[-16, -4], [16, 4]], lean: -6 },
  think: { a: [[20, 70], [28, 165]], g: [[-9, -4], [9, 4]], lean: 0 },
  cheer: { a: [[-118, -128], [118, 128]], g: [[-14, -6], [14, 6]], lean: 0 },
  fall: { a: [[-108, -140], [104, 132]], g: [[-35, 15], [45, 10]], lean: -10 },
  float: { a: [[-100, -115], [100, 115]], g: [[-22, -32], [22, 32]], lean: 0 },
  run: { a: [[-45, 20], [50, 120]], g: [[-35, -10], [50, -20]], lean: 12 },
  sit: { a: [[-18, 30], [18, 50]], g: [[80, 2], [86, 6]], lean: -4 },
  sad: { a: [[-14, -6], [14, 6]], g: [[-6, -2], [6, 2]], lean: 8 },
};

// Faces: eyes ('dot' | 'big' | 'side'), brows [left, right] tilt (+ = inner end down = angry,
// - = inner end up = worried), brow height, mouth, and an extra mark next to the head.
export const FACES = {
  neutral: { eyes: 'dot', brows: [0, 0], lift: 0, mouth: 'line' },
  happy: { eyes: 'dot', brows: [-4, -4], lift: 4, mouth: 'smile' },
  wow: { eyes: 'big', brows: [-6, -6], lift: 10, mouth: 'grin' },
  scared: { eyes: 'big', brows: [-22, -22], lift: 6, mouth: 'wavy', mark: 'sweat', shake: 1.6 },
  shocked: { eyes: 'big', brows: [-10, -10], lift: 14, mouth: 'o', mark: '!' },
  confused: { eyes: 'dot', brows: [12, -14], lift: 4, mouth: 'squiggle', mark: '?' },
  thinking: { eyes: 'side', brows: [6, -8], lift: 2, mouth: 'flat' },
  sad: { eyes: 'dot', brows: [-20, -20], lift: 0, mouth: 'frown', mark: 'tear' },
  angry: { eyes: 'dot', brows: [24, 24], lift: -2, mouth: 'frown' },
};

const lerp = (a, b, p) => a + (b - a) * p;
const ease = (p) => (p < 0.5 ? 2 * p * p : 1 - Math.pow(-2 * p + 2, 2) / 2);
const rad = (d) => (d * Math.PI) / 180;
// a point `len` away from (x, y) at our angle convention (0 = down, 90 = right)
const step = (x, y, deg, len) => [x + Math.sin(rad(deg)) * len, y + Math.cos(rad(deg)) * len];

function blendPose(a, b, p) {
  const mix = (u, v) => u.map((limb, i) => limb.map((ang, j) => lerp(ang, v[i][j], p)));
  return { a: mix(a.a, b.a), g: mix(a.g, b.g), lean: lerp(a.lean, b.lean, p) };
}

// Where the character is in its list of moves at scene time t: the pose blended 0.35 s into the new one.
function current(s, moves, t) {
  const list = moves.map((m) => ({ ...m, t: typeof m.at === 'number' ? m.at : s.time(m.at) })).sort((m, n) => m.t - n.t);
  let i = 0;
  while (i + 1 < list.length && list[i + 1].t <= t) i++;
  const now = list[i];
  const before = list[Math.max(0, i - 1)];
  const p = i === 0 ? 1 : ease(Math.min(1, Math.max(0, (t - now.t) / 0.35)));
  const pa = POSES[before.pose || 'stand'];
  const pb = POSES[now.pose || 'stand'];
  if (!pa || !pb) throw new Error(`unknown pose "${now.pose}" (have: ${Object.keys(POSES).join(', ')})`);
  if (!FACES[now.face || 'neutral']) throw new Error(`unknown face "${now.face}" (have: ${Object.keys(FACES).join(', ')})`);
  return { pose: blendPose(pa, pb, p), face: FACES[now.face || 'neutral'], spin: now.spin || 0, since: t - now.t };
}

function limb(ctx, x, y, angles, lens) {
  const [ex, ey] = step(x, y, angles[0], lens[0]);
  const [hx, hy] = step(ex, ey, angles[1], lens[1]);
  ctx.beginPath();
  ctx.moveTo(x, y);
  ctx.lineTo(ex, ey);
  ctx.lineTo(hx, hy);
  ctx.stroke();
  if (lens.hand) {
    ctx.beginPath();
    ctx.fillStyle = INK;
    ctx.arc(hx, hy, lens.hand, 0, Math.PI * 2);
    ctx.fill();
  }
  return [hx, hy];
}

function face(ctx, f, R, t, blinkSeed) {
  ctx.save();
  ctx.scale(R / 46, R / 46);
  const r = 46;
  const blink = (t + blinkSeed) % 3.3 < 0.12;
  const ex = r * 0.36;
  const ey = -r * 0.12;
  ctx.fillStyle = INK;
  ctx.strokeStyle = INK;
  ctx.lineWidth = 4;
  for (const side of [-1, 1]) {
    const x = side * ex;
    if (blink) {
      ctx.beginPath();
      ctx.moveTo(x - 7, ey);
      ctx.lineTo(x + 7, ey);
      ctx.stroke();
    } else if (f.eyes === 'big') {
      ctx.beginPath();
      ctx.fillStyle = SKIN;
      ctx.arc(x, ey, 11, 0, Math.PI * 2);
      ctx.fill();
      ctx.stroke();
      ctx.beginPath();
      ctx.fillStyle = INK;
      ctx.arc(x, ey + 1, 4, 0, Math.PI * 2);
      ctx.fill();
    } else {
      const dx = f.eyes === 'side' ? 5 : 0;
      const dy = f.eyes === 'side' ? -4 : 0;
      ctx.beginPath();
      ctx.arc(x + dx, ey + dy, 5.5, 0, Math.PI * 2);
      ctx.fill();
    }
    // brow: tilt + means the inner end (towards the nose) is lower
    const by = ey - 20 - f.lift;
    const tilt = rad(f.brows[side < 0 ? 0 : 1]);
    const half = 11;
    ctx.beginPath();
    const inner = [x - side * half, by + Math.sin(tilt) * half];
    const outer = [x + side * half, by - Math.sin(tilt) * half];
    ctx.moveTo(inner[0], inner[1]);
    ctx.lineTo(outer[0], outer[1]);
    ctx.stroke();
  }
  const my = r * 0.38;
  ctx.beginPath();
  switch (f.mouth) {
    case 'smile': ctx.arc(0, my - 10, 14, rad(20), rad(160)); ctx.stroke(); break;
    case 'grin': ctx.moveTo(-15, my - 4); ctx.arc(0, my - 4, 15, 0, Math.PI); ctx.closePath(); ctx.fill(); break;
    case 'frown': ctx.arc(0, my + 10, 13, rad(205), rad(335)); ctx.stroke(); break;
    case 'o': ctx.ellipse(0, my, 8, 11, 0, 0, Math.PI * 2); ctx.fill(); break;
    case 'wavy':
      ctx.moveTo(-14, my);
      for (let i = 1; i <= 4; i++) ctx.lineTo(-14 + i * 7, my + (i % 2 ? -4 : 4));
      ctx.stroke();
      break;
    case 'squiggle': ctx.moveTo(-12, my + 2); ctx.quadraticCurveTo(-4, my - 6, 2, my + 1); ctx.quadraticCurveTo(8, my + 6, 13, my - 3); ctx.stroke(); break;
    case 'flat': ctx.moveTo(-4, my + 2); ctx.lineTo(12, my); ctx.stroke(); break;
    default: ctx.moveTo(-10, my); ctx.lineTo(10, my); ctx.stroke();
  }
  ctx.restore();
}

function mark(ctx, kind, r, t) {
  if (!kind) return;
  ctx.save();
  ctx.fillStyle = kind === 'tear' || kind === 'sweat' ? '#6cb4ee' : RED;
  ctx.strokeStyle = INK;
  ctx.lineWidth = 3;
  if (kind === 'sweat' || kind === 'tear') {
    const x = kind === 'sweat' ? r * 0.95 : r * 0.38;
    const y = kind === 'sweat' ? -r * 0.55 + (t * 30) % 18 : r * 0.05 + (t * 40) % 26;
    ctx.beginPath();
    ctx.moveTo(x, y - 12);
    ctx.quadraticCurveTo(x + 9, y + 2, x, y + 7);
    ctx.quadraticCurveTo(x - 9, y + 2, x, y - 12);
    ctx.fill();
    ctx.stroke();
  } else {
    ctx.font = `bold ${Math.round(r * 1.1)}px sans-serif`;
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    const bob = Math.sin(t * 5) * 4;
    ctx.fillText(kind, r * 1.35, -r * 1.05 + bob);
  }
  ctx.restore();
}

// Draw the character. Options: x, y (feet), scale, flip (face left), at, out, enter, moves, helmet (space),
// float (gentle up-down drift, for space), id, and three that may be numbers or functions of `s`:
// stretch (1 = normal; 2 = twice as tall and squeezed thin, for spaghettification), alpha (0-1), color (line colour),
// and outline: a colour for a thin 'sticker' edge around every line, so he stays readable on dark backgrounds.
export function hero(s, o = {}) {
  const moves = o.moves && o.moves.length ? o.moves : [{ at: 0, pose: o.pose || 'stand', face: o.face || 'neutral' }];
  const sc = o.scale ?? 1;
  const box = { x: o.x ?? s.cx, y: (o.y ?? s.cy + 250) - 150 * sc, w: 180 * sc, h: 330 * sc };
  s.draw({ x: o.x ?? s.cx, y: o.y ?? s.cy + 250, at: o.at ?? 0, out: o.out, enter: o.enter ?? 'fade', id: o.id }, (ctx) => {
    const t = s.t;
    const c = current(s, moves, t);
    const val = (v, d) => (typeof v === 'function' ? v(s) : v ?? d);
    const k = Math.max(0.2, val(o.stretch, 1));
    INK = val(o.color, BLACK);
    ctx.globalAlpha *= Math.max(0, Math.min(1, val(o.alpha, 1)));
    const shake = c.face.shake ? Math.sin(t * 60) * c.face.shake : 0;
    const drift = o.float ? Math.sin(t * 1.6) * 14 : Math.sin(t * 2.2) * 1.5; // breathing or floating
    ctx.save();
    ctx.translate(shake, drift);
    if (o.outline) { // four hard drop shadows = a thin outline (canvas filters ignore the transform: screen pixels)
      const w = 3;
      ctx.filter = [[w, 0], [-w, 0], [0, w], [0, -w]].map(([dx, dy]) => `drop-shadow(${dx}px ${dy}px 0 ${o.outline})`).join(' ');
    }
    ctx.scale((o.flip ? -sc : sc) / Math.sqrt(k), sc * k); // taller and thinner, same volume (Spaghettification article)
    if (c.spin) {
      ctx.translate(0, -150);
      ctx.rotate(rad(c.spin * c.since));
      ctx.translate(0, 150);
    }
    ctx.lineCap = 'round';
    ctx.lineJoin = 'round';
    ctx.strokeStyle = INK;
    ctx.lineWidth = L.width;
    const hip = [0, -(L.thigh + L.shin)];
    limb(ctx, hip[0], hip[1], c.pose.g[0], [L.thigh, L.shin]);
    limb(ctx, hip[0], hip[1], c.pose.g[1], [L.thigh, L.shin]);
    // upper body leans around the hip
    ctx.save();
    ctx.translate(hip[0], hip[1]);
    ctx.rotate(rad(c.pose.lean));
    const neck = [0, -L.body];
    if (o.helmet) { // small backpack behind the shoulders
      ctx.save();
      ctx.fillStyle = '#d9d9de';
      ctx.lineWidth = 5;
      ctx.beginPath();
      ctx.roundRect(-30, neck[1] + 6, 24, 54, 7);
      ctx.fill();
      ctx.stroke();
      ctx.restore();
    }
    ctx.beginPath();
    ctx.moveTo(0, 0);
    ctx.lineTo(neck[0], neck[1]);
    ctx.stroke();
    const shoulder = [0, neck[1] + 8];
    limb(ctx, shoulder[0], shoulder[1], c.pose.a[0], Object.assign([L.upper, L.fore], { hand: L.hand }));
    limb(ctx, shoulder[0], shoulder[1], c.pose.a[1], Object.assign([L.upper, L.fore], { hand: L.hand }));
    // head
    ctx.translate(0, neck[1] - L.head + 6);
    if (o.flip) ctx.scale(-1, 1); // keep the face and marks readable when he faces left
    ctx.beginPath();
    ctx.fillStyle = SKIN;
    ctx.lineWidth = 7;
    ctx.arc(0, 0, L.head, 0, Math.PI * 2);
    ctx.fill();
    ctx.stroke();
    face(ctx, c.face, L.head, t, (o.x ?? 0) % 1.7);
    if (o.helmet) {
      ctx.beginPath();
      ctx.fillStyle = GLASS;
      ctx.lineWidth = 5;
      ctx.arc(0, 4, L.head * 1.5, 0, Math.PI * 2);
      const edge = ctx.filter;
      ctx.filter = 'none'; // the outline shadows of a see-through fill stack up into solid white and hide the face
      ctx.fill();
      ctx.filter = edge;
      ctx.stroke();
      ctx.beginPath();
      ctx.strokeStyle = 'rgba(255,255,255,0.9)';
      ctx.lineWidth = 6;
      ctx.arc(0, 4, L.head * 1.22, rad(200), rad(250));
      ctx.filter = 'none';
      ctx.stroke();
      ctx.filter = edge;
      ctx.strokeStyle = INK;
    }
    mark(ctx, c.face.mark, L.head, t);
    ctx.restore();
    ctx.restore();
    INK = BLACK;
  });
  return box;
}

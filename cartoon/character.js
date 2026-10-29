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
let WIDEN = 0; // extra line width while drawing the outline pass
const SKIN = '#ffffff';
const RED = '#e5484d';
const GLASS = 'rgba(150, 200, 235, 0.28)';

// Body sizes in design pixels at scale 1 (feet at y = 0, so the character stands on `y`).
const L = { head: 66, body: 100, upper: 50, fore: 46, thigh: 54, shin: 52, width: 11, hand: 11 }; // thick lines, round hands: matches the channel logo (29 Oct)

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
  // 29 Oct, richer scenes like the owner's reference Shorts. Extra fields: rot = whole-body turn (deg, around the
  // middle of the body), dy = lower the whole body (px, e.g. kneeling), head = head tilt (deg). A function of the
  // time t gives a moving pose (walk, swim...).
  walk: (t) => { const w = Math.sin(t * 7); return { a: [[-14 - 18 * w, -8 - 10 * w], [14 + 18 * w, 8 + 10 * w]], g: [[26 * w, 26 * w - 6], [-26 * w, -26 * w - 6]], lean: 3 }; },
  sprint: (t) => { const w = Math.sin(t * 12); return { a: [[-10 - 60 * w, 60 - 40 * w], [10 + 60 * w, 60 + 40 * w]], g: [[45 * w, 45 * w - 40], [-45 * w, -45 * w - 40]], lean: 14 }; },
  swim: (t) => { const w = t * 6; return { a: [[180 * Math.sin(w) - 60, 180 * Math.sin(w) - 40], [180 * Math.sin(w + 3) + 60, 180 * Math.sin(w + 3) + 40]], g: [[-8 + 14 * Math.sin(w * 2), -4], [8 - 14 * Math.sin(w * 2), 4]], lean: 0, rot: 75, dy: 60 }; },
  climb: (t) => { const w = Math.sin(t * 5); return { a: [[-150 + 20 * w, -175], [150 + 20 * w, 175]], g: [[30 * w + 20, -10], [-30 * w - 20, 10]], lean: 0 }; },
  jump: (t) => { const k = Math.abs(Math.sin(t * 4)); return { a: [[-140, -160], [140, 160]], g: [[-20 - 20 * k, 30], [20 + 20 * k, -30]], lean: 0, dy: -70 * k }; },
  kneel: { a: [[-20, 20], [30, 60]], g: [[80, 0], [0, -90]], lean: 2, dy: 52 },
  crouch: { a: [[-40, 30], [40, -30]], g: [[-70, 70], [70, -70]], lean: 10, dy: 70 },
  lie: { a: [[-20, -10], [20, 10]], g: [[-6, -2], [6, 2]], lean: 0, rot: -90, dy: 96 },
  hold: { a: [[60, 85], [70, 95]], g: [[-9, -4], [9, 4]], lean: 2 },
  carry: { a: [[150, 175], [-150, -175]], g: [[-12, -4], [12, 4]], lean: 0 },
  push: { a: [[80, 92], [86, 96]], g: [[-30, -10], [24, 6]], lean: 20 },
  pull: { a: [[74, 88], [80, 92]], g: [[30, 10], [-6, -2]], lean: -18 },
  look_up: { a: [[-24, -14], [24, 14]], g: [[-9, -4], [9, 4]], lean: -6, head: -16 },
  look_down: { a: [[-24, -14], [24, 14]], g: [[-9, -4], [9, 4]], lean: 8, head: 16 },
  cover_ears: { a: [[-110, -164], [110, 164]], g: [[-9, -4], [9, 4]], lean: 0 },
  panic: (t) => { const w = Math.sin(t * 14); return { a: [[-140 - 25 * w, -170 + 30 * w], [140 - 25 * w, 170 + 30 * w]], g: [[-12, -4], [12, 4]], lean: 0 }; },
  shiver: (t) => ({ a: [[20, 120], [-20, -120]], g: [[-6, -2], [6, 2]], lean: 3, rot: Math.sin(t * 50) * 1.5 }),
  tumble: (t) => ({ a: [[-108, -140], [104, 132]], g: [[-35, 15], [45, 10]], lean: -10, rot: (t * 300) % 360 }),
};
const poseAt = (name, t) => { const p = POSES[name]; return typeof p === 'function' ? p(t) : p; };

// Faces: eyes ('dot' | 'big' | 'side'), brows [left, right] tilt (+ = inner end down = angry,
// - = inner end up = worried), brow height, mouth, and an extra mark next to the head.
export const FACES = {
  neutral: { eyes: 'dot', brows: [0, 0], lift: 0, mouth: 'line' },
  happy: { eyes: 'dot', brows: [-4, -4], lift: 4, mouth: 'smile' },
  wow: { eyes: 'big', brows: [-6, -6], lift: 10, mouth: 'grin' },
  scared: { eyes: 'big', brows: [-22, -22], lift: 6, mouth: 'wavy', mark: 'sweat', shake: 1.6 },
  shocked: { eyes: 'big', brows: [-10, -10], lift: 14, mouth: 'o', mark: '!' },
  confused: { eyes: 'dot', brows: [-14, 10], lift: 4, mouth: 'side', mark: '?' },
  thinking: { eyes: 'side', brows: [-14, 10], lift: 2, mouth: 'side', mark: 'lines' }, // the channel logo's face
  sad: { eyes: 'dot', brows: [-20, -20], lift: 0, mouth: 'frown', mark: 'tear' },
  angry: { eyes: 'dot', brows: [24, 24], lift: -2, mouth: 'frown' },
  worried: { eyes: 'dot', brows: [-20, -20], lift: 4, mouth: 'wavy' },
  crying: { eyes: 'closed', brows: [-22, -22], lift: 2, mouth: 'frown', mark: 'tears' },
  sweating: { eyes: 'big', brows: [-14, -14], lift: 6, mouth: 'flat', mark: 'sweat' },
  sleepy: { eyes: 'half', brows: [0, 0], lift: -2, mouth: 'small', mark: 'zzz' },
  smug: { eyes: 'half', brows: [10, -10], lift: 2, mouth: 'smirk' },
  determined: { eyes: 'dot', brows: [18, 18], lift: -2, mouth: 'flat' },
  disgusted: { eyes: 'squint', brows: [16, -8], lift: 0, mouth: 'wavy' },
  laughing: { eyes: 'closed', brows: [-6, -6], lift: 8, mouth: 'grin', shake: 0.8 },
  pain: { eyes: 'squint', brows: [20, 20], lift: -2, mouth: 'teeth', mark: 'sweat' },
  dizzy: { eyes: 'spiral', brows: [-10, 10], lift: 2, mouth: 'squiggle', mark: 'stars' },
  cold: { eyes: 'dot', brows: [-12, -12], lift: 4, mouth: 'teeth', shake: 2.2, mark: 'cold' },
  relieved: { eyes: 'closed', brows: [-8, -8], lift: 2, mouth: 'smile', mark: 'sweat' },
};

const lerp = (a, b, p) => a + (b - a) * p;
const ease = (p) => (p < 0.5 ? 2 * p * p : 1 - Math.pow(-2 * p + 2, 2) / 2);
const rad = (d) => (d * Math.PI) / 180;
// a point `len` away from (x, y) at our angle convention (0 = down, 90 = right)
const step = (x, y, deg, len) => [x + Math.sin(rad(deg)) * len, y + Math.cos(rad(deg)) * len];

function blendPose(a, b, p) {
  const mix = (u, v) => u.map((limb, i) => limb.map((ang, j) => lerp(ang, v[i][j], p)));
  const f = (k) => lerp(a[k] || 0, b[k] || 0, p);
  return { a: mix(a.a, b.a), g: mix(a.g, b.g), lean: f('lean'), rot: f('rot'), dy: f('dy'), head: f('head') };
}

// Where the character is in its list of moves at scene time t: the pose blended 0.35 s into the new one.
function current(s, moves, t) {
  const list = moves.map((m) => ({ ...m, t: typeof m.at === 'number' ? m.at : s.time(m.at) })).sort((m, n) => m.t - n.t);
  let i = 0;
  while (i + 1 < list.length && list[i + 1].t <= t) i++;
  const now = list[i];
  const before = list[Math.max(0, i - 1)];
  const p = i === 0 ? 1 : ease(Math.min(1, Math.max(0, (t - now.t) / 0.35)));
  const pa = POSES[before.pose || 'stand'] && poseAt(before.pose || 'stand', t);
  const pb = POSES[now.pose || 'stand'] && poseAt(now.pose || 'stand', t);
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
    } else if (f.eyes === 'closed') { // happy closed eyes: upward arcs
      ctx.beginPath(); ctx.lineWidth = 5; ctx.arc(x, ey + 4, 8, rad(200), rad(340)); ctx.stroke(); ctx.lineWidth = 4;
    } else if (f.eyes === 'half') { // sleepy / smug: lids half down
      ctx.beginPath(); ctx.ellipse(x, ey + 5, 6.5, 6, 0, 0, Math.PI); ctx.fill();
      ctx.beginPath(); ctx.lineWidth = 4.5; ctx.moveTo(x - 9, ey + 4); ctx.lineTo(x + 9, ey + 4); ctx.stroke(); ctx.lineWidth = 4;
    } else if (f.eyes === 'squint') { // > < eyes
      ctx.beginPath(); ctx.lineWidth = 5;
      ctx.moveTo(x - side * 8, ey - 6); ctx.lineTo(x + side * 6, ey + 1); ctx.lineTo(x - side * 8, ey + 8); ctx.stroke(); ctx.lineWidth = 4;
    } else if (f.eyes === 'spiral') { // dizzy
      ctx.beginPath(); ctx.lineWidth = 3;
      for (let i = 0; i <= 28; i++) { const a = i * 0.45 + t * 6 * side, rr = i * 0.42; ctx.lineTo(x + Math.cos(a) * rr, ey + Math.sin(a) * rr); }
      ctx.stroke(); ctx.lineWidth = 4;
    } else {
      const dx = f.eyes === 'side' ? 5 : 0;
      const dy = f.eyes === 'side' ? -4 : 0;
      ctx.beginPath(); // tall black ovals, as in the channel logo
      ctx.ellipse(x + dx, ey + dy + 3, 6.5, 10.5, 0, 0, Math.PI * 2);
      ctx.fill();
    }
    // brow: tilt + means the inner end (towards the nose) is lower
    const by = ey - 20 - f.lift;
    const tilt = rad(f.brows[side < 0 ? 0 : 1]);
    const half = 11;
    ctx.beginPath(); // thick curved brows, as in the logo
    const inner = [x - side * half, by + Math.sin(tilt) * half];
    const outer = [x + side * half, by - Math.sin(tilt) * half];
    ctx.lineWidth = 5;
    ctx.moveTo(inner[0], inner[1]);
    ctx.quadraticCurveTo(x, by - 5 - Math.abs(Math.sin(tilt)) * 2, outer[0], outer[1]);
    ctx.stroke();
    ctx.lineWidth = 4;
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
    case 'small': ctx.ellipse(0, my + 2, 5, 6, 0, 0, Math.PI * 2); ctx.fill(); break;
    case 'smirk': ctx.moveTo(-8, my + 2); ctx.quadraticCurveTo(6, my + 6, 15, my - 6); ctx.stroke(); break;
    case 'teeth': // gritted teeth: a white box with lines
      ctx.fillStyle = SKIN; ctx.roundRect(-15, my - 7, 30, 14, 4); ctx.fill(); ctx.stroke();
      ctx.beginPath(); ctx.lineWidth = 2.5; ctx.moveTo(-15, my); ctx.lineTo(15, my);
      for (const xx of [-7, 0, 7]) { ctx.moveTo(xx, my - 7); ctx.lineTo(xx, my + 7); }
      ctx.stroke(); ctx.fillStyle = INK; break;
    case 'side': ctx.lineWidth = 4.5; ctx.arc(12, my + 8, 8, rad(215), rad(325)); ctx.stroke(); break; // the logo's small worried mouth
    default: ctx.moveTo(-10, my); ctx.lineTo(10, my); ctx.stroke();
  }
  ctx.restore();
}

// ---- Looks (29 Oct, owner: costumes, body types, hair, like the reference Shorts) --------------------------
// hero(s, { look: { body, outfit, top, hat, hair, hairColor, beard, moustache, glasses } }). Without `look` the
// stickman stays the plain logo character. Heads stay white and round (the channel look; no skin colours).
// Body types change the proportions and the shape of the filled body; outfits are a colour + small details.
export const BODIES = {
  normal: { body: 1, legs: 1, arms: 1, head: 1, torso: 'shirt', w: 64 },
  thin: { body: 1.12, legs: 1.15, arms: 1.1, head: 0.95, torso: 'shirt', w: 44 },
  round: { body: 0.95, legs: 0.85, arms: 1, head: 1, torso: 'round', w: 104 },
  muscle: { body: 1.05, legs: 1, arms: 1.05, head: 0.95, torso: 'muscle', w: 92 },
  short: { body: 0.78, legs: 0.72, arms: 0.85, head: 1, torso: 'shirt', w: 60 },
  child: { body: 0.62, legs: 0.62, arms: 0.7, head: 0.9, torso: 'shirt', w: 50 },
  old: { body: 0.95, legs: 0.95, arms: 1, head: 1, torso: 'shirt', w: 62, lean: 10 },
};
// top = main colour; long = coat down to the knees; details drawn on top
export const OUTFITS = {
  shirt: { top: '#4f9de8' },
  tshirt: { top: '#e5484d' },
  suit: { top: '#3b3f4a', details: ['tie'] },
  passenger_1912: { top: '#6b4f3a', details: ['bowtie', 'buttons'] },
  dress: { top: '#d65db1', details: ['skirt'] },
  doctor: { top: '#f4f4f6', long: true, details: ['stethoscope', 'pocket'] },
  scientist: { top: '#f4f4f6', long: true, details: ['pocket', 'buttons'] },
  police: { top: '#22315e', details: ['badge', 'belt', 'buttons'] },
  firefighter: { top: '#c9a227', long: true, details: ['stripes'] },
  astronaut: { top: '#eeeeF2', details: ['backpack', 'belt'] },
  diver: { top: '#2b2f38', details: ['stripes'] },
  sailor: { top: '#f4f4f6', details: ['collar'] },
  soldier_free: { top: '#556b2f', details: ['belt', 'pocket'] }, // plain green jacket, no weapons
  farmer: { top: '#5b8fd6', details: ['overalls'] },
  cowboy: { top: '#2fa8a0', details: ['vest'] },
  chef: { top: '#f4f4f6', details: ['buttons'] },
  worker: { top: '#f07c1f', details: ['stripes'] },
  student: { top: '#4f9de8', details: ['backpack'] },
  explorer: { top: '#b8945a', details: ['pocket', 'belt'] },
  hospital_gown: { top: '#9fd3d1', long: true },
};
export const HATS = ['cap', 'police_cap', 'cowboy', 'top_hat', 'hard_hat', 'straw', 'chef', 'beanie', 'fire_helmet', 'sailor_cap', 'bowler', 'explorer'];
export const HAIRS = ['short', 'long', 'curly', 'bun', 'spiky', 'bald'];

function torso(ctx, look, D, edge) {
  const out = OUTFITS[look.outfit] || (look.top ? { top: look.top } : null);
  if (!out && !look.body) return;
  const top = look.top || (out && out.top) || '#4f9de8';
  const h = L.body * D.body, w = D.w, long = out && out.long;
  ctx.save();
  ctx.lineWidth = 6 + WIDEN;
  ctx.fillStyle = edge ? INK : top;
  ctx.beginPath();
  if (D.torso === 'round') ctx.ellipse(0, -h * 0.45, w / 2, h * 0.62, 0, 0, Math.PI * 2);
  else if (D.torso === 'muscle') { ctx.moveTo(-w / 2, -h + 4); ctx.lineTo(w / 2, -h + 4); ctx.lineTo(w * 0.28, 8); ctx.lineTo(-w * 0.28, 8); ctx.closePath(); }
  else ctx.roundRect(-w / 2, -h + 2, w, h + (long ? 50 : 10), 14);
  ctx.fill(); ctx.stroke();
  if (edge || !out) { ctx.restore(); return; }
  const d = new Set(out.details || []);
  ctx.lineWidth = 4;
  if (d.has('skirt')) { ctx.beginPath(); ctx.fillStyle = top; ctx.moveTo(-w / 2, -6); ctx.lineTo(w / 2, -6); ctx.lineTo(w * 0.9, 52); ctx.lineTo(-w * 0.9, 52); ctx.closePath(); ctx.fill(); ctx.stroke(); }
  if (d.has('tie')) { ctx.beginPath(); ctx.fillStyle = RED; ctx.moveTo(0, -h + 6); ctx.lineTo(6, -h + 18); ctx.lineTo(0, -h * 0.35); ctx.lineTo(-6, -h + 18); ctx.closePath(); ctx.fill(); ctx.stroke(); }
  if (d.has('bowtie')) { ctx.beginPath(); ctx.fillStyle = RED; ctx.moveTo(0, -h + 10); ctx.lineTo(-12, -h + 3); ctx.lineTo(-12, -h + 17); ctx.closePath(); ctx.moveTo(0, -h + 10); ctx.lineTo(12, -h + 3); ctx.lineTo(12, -h + 17); ctx.closePath(); ctx.fill(); ctx.stroke(); }
  if (d.has('buttons')) { ctx.fillStyle = INK; for (let i = 1; i <= 3; i++) { ctx.beginPath(); ctx.arc(0, -h + i * h * 0.24, 3.5, 0, Math.PI * 2); ctx.fill(); } }
  if (d.has('pocket')) { ctx.strokeRect(w * 0.08, -h * 0.72, w * 0.28, h * 0.16); }
  if (d.has('badge')) { ctx.beginPath(); ctx.fillStyle = '#f2c94c'; ctx.arc(-w * 0.24, -h * 0.68, 6, 0, Math.PI * 2); ctx.fill(); ctx.stroke(); }
  if (d.has('belt')) { ctx.fillStyle = '#1d1d1f'; ctx.fillRect(-w / 2, -h * 0.14, w, 8); ctx.fillStyle = '#c9a227'; ctx.fillRect(-5, -h * 0.14, 10, 8); }
  if (d.has('stripes')) { ctx.fillStyle = '#e8e8e8'; ctx.fillRect(-w / 2 + 2, -h * 0.45, w - 4, 6); ctx.fillRect(-w / 2 + 2, -h * 0.2, w - 4, 6); }
  if (d.has('collar')) { ctx.beginPath(); ctx.fillStyle = '#2b5bb3'; ctx.moveTo(-w / 2, -h + 2); ctx.lineTo(w / 2, -h + 2); ctx.lineTo(0, -h + 26); ctx.closePath(); ctx.fill(); ctx.stroke(); }
  if (d.has('overalls')) { ctx.fillStyle = '#6b4f3a'; ctx.fillRect(-w / 2 + 3, -h * 0.5, w - 6, h * 0.5 + 8); ctx.strokeRect(-w / 2 + 3, -h * 0.5, w - 6, h * 0.5 + 8); }
  if (d.has('vest')) { ctx.fillStyle = '#6b4f3a'; ctx.fillRect(-w / 2, -h + 2, w * 0.3, h); ctx.fillRect(w / 2 - w * 0.3, -h + 2, w * 0.3, h); }
  if (d.has('stethoscope')) { ctx.beginPath(); ctx.strokeStyle = '#555'; ctx.lineWidth = 3; ctx.arc(0, -h + 12, w * 0.3, rad(20), rad(160)); ctx.stroke(); ctx.beginPath(); ctx.fillStyle = '#9aa0a6'; ctx.arc(w * 0.18, -h * 0.55, 5, 0, Math.PI * 2); ctx.fill(); ctx.strokeStyle = INK; }
  ctx.restore();
}

function backpack(ctx, h, edge) {
  ctx.save();
  ctx.fillStyle = edge ? INK : '#d9d9de';
  ctx.lineWidth = 5 + WIDEN;
  ctx.beginPath();
  ctx.roundRect(-34, -h + 6, 24, 54, 7);
  ctx.fill(); ctx.stroke();
  ctx.restore();
}

// hair is drawn on the head (after the white circle) except long hair, which also hangs behind the head
function hair(ctx, look, R, edge, behind) {
  const kind = look.hair;
  if (!kind || kind === 'bald') return;
  ctx.save();
  ctx.fillStyle = edge ? INK : look.hairColor || '#4a3424';
  ctx.lineWidth = 5 + WIDEN;
  ctx.beginPath();
  if (behind) {
    if (kind === 'long') { ctx.roundRect(-R * 1.08, -R * 0.6, R * 2.16, R * 1.9, R * 0.5); ctx.fill(); ctx.stroke(); }
    ctx.restore();
    return;
  }
  if (kind === 'curly') { for (let i = -3; i <= 3; i++) { ctx.moveTo(i * R * 0.28 + R * 0.2, -R * 0.82); ctx.arc(i * R * 0.28, -R * 0.82 - Math.abs(i) * -R * 0.06, R * 0.22, 0, Math.PI * 2); } }
  else if (kind === 'spiky') { ctx.moveTo(-R, -R * 0.35); for (let i = 0; i <= 6; i++) ctx.lineTo(-R + (i * 2 * R) / 6 + R / 6, -R * (i % 2 ? 1.25 : 0.75)); ctx.lineTo(R, -R * 0.35); ctx.arc(0, 0, R, -0.35, Math.PI + 0.35, true); }
  else { ctx.arc(0, 0, R, Math.PI + 0.55, -0.55); ctx.quadraticCurveTo(0, -R * 0.78, -R * 0.85, -R * 0.52); } // short/long/bun: a cap of hair
  ctx.closePath(); ctx.fill(); if (kind !== 'curly') ctx.stroke();
  if (kind === 'bun') { ctx.beginPath(); ctx.arc(0, -R * 1.08, R * 0.3, 0, Math.PI * 2); ctx.fill(); ctx.stroke(); }
  ctx.restore();
}

function hat(ctx, kind, R, edge) {
  if (!kind) return;
  const C = {
    cap: ['#e5484d'], police_cap: ['#22315e', '#f2c94c'], cowboy: ['#a8743f'], top_hat: ['#1d1d1f', '#e5484d'],
    hard_hat: ['#f6c343'], straw: ['#e8c76b', '#2b5bb3'], chef: ['#ffffff'], beanie: ['#2fa8a0'],
    fire_helmet: ['#d33b2c', '#f2c94c'], sailor_cap: ['#ffffff', '#2b5bb3'], bowler: ['#3b2f2a'], explorer: ['#c9a66b'],
  }[kind];
  if (!C) throw new Error(`unknown hat "${kind}" (have: ${HATS.join(', ')})`);
  ctx.save();
  ctx.lineWidth = 5 + WIDEN;
  ctx.fillStyle = edge ? INK : C[0];
  const band = (y, h) => { if (!edge && C[1]) { ctx.fillStyle = C[1]; ctx.fillRect(-R * 0.75, y, R * 1.5, h); ctx.fillStyle = C[0]; } };
  const brim = (wk, y) => { ctx.beginPath(); ctx.ellipse(0, y, R * wk, R * 0.16, 0, 0, Math.PI * 2); ctx.fill(); ctx.stroke(); };
  ctx.beginPath();
  if (kind === 'top_hat') { brim(1.2, -R * 0.72); ctx.beginPath(); ctx.rect(-R * 0.62, -R * 1.85, R * 1.24, R * 1.12); ctx.fill(); ctx.stroke(); band(-R * 0.95, R * 0.18); }
  else if (kind === 'cowboy' || kind === 'straw' || kind === 'explorer') { brim(kind === 'cowboy' ? 1.6 : 1.45, -R * 0.68); ctx.beginPath(); ctx.ellipse(0, -R * 0.95, R * 0.62, R * 0.42, 0, Math.PI, 0); ctx.closePath(); ctx.fill(); ctx.stroke(); band(-R * 0.82, R * 0.12); }
  else if (kind === 'chef') { ctx.roundRect(-R * 0.6, -R * 1.55, R * 1.2, R * 0.85, 8); ctx.fill(); ctx.stroke(); ctx.beginPath(); for (const x of [-0.45, 0, 0.45]) ctx.arc(x * R, -R * 1.55, R * 0.36, 0, Math.PI * 2); ctx.fill(); ctx.stroke(); }
  else if (kind === 'beanie') { ctx.arc(0, -R * 0.45, R * 0.98, Math.PI, 0); ctx.closePath(); ctx.fill(); ctx.stroke(); }
  else if (kind === 'bowler') { brim(1.15, -R * 0.66); ctx.beginPath(); ctx.arc(0, -R * 0.7, R * 0.68, Math.PI, 0); ctx.closePath(); ctx.fill(); ctx.stroke(); }
  else { // cap, police_cap, hard_hat, fire_helmet, sailor_cap: a dome with a visor or band
    ctx.arc(0, -R * 0.5, R * 0.98, Math.PI, 0); ctx.closePath(); ctx.fill(); ctx.stroke();
    if (kind === 'cap' || kind === 'police_cap') { ctx.beginPath(); ctx.ellipse(R * 0.7, -R * 0.52, R * 0.55, R * 0.13, 0, 0, Math.PI * 2); ctx.fill(); ctx.stroke(); }
    else { brim(1.15, -R * 0.52); }
    band(-R * 0.72, R * 0.14);
    if (kind === 'police_cap' && !edge) { ctx.beginPath(); ctx.fillStyle = '#f2c94c'; ctx.arc(0, -R * 1.0, R * 0.12, 0, Math.PI * 2); ctx.fill(); }
  }
  ctx.restore();
}

// glasses, moustache and beard, in the face's own frame (head radius R)
function faceExtras(ctx, look, R) {
  ctx.save();
  ctx.scale(R / 46, R / 46);
  ctx.strokeStyle = INK; ctx.lineWidth = 3.5;
  if (look.glasses) { for (const x of [-16.5, 16.5]) { ctx.beginPath(); ctx.arc(x, -3, 12, 0, Math.PI * 2); ctx.stroke(); } ctx.beginPath(); ctx.moveTo(-4.5, -4); ctx.lineTo(4.5, -4); ctx.stroke(); }
  ctx.fillStyle = look.hairColor || '#4a3424';
  if (look.moustache) { ctx.beginPath(); ctx.ellipse(-7, 8, 9, 4.5, -0.2, 0, Math.PI * 2); ctx.ellipse(7, 8, 9, 4.5, 0.2, 0, Math.PI * 2); ctx.fill(); }
  if (look.beard) { ctx.beginPath(); ctx.arc(0, 4, 40, rad(20), rad(160)); ctx.quadraticCurveTo(0, 62, 37.6, 17.7); ctx.fill(); }
  ctx.restore();
}

// One pass of the figure. edge = true draws only the silhouette (wider lines, no face, no glass fill).
function figure(ctx, c, o, sc, k, t, shake, drift, edge) {
  const look = o.look || {};
  const D = BODIES[look.body] || BODIES.normal;
  const thigh = L.thigh * D.legs, shin = L.shin * D.legs, bodyH = L.body * D.body, R = L.head * D.head;
  const arm = [L.upper * D.arms, L.fore * D.arms];
  ctx.save();
  ctx.translate(shake, drift + (c.pose.dy || 0) * k);
  ctx.scale((o.flip ? -sc : sc) / Math.sqrt(k), sc * k); // taller and thinner, same volume (Spaghettification article)
  const mid = -(thigh + shin + bodyH / 2);
  if (c.pose.rot) { ctx.translate(0, mid); ctx.rotate(rad(c.pose.rot)); ctx.translate(0, -mid); }
  if (c.spin) {
    ctx.translate(0, -150);
    ctx.rotate(rad(c.spin * c.since));
    ctx.translate(0, 150);
  }
  ctx.lineCap = 'round';
  ctx.lineJoin = 'round';
  ctx.strokeStyle = INK;
  ctx.lineWidth = L.width + WIDEN;
  const hip = [0, -(thigh + shin)];
  limb(ctx, hip[0], hip[1], c.pose.g[0], [thigh, shin]);
  limb(ctx, hip[0], hip[1], c.pose.g[1], [thigh, shin]);
  // upper body leans around the hip
  ctx.save();
  ctx.translate(hip[0], hip[1]);
  ctx.rotate(rad(c.pose.lean + (D.lean || 0)));
  const neck = [0, -bodyH];
  const out = OUTFITS[look.outfit];
  if (o.helmet || (out && (out.details || []).includes('backpack'))) backpack(ctx, bodyH, edge);
  ctx.lineWidth = L.width + WIDEN;
  ctx.beginPath();
  ctx.moveTo(0, 0);
  ctx.lineTo(neck[0], neck[1]);
  ctx.stroke();
  torso(ctx, look, D, edge);
  ctx.strokeStyle = INK;
  ctx.lineWidth = L.width + WIDEN;
  const shoulder = [0, neck[1] + 8];
  // with clothes the arms start at the sides of the body (like the reference Shorts), else at the neck line
  const dressed = !!(OUTFITS[look.outfit] || look.top || look.body);
  const sx = !dressed ? 0 : D.torso === 'round' ? D.w * 0.36 : D.torso === 'muscle' ? D.w * 0.42 : D.w * 0.5 - 5;
  limb(ctx, shoulder[0] - sx, shoulder[1] + (sx ? 8 : 0), c.pose.a[0], Object.assign(arm.slice(), { hand: L.hand + WIDEN / 2 }));
  limb(ctx, shoulder[0] + sx, shoulder[1] + (sx ? 8 : 0), c.pose.a[1], Object.assign(arm.slice(), { hand: L.hand + WIDEN / 2 }));
  // head
  ctx.translate(0, neck[1] - R + 6);
  if (c.pose.head) ctx.rotate(rad(c.pose.head));
  if (o.flip) ctx.scale(-1, 1); // keep the face and marks readable when he faces left
  hair(ctx, look, R, edge, true);
  ctx.beginPath();
  ctx.fillStyle = edge ? INK : SKIN;
  ctx.lineWidth = 7 + WIDEN;
  ctx.arc(0, 0, R, 0, Math.PI * 2);
  ctx.fill();
  ctx.stroke();
  hair(ctx, look, R, edge, false);
  if (!edge) face(ctx, c.face, R, t, (o.x ?? 0) % 1.7);
  if (!edge) faceExtras(ctx, look, R);
  hat(ctx, look.hat, R, edge);
  if (o.helmet) {
    ctx.beginPath();
    ctx.lineWidth = 5 + WIDEN;
    ctx.arc(0, 4, R * 1.5, 0, Math.PI * 2);
    if (!edge) {
      ctx.fillStyle = GLASS;
      ctx.fill();
    }
    ctx.stroke();
    if (!edge) {
      ctx.beginPath();
      ctx.strokeStyle = 'rgba(255,255,255,0.9)';
      ctx.lineWidth = 6;
      ctx.arc(0, 4, R * 1.22, rad(200), rad(250));
      ctx.stroke();
      ctx.strokeStyle = INK;
    }
  }
  if (!edge) mark(ctx, c.face.mark, R, t);
  ctx.restore();
  ctx.restore();
}

function mark(ctx, kind, r, t) {
  if (!kind) return;
  ctx.save();
  ctx.fillStyle = kind === 'tear' || kind === 'sweat' ? '#6cb4ee' : RED;
  ctx.strokeStyle = INK;
  ctx.lineWidth = 3;
  if (kind === 'lines') { // the logo's two little 'thinking' strokes above the head
    ctx.strokeStyle = INK;
    ctx.lineWidth = 6;
    ctx.lineCap = 'round';
    for (const [x0, y0, x1, y1] of [[-0.62, -1.22, -0.78, -1.5], [-0.3, -1.32, -0.33, -1.62]]) {
      ctx.beginPath(); ctx.moveTo(x0 * r, y0 * r); ctx.lineTo(x1 * r, y1 * r); ctx.stroke();
    }
    ctx.restore();
    return;
  }
  if (kind === 'tears') { // streams down both cheeks
    ctx.fillStyle = 'rgba(108,180,238,0.9)';
    for (const sx of [-1, 1]) {
      const y = r * 0.05 + (t * 60) % 40;
      ctx.beginPath(); ctx.ellipse(sx * r * 0.36, y, 6, 10, 0, 0, Math.PI * 2); ctx.fill();
      ctx.fillRect(sx * r * 0.36 - 3, -r * 0.05, 6, y + r * 0.05);
    }
    ctx.restore();
    return;
  }
  if (kind === 'zzz' || kind === 'stars' || kind === 'cold') {
    for (let i = 0; i < 3; i++) {
      const ph = (t * 0.8 + i / 3) % 1;
      if (kind === 'zzz') {
        ctx.font = `bold ${Math.round(r * (0.4 + 0.25 * i))}px sans-serif`; ctx.fillStyle = INK;
        ctx.fillText('Z', r * (0.9 + 0.3 * i), -r * (1 + 0.45 * i) - ph * 10);
      } else if (kind === 'stars') { // stars circling the head
        const a = t * 4 + (i * Math.PI * 2) / 3;
        ctx.fillStyle = '#fcd34d';
        ctx.font = `bold ${Math.round(r * 0.5)}px sans-serif`; ctx.textAlign = 'center';
        ctx.fillText('★', Math.cos(a) * r * 1.1, -r * 1.15 + Math.sin(a) * r * 0.25);
      } else { // cold: little blue shiver lines on both sides
        ctx.strokeStyle = '#7cc4ff'; ctx.lineWidth = 5; ctx.lineCap = 'round';
        for (const sx of [-1, 1]) { ctx.beginPath(); ctx.moveTo(sx * r * (1.25 + 0.15 * i), -r * 0.3 + i * 18); ctx.lineTo(sx * r * (1.45 + 0.15 * i), -r * 0.3 + i * 18 - 8); ctx.stroke(); }
      }
    }
    ctx.restore();
    return;
  }
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
// and outline: a colour for a 'sticker' edge around the whole figure, so he stays readable on dark backgrounds.
export function hero(s, o = {}) {
  const moves = o.moves && o.moves.length ? o.moves : [{ at: 0, pose: o.pose || 'stand', face: o.face || 'neutral' }];
  const sc = o.scale ?? 1;
  const box = { x: o.x ?? s.cx, y: (o.y ?? s.cy + 250) - 150 * sc, w: 180 * sc, h: 330 * sc };
  s.draw({ x: o.x ?? s.cx, y: o.y ?? s.cy + 250, at: o.at ?? 0, out: o.out, enter: o.enter ?? 'fade', id: o.id }, (ctx) => {
    const t = s.t;
    const c = current(s, moves, t);
    const val = (v, d) => (typeof v === 'function' ? v(s) : v ?? d);
    const k = Math.max(0.2, val(o.stretch, 1));
    ctx.globalAlpha *= Math.max(0, Math.min(1, val(o.alpha, 1)));
    const shake = c.face.shake ? Math.sin(t * 60) * c.face.shake : 0;
    const drift = o.float ? Math.sin(t * 1.6) * 14 : Math.sin(t * 2.2) * 1.5; // breathing or floating
    const ink = val(o.color, BLACK);
    // On a library place: a soft shadow on the floor and NO white sticker edge, so people stand IN the room
    // (owner, 29 Oct: "looks like pasted"). The edge stays for plain dark backgrounds.
    const onPlace = !!s._shot;
    if (onPlace && o.shadow !== false && !o.float) {
      ctx.save();
      ctx.fillStyle = 'rgba(0,0,0,0.28)';
      ctx.beginPath();
      ctx.ellipse(0, 4 * sc, (c.pose.rot ? 150 : 62) * sc, 13 * sc, 0, 0, Math.PI * 2);
      ctx.fill();
      ctx.restore();
    }
    // outline: draw the whole figure first in the edge colour with wider lines, then normally on top.
    // (A canvas drop-shadow filter did the same but made rendering ~30x slower: run 40824544082 hung.)
    if (o.outline && !(onPlace && o.outline === '#ffffff')) {
      INK = o.outline;
      WIDEN = 7 / sc;
      figure(ctx, c, o, sc, k, t, shake, drift, true);
    }
    INK = ink;
    WIDEN = 0;
    figure(ctx, c, o, sc, k, t, shake, drift, false);
    INK = BLACK;
  });
  return box;
}

// A crowd of extras (owner, 29 Oct: "stickmans there should be lot"): different bodies, clothes, hair and hats,
// chosen from a seed so the same crowd looks the same in every frame. crowd(s, { n, x0, x1, y, scale, depth,
// seed, faces, poses, outfits, at }). depth > 0 puts every second person a little further back (smaller).
export function crowd(s, o = {}) {
  const n = o.n ?? 6, seed = o.seed ?? 7;
  const rnd = (i) => Math.abs(Math.sin((i + 1) * 12.9898 + seed * 78.233) * 43758.5453) % 1;
  const pick = (arr, i) => arr[Math.floor(rnd(i) * arr.length) % arr.length];
  const bodies = ['normal', 'normal', 'thin', 'round', 'short', 'muscle', 'old'];
  const outfits = o.outfits || ['shirt', 'tshirt', 'suit', 'dress', 'worker', 'student', 'farmer', 'chef'];
  const hairs = ['short', 'long', 'curly', 'bun', 'spiky', 'bald'];
  const colors = ['#4a3424', '#1d1d1f', '#c98b3a', '#8a8a8a', '#a8432a'];
  const x0 = o.x0 ?? 120, x1 = o.x1 ?? s.W - 120, y = o.y ?? s.H * 0.78, sc = o.scale ?? 1;
  const people = [];
  for (let i = 0; i < n; i++) {
    const back = o.depth && i % 2 ? o.depth : 0;
    const look = { body: pick(bodies, i * 3), outfit: pick(outfits, i * 5 + 1), hair: pick(hairs, i * 7 + 2),
      hairColor: pick(colors, i * 11 + 3), hat: rnd(i * 13 + 4) < 0.25 ? pick(['cap', 'beanie', 'bowler', 'straw'], i) : undefined,
      glasses: rnd(i * 17 + 5) < 0.2, moustache: rnd(i * 19 + 6) < 0.15 };
    const face = o.faces ? pick(o.faces, i * 23 + 7) : 'neutral';
    const pose = o.poses ? pick(o.poses, i * 29 + 8) : 'stand';
    const x = n === 1 ? (x0 + x1) / 2 : x0 + ((x1 - x0) * i) / (n - 1);
    people.push(hero(s, { x, y: y - back, scale: sc * (1 - back / 900), look, flip: rnd(i * 31) < 0.5,
      outline: o.outline, at: o.at ?? 0, enter: o.enter ?? 'fade', moves: [{ at: 0, pose, face }] }));
  }
  return people;
}

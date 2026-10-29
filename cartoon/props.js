// Simple props drawn in code, in the same flat cartoon style as the character.
// Like the character, everything depends only on the time.
import { PLACES, ART } from './art_cards.js';

// A black hole, simplified from the well-known look (bright disc of gas in front, the far side of the disc
// bent up over the top by gravity, a thin bright rim around the black centre). Slowly shimmers.
export function blackHole(s, o = {}) {
  const r = o.r ?? 160;
  s.draw({ x: o.x ?? s.cx, y: o.y ?? s.cy, at: o.at ?? 0, out: o.out, enter: o.enter ?? 'fade', id: o.id }, (ctx) => {
    const t = s.t;
    const glow = 0.75 + 0.25 * Math.sin(t * 2.1);
    const band = (from, to, rr, w, alpha) => {
      ctx.beginPath();
      ctx.lineCap = 'round';
      ctx.lineWidth = w;
      ctx.strokeStyle = `rgba(246, 160, 58, ${alpha})`;
      ctx.arc(0, 0, rr, from, to);
      ctx.stroke();
    };
    ctx.save();
    // soft glow around everything
    const halo = ctx.createRadialGradient(0, 0, r * 0.9, 0, 0, r * 2.2);
    halo.addColorStop(0, `rgba(255, 190, 90, ${0.45 * glow})`);
    halo.addColorStop(1, 'rgba(255, 190, 90, 0)');
    ctx.fillStyle = halo;
    ctx.beginPath();
    ctx.arc(0, 0, r * 2.2, 0, Math.PI * 2);
    ctx.fill();
    // far side of the disc, bent over the top and under the bottom of the hole
    band(Math.PI * 1.04, Math.PI * 1.96, r * 1.18, r * 0.3, 0.95);
    band(Math.PI * 0.1, Math.PI * 0.9, r * 1.1, r * 0.12, 0.7);
    // the hole and its thin bright rim
    ctx.beginPath();
    ctx.fillStyle = '#0b0b0d';
    ctx.arc(0, 0, r, 0, Math.PI * 2);
    ctx.fill();
    ctx.lineWidth = r * 0.05;
    ctx.strokeStyle = `rgba(255, 226, 138, ${glow})`;
    ctx.stroke();
    // near side of the disc: a flat band across the front
    ctx.scale(1, 0.2);
    const g = ctx.createLinearGradient(-r * 2, 0, r * 2, 0);
    g.addColorStop(0, 'rgba(229, 72, 77, 0.9)');
    g.addColorStop(0.5, '#ffe28a');
    g.addColorStop(1, 'rgba(246, 160, 58, 0.9)');
    ctx.beginPath();
    ctx.lineWidth = r * 0.9;
    ctx.strokeStyle = g;
    ctx.arc(0, 0, r * 1.55, 0, Math.PI);
    ctx.stroke();
    ctx.restore();
  });
  return { x: o.x ?? s.cx, y: o.y ?? s.cy, w: r * 4, h: r * 2.6 };
}

// A few twinkling stars, for space scenes (light: true on a dark background).
export function stars(s, o = {}) {
  s.draw({ at: o.at ?? 0, out: o.out, enter: 'none' }, (ctx) => {
    for (let i = 0; i < (o.count ?? 40); i++) {
      const x = s.rand(i) * s.W;
      const y = s.rand(i + 100) * s.H;
      const tw = 0.5 + 0.5 * Math.sin(s.t * 2 + i);
      ctx.beginPath();
      ctx.fillStyle = o.light ? `rgba(255, 255, 255, ${0.35 + 0.5 * tw})` : `rgba(29, 29, 31, ${0.15 + 0.25 * tw})`;
      ctx.arc(x, y, 2 + 2 * s.rand(i + 200), 0, Math.PI * 2);
      ctx.fill();
    }
  });
}

// Captions like the big Shorts channels (owner's example, 29 Oct): ONE word at a time, bold white with a black
// edge, no box, popping in as it is spoken. Uses explainroo's word timings (s.words). Numbers in yellow.
export function words(s, o = {}) {
  const list = s.words || [];
  const y = o.y ?? s.H * 0.72;
  const size = o.size ?? 78;
  s.draw({ at: 0, enter: 'none', sfx: false }, (ctx) => {
    const t = s.t;
    let i = -1;
    for (let k = 0; k < list.length; k++) if (list[k].start <= t) i = k;
    if (i < 0) return;
    const w = list[i];
    const until = i + 1 < list.length ? Math.min(list[i + 1].start, w.end + 0.6) : w.end + 0.6;
    if (t > until) return;
    const text = w.text.replace(/[^\p{L}\p{N}'%.-]/gu, '').replace(/\.$/, '').toUpperCase();
    if (!text) return;
    const pop = Math.min(1, (t - w.start) / 0.09);
    ctx.save();
    ctx.translate(s.W / 2, y);
    ctx.scale(0.85 + 0.15 * pop, 0.85 + 0.15 * pop);
    ctx.font = `900 ${size}px Inter, "Arial Black", sans-serif`;
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.lineJoin = 'round';
    ctx.lineWidth = size * 0.16;
    ctx.strokeStyle = '#000000';
    ctx.strokeText(text, 0, 0);
    ctx.fillStyle = /\d/.test(text) ? '#fcd34d' : '#ffffff';
    ctx.fillText(text, 0, 0);
    ctx.restore();
  });
}

// ---------- backgrounds for every kind of topic (full 9:16 frame, drawn first in a scene) ----------
// background(s, 'space' | 'ocean' | 'deep' | 'sky' | 'land' | 'city' | 'night' | 'body' | 'desert' | 'snow' | 'fire' | 'room')
const SKIES = {
  space: ['#1d2b55', '#0d1328'], night: ['#1b2550', '#0a0f24'], ocean: ['#4fb3e8', '#0b4f86'],
  deep: ['#0b3a66', '#02111f'], sky: ['#8fd3ff', '#e9f7ff'], land: ['#8fd3ff', '#e9f7ff'],
  city: ['#ffd29a', '#ffeedd'], body: ['#f7a6a6', '#a8323e'], desert: ['#ffd27a', '#fff1cf'],
  snow: ['#bfe3ff', '#ffffff'], fire: ['#ffb347', '#7a1d0e'], room: ['#fbf3e4', '#efe2c8'],
};

export function background(s, kind = 'space') {
  // Keep the camera still: explainroo's automatic camera zoomed into the drawings and cut the captions off
  // (Mariana Trench Short, render 40862860430). background() is called first in every scene, as the camera needs.
  if (s.camera) s.camera([]);
  const [top, bottom] = SKIES[kind] || SKIES.space;
  s.draw({ at: 0, enter: 'none', sfx: false }, (ctx) => {
    const g = ctx.createLinearGradient(0, 0, 0, s.H);
    g.addColorStop(0, top);
    g.addColorStop(1, bottom);
    ctx.fillStyle = g;
    ctx.fillRect(0, 0, s.W, s.H);
    const t = s.t;
    ctx.save();
    if (kind === 'space' || kind === 'night') {
      for (let i = 0; i < 80; i++) {
        const tw = 0.5 + 0.5 * Math.sin(t * 2 + i);
        ctx.beginPath();
        ctx.fillStyle = `rgba(255,255,255,${0.3 + 0.5 * tw})`;
        ctx.arc(s.rand(i) * s.W, s.rand(i + 100) * (kind === 'night' ? s.H * 0.6 : s.H), 2 + 2 * s.rand(i + 200), 0, Math.PI * 2);
        ctx.fill();
      }
    }
    if (kind === 'ocean' || kind === 'deep') { // light rays and bubbles
      for (let i = 0; i < 5 && kind === 'ocean'; i++) {
        ctx.beginPath();
        ctx.fillStyle = 'rgba(255,255,255,0.07)';
        const x = s.W * (0.1 + i * 0.22) + Math.sin(t * 0.5 + i) * 30;
        ctx.moveTo(x - 40, 0); ctx.lineTo(x + 40, 0); ctx.lineTo(x + 160, s.H); ctx.lineTo(x - 20, s.H);
        ctx.fill();
      }
      for (let i = 0; i < 25; i++) {
        const y = (s.H - ((t * 60 + s.rand(i) * s.H * 3) % (s.H * 1.1)));
        ctx.beginPath();
        ctx.strokeStyle = 'rgba(255,255,255,0.45)';
        ctx.lineWidth = 3;
        ctx.arc(s.rand(i + 50) * s.W + Math.sin(t + i) * 10, y, 6 + 8 * s.rand(i + 70), 0, Math.PI * 2);
        ctx.stroke();
      }
    }
    if (kind === 'sky' || kind === 'land' || kind === 'snow' || kind === 'desert') { // drifting clouds
      for (let i = 0; i < 4; i++) {
        const x = ((s.rand(i) * s.W + t * 20 * (1 + i * 0.3)) % (s.W + 400)) - 200;
        cloud(ctx, x, 180 + i * 140, 70 + 30 * s.rand(i + 9));
      }
    }
    if (kind === 'land' || kind === 'city' || kind === 'desert' || kind === 'snow') { // the ground
      ctx.beginPath();
      ctx.fillStyle = { land: '#7cc26b', city: '#9a9aa5', desert: '#e8b75e', snow: '#f4f8ff' }[kind];
      ctx.moveTo(0, s.H * 0.68);
      for (let x = 0; x <= s.W; x += 60) ctx.lineTo(x, s.H * 0.68 + Math.sin(x / 140) * 18);
      ctx.lineTo(s.W, s.H); ctx.lineTo(0, s.H); ctx.closePath();
      ctx.fill();
      ctx.strokeStyle = '#1d1d1f'; ctx.lineWidth = 6; ctx.stroke();
    }
    if (kind === 'city') { // simple skyline behind the ground line
      for (let i = 0; i < 9; i++) {
        const w = 90 + 40 * s.rand(i + 3), h = 220 + 380 * s.rand(i + 30), x = i * 125 - 20;
        ctx.fillStyle = i % 2 ? '#c9c3d9' : '#b5afc8';
        ctx.strokeStyle = '#1d1d1f'; ctx.lineWidth = 5;
        ctx.beginPath(); ctx.rect(x, s.H * 0.68 - h, w, h); ctx.fill(); ctx.stroke();
        ctx.fillStyle = '#fff3b0';
        for (let r = 0; r < h / 70 - 1; r++) for (let c = 0; c < 2; c++) ctx.fillRect(x + 18 + c * 38, s.H * 0.68 - h + 25 + r * 70, 20, 28);
      }
    }
    if (kind === 'body') { // soft cells floating, for 'inside the human body'
      for (let i = 0; i < 14; i++) {
        ctx.beginPath();
        ctx.fillStyle = 'rgba(255,255,255,0.12)';
        ctx.arc(s.rand(i) * s.W + Math.sin(t * 0.7 + i) * 20, s.rand(i + 40) * s.H, 40 + 60 * s.rand(i + 80), 0, Math.PI * 2);
        ctx.fill();
      }
    }
    if (kind === 'room') { // a floor line, like a simple cartoon room
      ctx.fillStyle = '#d9c4a0';
      ctx.fillRect(0, s.H * 0.7, s.W, s.H * 0.3);
      ctx.strokeStyle = '#1d1d1f'; ctx.lineWidth = 6;
      ctx.beginPath(); ctx.moveTo(0, s.H * 0.7); ctx.lineTo(s.W, s.H * 0.7); ctx.stroke();
    }
    ctx.restore();
  });
}

function cloud(ctx, x, y, r) {
  ctx.save();
  ctx.fillStyle = 'rgba(255,255,255,0.95)';
  ctx.beginPath();
  for (const [dx, dy, k] of [[0, 0, 1], [-0.9, 0.2, 0.7], [0.9, 0.2, 0.75], [-0.4, -0.4, 0.7], [0.4, -0.35, 0.65]]) {
    ctx.moveTo(x + dx * r + k * r, y + dy * r);
    ctx.arc(x + dx * r, y + dy * r, k * r, 0, Math.PI * 2);
  }
  ctx.fill();
  ctx.restore();
}

// ---------- text that reads on any background ----------
// label(s, 'TEXT', { x, y, size, color, at, out }): bold, white (or color) with a black edge, like the captions.
export function label(s, text, o = {}) {
  const size = o.size ?? 72;
  s.draw({ at: o.at ?? 0, out: o.out, enter: o.enter ?? 'pop', id: o.id }, (ctx, life) => {
    ctx.save();
    ctx.translate(o.x ?? s.W / 2, o.y ?? 300);
    const k = 0.8 + 0.2 * Math.min(1, life.p ?? 1);
    ctx.scale(k, k);
    let sz = size;
    ctx.font = `900 ${sz}px Inter, sans-serif`;
    while (ctx.measureText(text).width > (o.maxWidth ?? s.W * 0.85) && sz > 24) { sz -= 4; ctx.font = `900 ${sz}px Inter, sans-serif`; }
    ctx.textAlign = 'center'; ctx.textBaseline = 'middle'; ctx.lineJoin = 'round';
    ctx.lineWidth = sz * 0.16; ctx.strokeStyle = '#000';
    ctx.strokeText(text, 0, 0);
    ctx.fillStyle = { yellow: '#fcd34d', red: '#ff5a5f', green: '#4ade80', blue: '#60a5fa' }[o.color] || o.color || '#ffffff';
    ctx.fillText(text, 0, 0);
    ctx.restore();
  });
}

// ---------- simple props (flat, thick black outline, like the character) ----------
// thing(s, name, { x, y, size, at, out, rotate, color }) — name is one of THINGS below.
// For anything else, build it from s.circle / s.box / s.path / s.icon.
function outline(ctx, fill) { ctx.fillStyle = fill; ctx.fill(); ctx.stroke(); }

const THINGS = {
  sun: (ctx, r, t) => { for (let i = 0; i < 12; i++) { const a = i * Math.PI / 6 + t * 0.3; ctx.beginPath(); ctx.moveTo(Math.cos(a) * r * 1.2, Math.sin(a) * r * 1.2); ctx.lineTo(Math.cos(a) * r * 1.55, Math.sin(a) * r * 1.55); ctx.stroke(); } ctx.beginPath(); ctx.arc(0, 0, r, 0, Math.PI * 2); outline(ctx, '#fcd34d'); },
  earth: (ctx, r) => { ctx.beginPath(); ctx.arc(0, 0, r, 0, Math.PI * 2); outline(ctx, '#4fa3e3'); ctx.save(); ctx.clip(); ctx.fillStyle = '#5cb85c'; for (const [x, y, k] of [[-0.4, -0.3, 0.45], [0.35, 0.25, 0.5], [0.1, -0.6, 0.25]]) { ctx.beginPath(); ctx.ellipse(x * r, y * r, k * r, k * r * 0.7, 0.5, 0, Math.PI * 2); ctx.fill(); } ctx.restore(); ctx.beginPath(); ctx.arc(0, 0, r, 0, Math.PI * 2); ctx.stroke(); },
  moon: (ctx, r) => { ctx.beginPath(); ctx.arc(0, 0, r, 0, Math.PI * 2); outline(ctx, '#e5e5ea'); for (const [x, y, k] of [[-0.3, -0.2, 0.18], [0.3, 0.3, 0.14], [0.2, -0.4, 0.1]]) { ctx.beginPath(); ctx.arc(x * r, y * r, k * r, 0, Math.PI * 2); outline(ctx, '#c7c7cf'); } },
  ship: (ctx, r) => { ctx.beginPath(); ctx.moveTo(-r, 0); ctx.lineTo(r, 0); ctx.lineTo(0.75 * r, 0.45 * r); ctx.lineTo(-0.75 * r, 0.45 * r); ctx.closePath(); outline(ctx, '#2f2f3a'); ctx.beginPath(); ctx.rect(-0.6 * r, -0.3 * r, 1.1 * r, 0.3 * r); outline(ctx, '#ffffff'); for (const x of [-0.4, -0.05, 0.3]) { ctx.beginPath(); ctx.rect(x * r, -0.75 * r, 0.18 * r, 0.45 * r); outline(ctx, '#e8a33c'); } },
  wave: (ctx, r, t) => { ctx.beginPath(); ctx.moveTo(-r * 1.5, 0); for (let i = 0; i <= 6; i++) ctx.quadraticCurveTo(-r * 1.5 + (i + 0.5) * r * 0.5, -r * 0.25 * Math.sin(t * 2 + i), -r * 1.5 + (i + 1) * r * 0.5, 0); ctx.lineTo(r * 1.6, r * 0.6); ctx.lineTo(-r * 1.5, r * 0.6); ctx.closePath(); outline(ctx, '#3b8fd4'); },
  mountain: (ctx, r) => { ctx.beginPath(); ctx.moveTo(-r * 1.2, r * 0.6); ctx.lineTo(0, -r); ctx.lineTo(r * 1.2, r * 0.6); ctx.closePath(); outline(ctx, '#8d8fa3'); ctx.beginPath(); ctx.moveTo(-r * 0.32, -r * 0.55); ctx.lineTo(0, -r); ctx.lineTo(r * 0.32, -r * 0.55); ctx.lineTo(0, -r * 0.42); ctx.closePath(); outline(ctx, '#ffffff'); },
  volcano: (ctx, r, t) => { ctx.beginPath(); ctx.moveTo(-r * 1.2, r * 0.6); ctx.lineTo(-r * 0.3, -r * 0.6); ctx.lineTo(r * 0.3, -r * 0.6); ctx.lineTo(r * 1.2, r * 0.6); ctx.closePath(); outline(ctx, '#8b5a3c'); for (let i = 0; i < 5; i++) { ctx.beginPath(); ctx.arc(Math.sin(t * 3 + i) * r * 0.3, -r * 0.8 - i * r * 0.18 - ((t * 60) % 30), r * (0.25 - i * 0.03), 0, Math.PI * 2); outline(ctx, i % 2 ? '#ff7a1a' : '#555'); } },
  tree: (ctx, r) => { ctx.beginPath(); ctx.rect(-r * 0.12, 0, r * 0.24, r * 0.7); outline(ctx, '#8b5a3c'); ctx.beginPath(); ctx.arc(0, -r * 0.2, r * 0.55, 0, Math.PI * 2); outline(ctx, '#4caf50'); },
  house: (ctx, r) => { ctx.beginPath(); ctx.rect(-r * 0.7, -r * 0.2, r * 1.4, r * 0.9); outline(ctx, '#f2e2c4'); ctx.beginPath(); ctx.moveTo(-r * 0.85, -r * 0.2); ctx.lineTo(0, -r * 0.9); ctx.lineTo(r * 0.85, -r * 0.2); ctx.closePath(); outline(ctx, '#d9534f'); ctx.beginPath(); ctx.rect(-r * 0.15, r * 0.25, r * 0.3, r * 0.45); outline(ctx, '#8b5a3c'); },
  fire: (ctx, r, t) => { const f = 1 + 0.08 * Math.sin(t * 12); ctx.beginPath(); ctx.moveTo(0, -r * f); ctx.bezierCurveTo(r * 0.7, -r * 0.3, r * 0.6, r * 0.6, 0, r * 0.6); ctx.bezierCurveTo(-r * 0.6, r * 0.6, -r * 0.7, -r * 0.3, 0, -r * f); outline(ctx, '#ff7a1a'); ctx.beginPath(); ctx.moveTo(0, -r * 0.3 * f); ctx.bezierCurveTo(r * 0.35, 0, r * 0.3, r * 0.5, 0, r * 0.5); ctx.bezierCurveTo(-r * 0.3, r * 0.5, -r * 0.35, 0, 0, -r * 0.3 * f); outline(ctx, '#fcd34d'); },
  drop: (ctx, r) => { ctx.beginPath(); ctx.moveTo(0, -r); ctx.bezierCurveTo(r * 0.8, -r * 0.1, r * 0.7, r * 0.7, 0, r * 0.7); ctx.bezierCurveTo(-r * 0.7, r * 0.7, -r * 0.8, -r * 0.1, 0, -r); outline(ctx, '#4fb3e8'); },
  heart: (ctx, r, t) => { const b = 1 + 0.06 * Math.max(0, Math.sin(t * 6)); ctx.scale(b, b); ctx.beginPath(); ctx.moveTo(0, r * 0.8); ctx.bezierCurveTo(-r * 1.2, -r * 0.1, -r * 0.6, -r * 0.95, 0, -r * 0.35); ctx.bezierCurveTo(r * 0.6, -r * 0.95, r * 1.2, -r * 0.1, 0, r * 0.8); outline(ctx, '#e5484d'); },
  brain: (ctx, r) => { ctx.beginPath(); ctx.ellipse(0, 0, r, r * 0.75, 0, 0, Math.PI * 2); outline(ctx, '#f7a6c2'); ctx.beginPath(); ctx.moveTo(0, -r * 0.75); ctx.lineTo(0, r * 0.75); for (const [x, y] of [[-0.5, -0.2], [0.5, -0.2], [-0.45, 0.3], [0.45, 0.3]]) { ctx.moveTo(x * r - r * 0.2, y * r); ctx.quadraticCurveTo(x * r, y * r - r * 0.2, x * r + r * 0.2, y * r); } ctx.stroke(); },
  clock: (ctx, r, t) => { ctx.beginPath(); ctx.arc(0, 0, r, 0, Math.PI * 2); outline(ctx, '#ffffff'); ctx.beginPath(); ctx.moveTo(0, 0); ctx.lineTo(Math.cos(t - Math.PI / 2) * r * 0.75, Math.sin(t - Math.PI / 2) * r * 0.75); ctx.moveTo(0, 0); ctx.lineTo(r * 0.4, 0); ctx.stroke(); },
  rock: (ctx, r) => { ctx.beginPath(); ctx.moveTo(-r, r * 0.4); ctx.lineTo(-r * 0.7, -r * 0.4); ctx.lineTo(0, -r * 0.6); ctx.lineTo(r * 0.8, -r * 0.3); ctx.lineTo(r, r * 0.4); ctx.closePath(); outline(ctx, '#9b9ba5'); },
  fish: (ctx, r) => { ctx.beginPath(); ctx.ellipse(0, 0, r, r * 0.5, 0, 0, Math.PI * 2); outline(ctx, '#ff9f43'); ctx.beginPath(); ctx.moveTo(r * 0.9, 0); ctx.lineTo(r * 1.4, -r * 0.4); ctx.lineTo(r * 1.4, r * 0.4); ctx.closePath(); outline(ctx, '#ff9f43'); ctx.beginPath(); ctx.fillStyle = '#1d1d1f'; ctx.arc(-r * 0.5, -r * 0.1, r * 0.1, 0, Math.PI * 2); ctx.fill(); },
  rocket: (ctx, r, t) => { ctx.beginPath(); ctx.moveTo(0, -r); ctx.quadraticCurveTo(r * 0.45, -r * 0.4, r * 0.35, r * 0.5); ctx.lineTo(-r * 0.35, r * 0.5); ctx.quadraticCurveTo(-r * 0.45, -r * 0.4, 0, -r); outline(ctx, '#ffffff'); ctx.beginPath(); ctx.arc(0, -r * 0.2, r * 0.15, 0, Math.PI * 2); outline(ctx, '#60a5fa'); ctx.save(); ctx.translate(0, r * 0.75); THINGS.fire(ctx, r * 0.3 * (1 + 0.1 * Math.sin(t * 20)), t); ctx.restore(); },
  question: (ctx, r) => { ctx.font = `900 ${r * 2}px Inter`; ctx.textAlign = 'center'; ctx.textBaseline = 'middle'; ctx.lineWidth = r * 0.25; ctx.strokeText('?', 0, 0); ctx.fillStyle = '#ff5a5f'; ctx.fillText('?', 0, 0); },
};
export const THING_NAMES = Object.keys(THINGS);

export function thing(s, name, o = {}) {
  if (!THINGS[name]) throw new Error(`unknown thing "${name}" (have: ${THING_NAMES.join(', ')})`);
  const r = (o.size ?? 120) / 2;
  s.draw({ x: o.x ?? s.W / 2, y: o.y ?? s.H / 2, at: o.at ?? 0, out: o.out, enter: o.enter ?? 'pop', id: o.id }, (ctx) => {
    ctx.save();
    if (o.rotate) ctx.rotate((o.rotate * Math.PI) / 180);
    ctx.lineWidth = Math.max(4, r * 0.08);
    ctx.lineJoin = 'round'; ctx.lineCap = 'round';
    ctx.strokeStyle = '#1d1d1f';
    THINGS[name](ctx, r, s.t);
    ctx.restore();
  });
  return { x: o.x, y: o.y, w: r * 2, h: r * 2 };
}

// Twemoji drawings (CC BY 4.0, owner's choice 29 Oct) for animals and objects we have not drawn ourselves:
// emoji(s, 'shark', { x, y, size, at, out, enter, rotate, flip }). Names: cartoon/emoji/NAMES.txt. The file is
// copied into the project's assets/emoji/ before rendering. Each gets the white sticker edge the stickman has, so
// they look like one family; the outlined picture is made once per name and size, then reused every frame.
const STICKERS = new Map();
function sticker(img, size) {
  const key = img.src + '|' + size;
  if (STICKERS.has(key)) return STICKERS.get(key);
  const edge = Math.max(4, Math.round(size * 0.045));
  const c = document.createElement('canvas');
  c.width = c.height = size + edge * 2 + 2;
  const g = c.getContext('2d');
  for (let i = 0; i < 16; i++) {  // white silhouette: the picture drawn around a circle, then painted white
    const a = (i / 16) * Math.PI * 2;
    g.drawImage(img, edge + 1 + Math.cos(a) * edge, edge + 1 + Math.sin(a) * edge, size, size);
  }
  g.globalCompositeOperation = 'source-in';
  g.fillStyle = '#ffffff';
  g.fillRect(0, 0, c.width, c.height);
  g.globalCompositeOperation = 'source-over';
  g.drawImage(img, edge + 1, edge + 1, size, size);
  STICKERS.set(key, c);
  return c;
}

export function emoji(s, name, o = {}) {
  const size = Math.round(o.size ?? 240);
  const img = s.engine.image(`assets/emoji/${name}.svg`);
  s.draw({ x: o.x ?? s.W / 2, y: o.y ?? s.H / 2, at: o.at ?? 0, out: o.out, enter: o.enter ?? 'pop', id: o.id }, (ctx) => {
    const pic = sticker(img, size);
    ctx.save();
    if (o.rotate) ctx.rotate((o.rotate * Math.PI) / 180);
    if (o.flip) ctx.scale(-1, 1);
    ctx.drawImage(pic, -pic.width / 2, -pic.height / 2);
    ctx.restore();
  });
  return { x: o.x, y: o.y, w: size, h: size };
}

// Library pictures (owner's ChatGPT art, 29 Oct; cards in cartoon/art/library.json, copied into the project's
// assets/art/ before rendering). place() is the background of a shot; art() is a detailed object.
const PX_PER_M = 165;  // the stickman at scale 1 is about 1.7 m tall on screen

// Moods drawn over a place: the same picture by day, at night, lit by fire, in the dark...
const MOODS = {
  night: ['rgba(10,20,60,0.45)', 'multiply'], dark: ['rgba(0,0,0,0.55)', 'multiply'],
  fire: ['rgba(255,110,20,0.28)', 'overlay'], cold: ['rgba(120,170,255,0.25)', 'overlay'],
  storm: ['rgba(30,40,60,0.45)', 'multiply'], dusk: ['rgba(255,120,60,0.22)', 'overlay'],
  underwater: ['rgba(0,90,160,0.3)', 'multiply'],
};

export function place(s, name, o = {}) {
  const card = PLACES[name];
  if (!card) throw new Error(`unknown place "${name}" (have: ${Object.keys(PLACES).join(', ')})`);
  if (s.camera) s.camera([]);  // still camera, like background() (captions are never cut off)
  const img = s.engine.image(`assets/art/${card.file}`);
  s.draw({ x: 0, y: 0, at: 0, enter: 'none', sfx: false }, (ctx) => {
    const zoom = o.zoom ?? 1;  // > 1 = closer shot of the same place, centred on o.focus ([x, y] in 0..1)
    const [fx, fy] = o.focus ?? [0.5, 0.6];
    const w = s.W * zoom, h = s.H * zoom;
    ctx.drawImage(img, (s.W - w) * fx, (s.H - h) * fy, w, h);
    const mood = MOODS[o.mood];
    if (mood) {
      ctx.save(); ctx.globalCompositeOperation = mood[1]; ctx.fillStyle = mood[0]; ctx.fillRect(0, 0, s.W, s.H); ctx.restore();
    }
    if (o.flash) {  // lightning or an explosion: a short white flash at these times (seconds in the scene)
      const k = Math.max(0, ...[].concat(o.flash).map((t) => 1 - Math.abs(s.t - s.time(t)) / 0.15));
      if (k > 0) { ctx.fillStyle = `rgba(255,255,255,${0.8 * k})`; ctx.fillRect(0, 0, s.W, s.H); }
    }
  });
  return { floor: card.floor * s.H };
}

// Where feet stand in a place: depth 0 = the back of the open floor, 1 = the front of the picture.
export function floorY(s, name, depth = 0.5) {
  const card = PLACES[name];
  if (!card) throw new Error(`unknown place "${name}"`);
  const top = card.floor * s.H + 40, bottom = s.H * 0.86;
  return top + (bottom - top) * Math.min(1, Math.max(0, depth));
}

// A detailed object, drawn at its real size next to the stickman: art(s, 'car', { x, y, scale }) where y is
// where it stands (its bottom) and scale means the same as hero's scale (a 1.7 m stickman at scale 1).
// `size` (px of height) overrides the real size, e.g. for a close-up.
export function art(s, name, o = {}) {
  const card = ART[name];
  if (!card) throw new Error(`unknown art "${name}" (have: ${Object.keys(ART).join(', ')})`);
  const img = s.engine.image(`assets/art/${card.file}`);
  const h = Math.min(s.H * 1.4, o.size ?? card.height_m * PX_PER_M * (o.scale ?? 1));
  const w = (h * card.w) / card.h;
  s.draw({ x: o.x ?? s.W / 2, y: o.y ?? s.H * 0.8, at: o.at ?? 0, out: o.out, enter: o.enter ?? 'pop', id: o.id }, (ctx) => {
    ctx.save();
    if (o.rotate) ctx.rotate((o.rotate * Math.PI) / 180);
    if (o.flip) ctx.scale(-1, 1);
    ctx.drawImage(img, -w / 2, -h, w, h);  // anchored at its bottom centre, like the stickman's feet
    ctx.restore();
  });
  return { x: o.x, y: o.y, w, h };
}

// Simple props drawn in code, in the same flat cartoon style as the character.
// Like the character, everything depends only on the time.

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

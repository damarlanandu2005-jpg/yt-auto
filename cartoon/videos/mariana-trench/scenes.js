// What happens if you fall into the Mariana Trench? Second Stickman Thoughts Short. The narration and its
// fact-check are from automatic run 40843120092 (Wikipedia: Mariana Trench, Drowning, Barotrauma); the AI-written
// pictures there were text-heavy and one label said "crushed" where the narration says "injure" (rule R2), so
// these scenes were redrawn by hand under the "show, don't write" rules (SCENE_API.md): drawings tell the story,
// at most one short label per scene, made only of spoken words.
import { hero } from './character.js';
import { background, label, thing, words } from './props.js';

const EDGE = '#ffffff';

// the trench seen from the side: a dark V cut into the sea floor, deeper than the frame
function trench(s, o = {}) {
  s.draw({ at: o.at ?? 0, enter: o.enter ?? 'fade' }, (ctx) => {
    ctx.save();
    ctx.lineWidth = 8;
    ctx.strokeStyle = '#1d1d1f';
    ctx.lineJoin = 'round';
    ctx.beginPath(); // sea floor with the trench
    ctx.moveTo(0, 980); ctx.lineTo(330, 1000); ctx.lineTo(470, 1900); ctx.lineTo(610, 1900); ctx.lineTo(750, 1000);
    ctx.lineTo(1080, 980); ctx.lineTo(1080, 1920); ctx.lineTo(0, 1920); ctx.closePath();
    ctx.fillStyle = '#5b4a3a';
    ctx.fill();
    ctx.stroke();
    ctx.beginPath(); // the dark water inside the trench
    ctx.moveTo(338, 1004); ctx.lineTo(474, 1880); ctx.lineTo(606, 1880); ctx.lineTo(742, 1004); ctx.closePath();
    ctx.fillStyle = '#04101f';
    ctx.fill();
    ctx.restore();
  });
}

// bubbles rising from the stickman's mouth while he gasps
function bubbles(s, x, y, at) {
  s.draw({ at, enter: 'none', sfx: false }, (ctx) => {
    const t = s.since(at);
    if (t < 0) return;
    for (let i = 0; i < 9; i++) {
      const life = (t * 0.9 + i * 0.37) % 2.4;
      ctx.beginPath();
      ctx.lineWidth = 4;
      ctx.strokeStyle = 'rgba(255,255,255,0.85)';
      ctx.arc(x + Math.sin(i * 2.1 + t * 3) * 25, y - life * 230, 10 + (i % 3) * 6, 0, Math.PI * 2);
      ctx.stroke();
    }
  });
}

// arrows pushing in from all sides: water pressure
function squeeze(s, x, y, r, at) {
  const pairs = [[[x - r - 230, y], [x - r, y]], [[x + r + 230, y], [x + r, y]],
    [[x, y - r - 230], [x, y - r]], [[x, y + r + 230], [x, y + r]]];
  pairs.forEach(([a, b], i) => s.arrow(a, b, { color: 'blue', width: 14, at: s.time(at) + 0.15 * i }));
}

// a simple pair of lungs, flat colours and a thick outline like the props
function lungs(s, x, y, size, at) {
  s.draw({ x, y, at, enter: 'pop' }, (ctx) => {
    const k = size / 300;
    const shrink = 1 - 0.12 * Math.max(0, Math.sin(s.t * 3));
    ctx.save();
    ctx.scale(k * shrink, k);
    ctx.lineWidth = 9;
    ctx.strokeStyle = '#1d1d1f';
    ctx.fillStyle = '#f7a6b4';
    for (const side of [-1, 1]) {
      ctx.beginPath();
      ctx.moveTo(side * 20, -110);
      ctx.bezierCurveTo(side * 150, -130, side * 160, 120, side * 60, 140);
      ctx.bezierCurveTo(side * 20, 140, side * 15, 0, side * 20, -110);
      ctx.fill();
      ctx.stroke();
    }
    ctx.beginPath(); // windpipe
    ctx.moveTo(0, -200); ctx.lineTo(0, -100);
    ctx.moveTo(0, -100); ctx.lineTo(-20, -110); ctx.moveTo(0, -100); ctx.lineTo(20, -110);
    ctx.stroke();
    ctx.restore();
  });
}

export default {
  hook(s) {
    background(s, 'ocean');
    thing(s, 'wave', { x: 540, y: 230, size: 900, at: 0, enter: 'none' });
    hero(s, { x: 540, y: 1050, scale: 1.6, outline: EDGE, at: 0, enter: 'none',
      moves: [{ at: 0, pose: 'fall', face: 'scared' }, { at: 'mariana', pose: 'fall', face: 'shocked' }] });
    label(s, 'MARIANA TRENCH', { y: 1240, size: 84, color: 'yellow', at: 'mariana' });
    words(s);
  },

  step1(s) {
    background(s, 'ocean');
    trench(s, { at: 0.2 });
    hero(s, { x: 540, y: 820, scale: 1.1, outline: EDGE, at: 0,
      moves: [{ at: 0, pose: 'fall', face: 'scared' }, { at: 'cold', pose: 'scared', face: 'shocked' },
        { at: 'gasping', pose: 'scared', face: 'scared' }] });
    s.number(10935, { x: 540, y: 200, size: 96, suffix: ' metres', color: 'yellow', at: 'depth' });
    s.icon('snowflake', { x: 860, y: 520, size: 150, color: 'blue', at: 'cold' });
    bubbles(s, 560, 470, s.cue('gasping'));
    label(s, '2 MINUTES', { x: 540, y: 330, size: 80, color: 'red', at: 'kill' });
    words(s);
  },

  step2(s) {
    background(s, 'deep');
    // he sinks slowly from the top of the frame towards the middle
    const sink = s.p(0, s.dur, 'linear');
    hero(s, { x: 540, y: 700 + 300 * sink, scale: 1.3, outline: EDGE, at: -1,
      moves: [{ at: 0, pose: 'fall', face: 'sad' }, { at: 'pressure', pose: 'scared', face: 'shocked' }] });
    bubbles(s, 560, 300 + 300 * sink, s.cue('gasping'));
    squeeze(s, 540, 760 + 300 * sink - 230, 170, 'pressure');
    label(s, 'PRESSURE', { y: 240, size: 90, color: 'blue', at: 'pressure' });
    words(s);
  },

  step3(s) {
    background(s, 'deep');
    lungs(s, 680, 640, 420, 'lungs');
    s.icon('ear', { x: 760, y: 1060, size: 170, color: 'pink', at: 'ears' });
    hero(s, { x: 250, y: 1200, scale: 1.0, outline: EDGE, at: 0,
      moves: [{ at: 0, pose: 'sad', face: 'sad' }, { at: 'injuries', pose: 'scared', face: 'scared' }] });
    label(s, 'LUNGS AND EARS', { y: 250, size: 84, color: 'red', at: 'lungs' });
    words(s);
  },

  answer(s) {
    background(s, 'deep');
    hero(s, { x: 540, y: 1180, scale: 1.4, outline: EDGE, at: 0,
      moves: [{ at: 0, pose: 'sad', face: 'sad' }, { at: 'pressure', pose: 'scared', face: 'scared' }] });
    s.icon('snowflake', { x: 240, y: 420, size: 170, color: 'blue', at: 'cold' });
    thing(s, 'drop', { x: 540, y: 420, size: 170, at: 'drowning' });
    s.icon('heart-pulse', { x: 840, y: 420, size: 170, color: 'red', at: 'organs' });
    label(s, 'IN MINUTES', { y: 640, size: 88, color: 'yellow', at: 'minutes' });
    words(s);
  },

  end(s) {
    background(s, 'ocean');
    thing(s, 'wave', { x: 540, y: 230, size: 900, at: 0, enter: 'none' });
    hero(s, { x: 540, y: 1150, scale: 1.6, outline: EDGE, at: 0,
      moves: [{ at: 0, pose: 'think', face: 'thinking' }] });
    thing(s, 'question', { x: 800, y: 560, size: 170, at: 'dare' });
    words(s);
  },
};

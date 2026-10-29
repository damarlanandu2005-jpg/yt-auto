import { hero } from './character.js';
import { background, thing, label, words } from './props.js';

export default {
  hook(s) {
    background(s, 'ocean');
    thing(s, 'ship', { x: 540, y: 1300, size: 300, at: 0 });
    hero(s, { x: 540, y: 1000, scale: 1.4, outline: '#ffffff', at: 0,
      moves: [{ at: 0, pose: 'stand', face: 'thinking' }] });
    words(s);
  },

  step1(s) {
    background(s, 'ocean');
    // Draw iceberg
    s.draw({ x: 300, y: 800, at: 0 }, (ctx) => {
      ctx.beginPath();
      ctx.moveTo(0, 0);
      ctx.lineTo(80, 0);
      ctx.lineTo(120, 80);
      ctx.lineTo(0, 80);
      ctx.closePath();
      ctx.fillStyle = '#ffffff';
      ctx.fill();
      ctx.strokeStyle = '#000000';
      ctx.lineWidth = 4;
      ctx.stroke();
    });
    thing(s, 'wave', { x: 540, y: 1350, size: 150, at: 'shudder' });
    hero(s, { x: 540, y: 1000, scale: 1.4, outline: '#ffffff', at: -1,
      moves: [{ at: 0, pose: 'scared', face: 'scared' }] });
    label(s, 'SHUDDER', { x: 760, y: 300, size: 80, color: 'white', at: 'shudder' });
    words(s);
  },

  step2(s) {
    background(s, 'ocean');
    // Small lifeboats
    thing(s, 'ship', { x: 300, y: 1200, size: 80, at: 0 });
    thing(s, 'ship', { x: 780, y: 1200, size: 80, at: 0 });
    label(s, 'SCARCE', { x: 540, y: 300, size: 80, color: 'red', at: 0 });
    hero(s, { x: 540, y: 1000, scale: 1.3, outline: '#ffffff', at: -1,
      moves: [{ at: 0, pose: 'point', face: 'worried' }] });
    words(s);
  },

  step3(s) {
    background(s, 'ocean');
    // Tilted ship effect via stickman position
    hero(s, { x: 450, y: 1150, scale: 1.2, outline: '#ffffff', at: -1,
      moves: [{ at: 0, pose: 'stand', face: 'shocked' }] });
    s.icon('thermometer', { x: 540, y: 300, size: 100, color: 'blue', at: 0 });
    label(s, '-2°C', { x: 540, y: 220, size: 60, color: 'white', at: 0 });
    words(s);
  },

  step4(s) {
    background(s, 'ocean');
    hero(s, { x: 540, y: 1300, scale: 1.0, outline: '#ffffff', at: 0,
      moves: [{ at: 0, pose: 'fall', face: 'shocked' }] });
    thing(s, 'wave', { x: 540, y: 1350, size: 200, at: 0 });
    s.icon('thermometer', { x: 540, y: 300, size: 100, color: 'blue', at: 0 });
    label(s, 'COLD', { x: 540, y: 220, size: 60, color: 'white', at: 0 });
    words(s);
  },

  end(s) {
    background(s, 'ocean');
    hero(s, { x: 540, y: 1000, scale: 1.4, outline: '#ffffff', at: 0,
      moves: [{ at: 0, pose: 'think', face: 'confused' }] });
    s.icon('question', { x: 540, y: 300, size: 120, color: 'yellow', at: 0 });
    label(s, 'SURVIVAL?', { x: 540, y: 200, size: 80, color: 'yellow', at: 0 });
    words(s);
  },
};
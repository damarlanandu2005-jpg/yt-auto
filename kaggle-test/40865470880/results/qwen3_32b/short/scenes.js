import { hero } from './character.js';
import { background, thing, label, words, blackHole } from './props.js';

export default {
  hook(s) {
    background(s, 'ocean');
    hero(s, { x: 540, y: 1300, scale: 1.6, outline: '#ffffff', at: 0,
      moves: [{ at: 0, pose: 'fall', face: 'scared' }, { at: 'trench', pose: 'think', face: 'confused' }] });
    s.icon('question', { x: 540, y: 300, size: 150, color: 'white', at: 0 });
    words(s);
  },

  step1(s) {
    background(s, 'ocean');
    hero(s, { x: 540, y: 1100, scale: 1.5, outline: '#ffffff', at: -1,
      moves: [{ at: 0, pose: 'fall', face: 'scared' }] });
    thing(s, 'wave', { x: 540, y: 1250, size: 200, at: 0 });
    s.icon('thermometer', { x: 300, y: 400, size: 80, color: 'blue', at: 'cold' });
    label(s, 'COLD SHOCK', { x: 780, y: 300, size: 70, color: 'yellow', at: 'cold' });
    words(s);
  },

  step2(s) {
    background(s, 'deep');
    hero(s, { x: 540, y: 1250, scale: 1.4, outline: '#ffffff', at: -1,
      moves: [{ at: 0, pose: 'fall', face: 'shocked' }] });
    s.draw({ x: 540, y: 700, at: 0 }, (ctx) => {
      ctx.lineWidth = 8;
      ctx.strokeStyle = '#ffffff';
      ctx.beginPath();
      ctx.arc(0, 0, 60, 0, Math.PI * 2);
      ctx.stroke();
    });
    s.arrow([400, 700], [680, 700], { color: 'red', width: 10, at: 'pressure' });
    s.arrow([680, 700], [400, 700], { color: 'red', width: 10, at: 'pressure' });
    label(s, 'HYDROSTATIC PRESSURE', { x: 540, y: 280, size: 70, color: 'red', at: 'pressure' });
    words(s);
  },

  step3(s) {
    background(s, 'deep');
    hero(s, { x: 540, y: 1280, scale: 1.3, outline: '#ffffff', at: -1,
      moves: [{ at: 0, pose: 'fall', face: 'shocked' }] });
    s.draw({ x: 540, y: 700, at: 0 }, (ctx) => {
      ctx.lineWidth = 6;
      ctx.strokeStyle = '#ffffff';
      ctx.beginPath();
      ctx.moveTo(-40, 0);
      ctx.lineTo(40, 0);
      ctx.stroke();
      ctx.beginPath();
      ctx.arc(0, -30, 20, 0, Math.PI * 2);
      ctx.stroke();
    });
    s.arrow([300, 600], [780, 600], { color: 'red', width: 8, at: 'injured' });
    s.arrow([780, 600], [300, 600], { color: 'red', width: 8, at: 'injured' });
    label(s, 'INJURED LUNGS & EARS', { x: 540, y: 280, size: 60, color: 'red', at: 'injured' });
    words(s);
  },

  answer(s) {
    background(s, 'deep');
    hero(s, { x: 540, y: 1300, scale: 1.5, outline: '#ffffff', at: -1,
      moves: [{ at: 0, pose: 'think', face: 'neutral' }] });
    s.draw({ x: 540, y: 600, at: 0 }, (ctx) => {
      ctx.lineWidth = 4;
      ctx.strokeStyle = '#ffffff';
      ctx.beginPath();
      ctx.moveTo(-60, 0);
      ctx.lineTo(60, 0);
      ctx.stroke();
      ctx.beginPath();
      ctx.arc(0, -30, 20, 0, Math.PI * 2);
      ctx.stroke();
      ctx.beginPath();
      ctx.arc(0, 30, 15, 0, Math.PI * 2);
      ctx.stroke();
    });
    words(s);
  },

  end(s) {
    background(s, 'deep');
    hero(s, { x: 540, y: 1250, scale: 1.4, outline: '#ffffff', at: 0,
      moves: [{ at: 0, pose: 'point', face: 'confused' }] });
    s.number(10935, { x: 540, y: 300, size: 60, suffix: 'm', at: 0 });
    s.icon('question', { x: 540, y: 150, size: 120, color: 'white', at: 0 });
    words(s);
  },
};
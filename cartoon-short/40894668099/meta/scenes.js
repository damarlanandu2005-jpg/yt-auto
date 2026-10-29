import { hero } from './character.js';
import { place, floorY, art, background, thing, label, words, s } from './props.js';

export default {
  hook(s) {
    // Titanic deck at night, camera steady
    place(s, 'titanic_deck_night', { mood: 'night', zoom: 1.5, focus: [0.5, 0.6] });
    // Hero standing, eyes wide, wondering
    hero(s, {
      x: 540,
      y: floorY(s, 'titanic_deck_night', 0.8),
      scale: 1.4,
      outline: '#ffffff',
      at: 0,
      moves: [{ at: 0, pose: 'stand', face: 'wow' }]
    });
    // Ship front half visible behind hero
    art(s, 'ship_front_half', { x: 540, y: floorY(s, 'titanic_deck_night', 0.6), scale: 1.6, at: -1 });
    // Label on the spoken word "Titanic"
    label(s, 'TITANIC', { x: 540, y: 300, size: 80, color: 'yellow', at: 'Titanic' });
    words(s);
  },

  step1(s) {
    place(s, 'titanic_deck_night', { mood: 'night', zoom: 1.5, focus: [0.5, 0.6] });
    // Hero pointing at lifeboat, thinking
    hero(s, {
      x: 340,
      y: floorY(s, 'titanic_deck_night', 0.8),
      scale: 1.3,
      outline: '#ffffff',
      at: 0,
      moves: [{ at: 0, pose: 'point', face: 'thinking' }]
    });
    // Crowded lifeboat on water
    art(s, 'lifeboat_crowded', { x: 720, y: floorY(s, 'titanic_deck_night', 0.5), scale: 1.2, at: -1 });
    // Simple iceberg drawn with custom shape
    s.draw({ x: 100, y: 200, at: 0 }, (ctx) => {
      ctx.fillStyle = '#e0f7ff';
      ctx.strokeStyle = '#000000';
      ctx.lineWidth = 4;
      ctx.beginPath();
      ctx.moveTo(0, 120);
      ctx.lineTo(80, 0);
      ctx.lineTo(160, 120);
      ctx.closePath();
      ctx.fill();
      ctx.stroke();
    });
    // Label on the spoken word "lifeboats"
    label(s, 'LIFEBOATS', { x: 720, y: 300, size: 80, color: 'yellow', at: 'lifeboats' });
    words(s);
  },

  step2(s) {
    place(s, 'titanic_deck_night', { mood: 'night', zoom: 1.4, focus: [0.5, 0.7] });
    // Hero falling off the rear poop deck, scared
    hero(s, {
      x: 540,
      y: floorY(s, 'titanic_deck_night', 0.8),
      scale: 1.2,
      outline: '#ffffff',
      at: 0,
      moves: [{ at: 0, pose: 'fall', face: 'scared' }]
    });
    // Splash circle to show icy water
    s.draw({ x: 540, y: floorY(s, 'titanic_deck_night', 0.6), at: 0 }, (ctx) => {
      ctx.fillStyle = '#a0e0ff';
      ctx.strokeStyle = '#000000';
      ctx.lineWidth = 3;
      ctx.beginPath();
      ctx.arc(0, 0, 120, 0, Math.PI * 2);
      ctx.fill();
      ctx.stroke();
    });
    // Small water drop for extra detail
    thing(s, 'drop', { x: 540, y: floorY(s, 'titanic_deck_night', 0.55), size: 60, at: 0.5 });
    // Label on the spoken word "water"
    label(s, 'WATER', { x: 540, y: 250, size: 80, color: 'white', at: 'water' });
    words(s);
  },

  answer(s) {
    // Underwater view, cold water around hero
    background(s, 'deep_sea');
    hero(s, {
      x: 540,
      y: floorY(s, 'deep_sea', 0.9),
      scale: 1.1,
      outline: '#ffffff',
      at: 0,
      moves: [{ at: 0, pose: 'sad', face: 'sad' }]
    });
    // Cold water droplets surrounding hero
    for (let i = 0; i < 6; i++) {
      const angle = (i / 6) * Math.PI * 2;
      const r = 150;
      thing(s, 'drop', {
        x: 540 + r * Math.cos(angle),
        y: floorY(s, 'deep_sea', 0.9) - 100 + r * Math.sin(angle),
        size: 40,
        at: 0.2 + i * 0.1
      });
    }
    words(s);
  },

  end(s) {
    place(s, 'titanic_deck_night', { mood: 'night', zoom: 1.3, focus: [0.5, 0.5] });
    // Hero shrugging, neutral face, looking at the sinking ship silhouette
    hero(s, {
      x: 540,
      y: floorY(s, 'titanic_deck_night', 0.8),
      scale: 1.4,
      outline: '#ffffff',
      at: 0,
      moves: [{ at: 0, pose: 'shrug', face: 'neutral' }]
    });
    // Silhouette of sinking Titanic (using ship_wreck art)
    art(s, 'ship_wreck', { x: 540, y: floorY(s, 'titanic_deck_night', 0.4), scale: 1.8, at: -1, rotate: 0.1 });
    // Label on the spoken word "sinking"
    label(s, 'SINKING', { x: 540, y: 300, size: 80, color: 'red', at: 'sinking' });
    words(s);
  }
};
import {defineConfig} from 'vite';
import {createRequire} from 'node:module';
import preact from '@preact/preset-vite';

const require = createRequire(import.meta.url);
const motionCanvasModule = require('@motion-canvas/vite-plugin');
const motionCanvas = motionCanvasModule.default ?? motionCanvasModule;

export default defineConfig({
  plugins: [
    preact(),
    motionCanvas({
      project: './src/project.ts',
      buildForEditor: true,
    }),
  ],
  server: {
    port: 9000,
    strictPort: true,
  },
});

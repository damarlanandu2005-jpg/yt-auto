import {defineConfig} from 'vite';
import {createRequire} from 'node:module';

const require = createRequire(import.meta.url);
const motionCanvasModule = require('@motion-canvas/vite-plugin');
const motionCanvas = motionCanvasModule.default ?? motionCanvasModule;

export default defineConfig({
  plugins: [
    motionCanvas({
      project: './src/project.ts',
    }),
  ],
  server: {
    port: 9000,
    strictPort: true,
  },
});

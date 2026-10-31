import {defineConfig} from 'vite';
import motionCanvasModule from '@motion-canvas/vite-plugin';
import ffmpegModule from '@motion-canvas/ffmpeg';

// Some Node/Vite combinations expose CommonJS default exports as a nested
// .default property. Normalize both forms before registering the plugins.
const motionCanvas = typeof motionCanvasModule === 'function'
  ? motionCanvasModule
  : (motionCanvasModule as unknown as {default: typeof motionCanvasModule}).default;

const ffmpeg = typeof ffmpegModule === 'function'
  ? ffmpegModule
  : (ffmpegModule as unknown as {default: typeof ffmpegModule}).default;

export default defineConfig({
  plugins: [motionCanvas(), ffmpeg()],
  server: {port: 9000, strictPort: true},
});

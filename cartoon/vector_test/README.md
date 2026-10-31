# 2D cartoon animation prototype

An isolated Motion Canvas experiment for Stickman Thoughts. It does not modify the existing Shorts pipeline.

## Goal

Test a reusable, code-drawn 2D cartoon style: a recurring stickman presenter, illustrated backgrounds, planets, vehicles, props, simple environments, camera framing and timed movement. Everything in the demo is drawn from vector shapes; no FLUX images are used.

## Run locally

Requires Node.js 18+.

```bash
cd cartoon/vector_test
npm install
npm run dev
```

Open the local URL printed by Vite. Use the Motion Canvas editor to preview the scene and render it. The project is configured for a 1080x1920 vertical canvas at 30 fps.

To build-check the TypeScript:

```bash
npm run build
```

## Demo

The sample scene is a short visual explainer: a stickman presenter introduces Earth, the Earth rotates, a rocket passes, and a simple illustrated city appears. The character and all props are reusable vector components.

## Scope and limitations

- This is a visual/technical prototype, not yet connected to the AI script writer, TTS, subtitle timing or existing FFmpeg pipeline.
- It intentionally uses simple shapes so we can evaluate the look and animation system before building a large asset library.
- More detailed hand-drawn objects will need reusable SVG assets or additional vector drawing components.
- The prototype is isolated under `cartoon/vector_test/`; existing production workflows are unchanged.

## Why Motion Canvas?

Motion Canvas is an open-source TypeScript animation library with a real-time editor, designed for explanatory vector animations and voice-over synchronization. See [official documentation](https://motioncanvas.io/docs/).

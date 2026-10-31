import {makeProject} from '@motion-canvas/core';
import earthStory from './scenes/earth-story?scene';

export default makeProject({
  scenes: [earthStory],
  settings: {
    shared: {
      size: [1080, 1920],
      fps: 30,
    },
  },
});

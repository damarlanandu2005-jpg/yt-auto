// Screenshot an HTML test page with the pre-installed Chromium: node shoot.js page.html out.png [width height]
const { chromium } = require('playwright');
const path = require('path');
(async () => {
  const [page, out, w = 1920, h = 1080] = process.argv.slice(2);
  const browser = await chromium.launch();
  const tab = await browser.newPage({ viewport: { width: +w, height: +h } });
  tab.on('console', (m) => console.log(m.text()));
  tab.on('pageerror', (e) => console.error('page error:', e.message));
  await tab.goto(page.startsWith('http') ? page : 'file://' + path.resolve(page));
  await tab.waitForFunction(() => document.title === 'done', null, { timeout: 10000 }).catch(() => console.error('page did not finish'));
  await tab.screenshot({ path: out });
  await browser.close();
})();

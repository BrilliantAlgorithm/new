// Renders thumbnails: thumbnail_vertical.png (1080x1920) and thumbnail_youtube.png (1280x720)
const { chromium } = require('playwright');
const fs = require('fs');
(async () => {
  const b = await chromium.launch(); const p = await b.newPage();
  const errs = []; p.on('pageerror', e => errs.push(e.message));
  await p.goto('file://' + __dirname + '/reel.html?render=1'); await p.waitForTimeout(600);
  for (const [w, h, name] of [[1080, 1920, 'thumbnail_vertical.png'], [1280, 720, 'thumbnail_youtube.png']]) {
    const d = await p.evaluate(([w, h]) => { const c = document.createElement('canvas'); c.width = w; c.height = h; drawThumb(c.getContext('2d'), w, h); return c.toDataURL('image/png'); }, [w, h]);
    fs.writeFileSync(__dirname + '/' + name, Buffer.from(d.split(',')[1], 'base64'));
  }
  console.log('errors:', errs); await b.close();
})();

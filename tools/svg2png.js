// Usage: node svg2png.js in.svg out.png  - rasterise an SVG at 1000px wide with transparency.
const { chromium } = require('playwright'); const fs = require('fs');
(async () => {
  const b = await chromium.launch(); const p = await b.newPage({ viewport: { width: 1200, height: 1200 } });
  const data = fs.readFileSync(process.argv[2]).toString('base64');
  await p.setContent(`<body style="margin:0;background:transparent"><img id="i" style="width:1000px;display:block" src="data:image/svg+xml;base64,${data}"></body>`);
  await p.waitForFunction(() => document.getElementById('i').complete);
  await (await p.$('#i')).screenshot({ path: process.argv[3], omitBackground: true }); await b.close();
})();

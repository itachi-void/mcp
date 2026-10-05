import { chromium } from 'playwright-core';
const out = process.argv[2] || '/tmp/kitchen.png';
const wait = parseInt(process.argv[3]||'6000');
const b = await chromium.launch({ executablePath: '/usr/bin/chromium',
  args: ['--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader','--no-sandbox','--ignore-gpu-blocklist'] });
const pg = await b.newPage({ viewport: { width: 1280, height: 800 }, deviceScaleFactor: 1 });
const errs = [];
pg.on('console', m => { if (m.type()==='error') errs.push(m.text()); });
pg.on('pageerror', e => errs.push('PAGEERR '+e.message));
await pg.goto('http://localhost:3000/', { waitUntil: 'networkidle', timeout: 60000 });
await pg.waitForTimeout(wait);
await pg.screenshot({ path: out });
console.log('SHOT', out);
console.log('ERRORS', errs.slice(0,12).join('\n') || 'none');
await b.close();

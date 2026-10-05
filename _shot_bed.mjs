import { chromium } from 'playwright-core';
const b = await chromium.launch({ executablePath: '/usr/bin/chromium',
  args: ['--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader','--no-sandbox','--ignore-gpu-blocklist'] });
const pg = await b.newPage({ viewport: { width: 1280, height: 800 } });
pg.on('console', m => { if (m.type()==='error') console.log('PAGE-ERR', m.text()); });
await pg.goto('http://localhost:3000/', { waitUntil: 'networkidle', timeout: 60000 });
await pg.waitForTimeout(2000);
await pg.getByRole('button', { name: 'Bedroom' }).click();
await pg.waitForTimeout(7000);
await pg.screenshot({ path: '/tmp/bed_wide.png' });
const cx=640, cy=430;
await pg.mouse.move(cx, cy);
for (let i=0;i<7;i++){ await pg.mouse.wheel(0,-120); await pg.waitForTimeout(120); }
await pg.waitForTimeout(2500);
await pg.screenshot({ path: '/tmp/bed_zoom.png' });
console.log('done');
await b.close();

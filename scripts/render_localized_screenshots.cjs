// Render HTML compositions around real device captures; no synthetic app state.
const { chromium } = require('../website/node_modules/@playwright/test');
const fs = require('node:fs/promises');
const path = require('node:path');
const root = path.resolve(__dirname, '..');
(async () => {
  const locales = JSON.parse(await fs.readFile(path.join(root,'deliverables/localization/coverage.json'),'utf8')).map(row=>row.locale);
  const shots=['home','albums','timeline','keepsakes','settings','editor','voice','transcript'];
  const browser=await chromium.launch({headless:true});
  const page=await browser.newPage({viewport:{width:1920,height:1200},deviceScaleFactor:1});
  const audit=[];
  try {
    for(const locale of locales) for(const shot of shots){
      await page.goto(`http://127.0.0.1:3011/store-assets/screenshots/localized-drafts/${locale}/${shot}.html`,{waitUntil:'load'});
      await page.evaluate(()=>document.fonts.ready);
      const metrics=await page.evaluate(()=>{
        const image=document.querySelector('img'),heading=document.querySelector('h1');
        return {lang:document.documentElement.lang,dir:document.documentElement.dir,width:innerWidth,height:innerHeight,imageLoaded:image.complete&&image.naturalWidth===1920,headlineFits:heading.getBoundingClientRect().height<104};
      });
      if(metrics.lang!==locale||!metrics.imageLoaded||!metrics.headlineFits)throw Error(JSON.stringify({locale,shot,metrics}));
      const destination=path.join(root,`deliverables/store-assets/screenshots/localized-drafts/${locale}/${shot}.jpg`);
      await page.screenshot({path:destination,type:'jpeg',quality:95,fullPage:true});
      audit.push({locale,shot,...metrics,nativeApproved:false});
    }
    await fs.writeFile(path.join(root,'deliverables/reports/website-localization/screenshot-render-audit.json'),JSON.stringify(audit,null,2)+'\n');
    console.log(`${audit.length} actual-capture compositions exported; native review pending`);
  } finally { await browser.close(); }
})().catch(error=>{console.error(error);process.exitCode=1;});

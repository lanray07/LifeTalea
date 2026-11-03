// Browser fallback after in-app automation timed out. Checks rendered editorial copy.
const {chromium}=require('../website/node_modules/@playwright/test');
const fs=require('node:fs/promises');
const path=require('node:path');
const assert=require('node:assert/strict');
const root=path.resolve(__dirname,'..');
(async()=>{
  const locales=JSON.parse(await fs.readFile(path.join(root,'deliverables/localization/coverage.json'),'utf8')).map(row=>row.locale).filter(locale=>!process.argv[2]||locale===process.argv[2]);
  assert.ok(locales.length,'Unknown locale filter');
  const output=path.join(root,'deliverables/reports/website-localization-polish');
  await fs.mkdir(output,{recursive:true});
  const browser=await chromium.launch({headless:true});
  const page=await browser.newPage();const errors=[],requests=[],checks=[];
  page.on('response',response=>{if(response.status()>=400)requests.push({status:response.status(),url:response.url()});});
  page.on('pageerror',error=>errors.push(error.message));
  page.on('console',message=>{if(['error','warning'].includes(message.type()))errors.push(message.text());});
  try {
    for(const locale of locales){
      const dictionary=JSON.parse(await fs.readFile(path.join(root,`website/src/dictionaries/${locale}.json`),'utf8'));
      for(const viewport of [{width:1280,height:900},{width:390,height:844}]){
        await page.setViewportSize(viewport);
        for(const slug of ['features','voice-transcription','privacy']){
          const response=await page.goto(`http://localhost:3000/${locale}/${slug}/`,{waitUntil:'load'});
          assert.equal(response.status(),200);
          await page.evaluate(()=>document.fonts.ready);
          const actual=await page.evaluate(()=>({lang:document.documentElement.lang,dir:document.documentElement.dir,width:document.documentElement.clientWidth,scroll:document.documentElement.scrollWidth,h1:document.querySelector('main h1')?.textContent,text:document.querySelector('main')?.textContent,overlay:!!document.querySelector('nextjs-portal')}));
          assert.equal(actual.lang,locale);assert.equal(actual.dir,locale==='ar'?'rtl':'ltr');
          assert.ok(actual.scroll<=actual.width+1,`${locale}/${slug}: horizontal overflow`);
          assert.equal(actual.h1,dictionary.articles[slug].title);assert.ok(!actual.overlay);
          for(const section of dictionary.articles[slug].sections)assert.ok(actual.text.includes(section.body),`${locale}/${slug}: stale or missing paragraph`);
          checks.push({locale,slug,viewport,status:'PASS'});
          if(slug==='features'&&((locale==='fr-FR'&&viewport.width===1280)||(locale==='ar'&&viewport.width===390)))await page.screenshot({path:path.join(output,`${locale}-features-${viewport.width}.jpg`),type:'jpeg',quality:92,fullPage:true});
        }
      }
    }
    await page.goto('http://localhost:3000/fr-FR/features/',{waitUntil:'load'});
    await page.getByRole('combobox').selectOption('de-DE');
    await page.waitForURL('**/de-DE/features/');
    checks.push({interaction:'French to German preserves /features/',status:'PASS'});
    await page.getByRole('navigation').getByRole('link',{name:'Datenschutz',exact:true}).click();
    await page.waitForURL('**/de-DE/privacy/');
    assert.equal(await page.locator('main h1').textContent(),'Datenschutz beginnt beim Speicherort Ihrer Geschichten');
    checks.push({interaction:'German header navigation renders the privacy article',status:'PASS'});
    await fs.writeFile(path.join(output,process.argv[2]?'subset-checks.json':'checks.json'),JSON.stringify({status:errors.length?'FAIL':'PASS',date:'2026-11-03',environment:'Playwright Chromium; http://localhost:3000; in-app browser timeout fallback',pageChecks:checks.filter(check=>check.locale).length,consoleErrors:errors,failedRequests:requests,nativeApproved:false,checks},null,2)+'\n');
    assert.deepEqual(errors,[],JSON.stringify(requests.slice(0,8)));
    console.log(`${checks.filter(check=>check.locale).length} rendered page/viewport checks and article-preserving language switch passed; no console warnings/errors`);
  } finally {await browser.close();}
})().catch(error=>{console.error(error);process.exitCode=1;});

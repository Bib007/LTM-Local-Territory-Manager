/* Exercise the actual Pages bundle under a subpath with the network isolated. */
'use strict';
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const {chromium} = require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const root = path.resolve(__dirname, '../dist/demo');
const out = process.env.LTM_BROWSER_OUTPUT;
const origin = 'https://ltm.demo.test';
const pages = ['home','desk','territories','map','publishers','tasks','followups','addresses','reports','settings'];

async function navigate(page, name) {
  if (await page.locator('#menu').isVisible() && await page.locator('#menu').getAttribute('aria-expanded') === 'false') {
    await page.locator('#menu').click();
  }
  await page.locator(`nav [data-go="${name}"]`).click();
  assert.equal(await page.locator(`nav [data-go="${name}"]`).getAttribute('aria-current'), 'page');
}

async function setAppearance(page, mode) {
  const menu = page.locator('#menu');
  if (await menu.isVisible()) await menu.click();
  await page.locator('#appearanceChoice').selectOption(mode);
  if (await menu.isVisible()) await menu.click();
  assert.equal(await page.locator('html').getAttribute('data-theme'), mode);
}

async function fits(page, label) {
  assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1), label);
}

async function shot(page, name) {
  if (!out) return;
  fs.mkdirSync(out, {recursive:true});
  await page.screenshot({path:path.join(out, name + '.png')});
}

(async () => {
  const browser = await chromium.launch({args:['--no-sandbox'], executablePath:process.env.LTM_CHROMIUM});
  try {
    for (const width of [320,390,768,1440]) {
      const context = await browser.newContext({viewport:{width,height:950}, hasTouch:width<=768});
      const page = await context.newPage(), errors = [], unexpected = [];
      page.on('pageerror', error => errors.push(error.message));
      await context.route('**/*', route => {
        const url = new URL(route.request().url());
        if (url.hostname === 'tile.openstreetmap.org') return route.fulfill({status:404,body:''});
        const name = url.pathname.slice('/project/'.length) || 'index.html';
        if (url.origin !== origin || !url.pathname.startsWith('/project/') || !fs.existsSync(path.join(root,name))) {
          unexpected.push(url.href);
          return route.abort();
        }
        return route.fulfill({path:path.join(root,name)});
      });
      await page.clock.setFixedTime(new Date('2026-11-06T12:00:00Z'));
      await page.goto(origin+'/project/');
      await page.locator('.dashboardHero').waitFor();
      assert.match(await page.locator('#notice').innerText(), /DEMO/);

      for (const lang of ['da','en']) {
        await page.locator('#language').selectOption(lang);
        for (const theme of ['light','dark']) {
          await setAppearance(page,theme);
          for (const target of pages) {
            await navigate(page,target);
            await fits(page,`${lang}/${theme}/${target}/${width} overflow`);
          }
          await navigate(page,'reports');
          for (const mode of ['calendar','service','rolling']) {
            await page.locator(`[data-mode="${mode}"]`).click();
            assert.equal(await page.locator(`[data-mode="${mode}"]`).getAttribute('aria-pressed'),'true');
            assert.equal(await page.locator('.metrics strong').count(),6);
            assert.equal(await page.locator('#reportMap .leaflet-overlay-pane path').count(),25);
            assert.equal(await page.locator('#reportMap .leaflet-control-zoom').count(),0);
            assert.match(await page.locator('.reportSummary').innerText(), /DEMO/);
            await fits(page,`${lang}/${theme}/${mode}/${width} overflow`);
          }
          assert.equal(await page.locator('#calendarYear').count(),0);
          await page.locator('[data-mode=calendar]').click();
          await page.locator('#calendarYear').selectOption('2025');
          assert.match(await page.locator('.reportSummary h2').innerText(), /2025$/);
          await page.locator('#calendarYear').selectOption('2026');
          await page.locator('[data-mode=service]').click();
          await shot(page,`demo-report-${lang}-${theme}-${width}`);
          if (width===1440 && out) {
            await page.locator('.reportScreenMap').evaluate(n=>n.scrollIntoView({block:'center'}));
            await shot(page,`demo-map-${lang}-${theme}-${width}`);
            await page.evaluate(()=>scrollTo(0,0));
          }
          await page.locator('[data-mode=history]').click();
          assert.equal(await page.locator('.historyTable tbody tr').count(),24);
          await fits(page,`${lang}/${theme}/history/${width} overflow`);
          const search = page.locator('#historySearch');
          await search.fill('not-a-demo-card');
          assert.match(await page.locator('.empty').innerText(),lang==='da'?/Ingen kort/:/No cards/);
          assert.equal(await search.evaluate(n => n===document.activeElement),true);
          await search.fill('100');
          assert.equal(await page.locator('.historyTable tbody tr').count(),1);
          await shot(page,`demo-history-${lang}-${theme}-${width}`);
          await search.fill('');
          await page.locator('[data-mode=visits]').click();
          assert.equal(await page.locator('[data-do=visit]').count(),2);
        }
      }

      await page.locator('[data-mode=history]').click();
      await page.locator('#historySearch').fill('100');
      await page.locator('[data-do=correct-loan][data-id=loan-0]').click();
      await page.locator('[data-form=preview-correction] select').selectOption('person-3');
      await page.getByRole('button',{name:'Preview correction'}).click();
      assert.match(await page.locator('#dialog').innerText(),/Before · Demo · Anna[\s\S]*After · Demo · Mikkel/);
      await page.getByRole('button',{name:'Confirm and save'}).click();
      assert.match(await page.locator('.historyLoan').first().innerText(),/Demo · Mikkel/);

      // Returned and active loans are separate, including older hidden rows.
      await page.locator('[data-mode=history]').click();
      await page.locator('#historySearch').fill('100');
      await page.getByText('1 earlier assignments',{exact:true}).click();
      const returned = page.locator('[data-do=delete-loan][data-id=old-loan-0-2]');
      await returned.click();
      const form = page.locator('[data-form=delete-loan]');
      assert.match(await page.locator('#dialog').innerText(),/Card 100[\s\S]*Demo · Sofie[\s\S]*Returned/);
      if (width===1440 || width===390) await shot(page,'demo-delete-en-dark-'+width);
      await form.getByRole('button',{name:'Cancel'}).click();
      assert.equal(await returned.count(),1);
      await page.getByText('1 earlier assignments',{exact:true}).click();
      await returned.click();
      const before = await page.evaluate(() => ({dates:data.completions.map(x=>x.date), notes:data.notes}));
      await form.getByRole('button',{name:'Delete assignment'}).click();
      assert.equal(await returned.count(),0);
      assert.equal(await page.locator('[data-do=delete-loan][data-id=old-loan-0-1]').count(),1);
      assert.deepEqual(await page.evaluate(() => ({dates:data.completions.map(x=>x.date), notes:data.notes})),before);
      await page.getByText('All recorded completions',{exact:true}).click();
      assert.match(await page.locator('.historyTable details[open]').innerText(), /known completion/);
      await page.locator('[data-do=delete-loan][data-id=loan-0]').click();
      await form.getByRole('button',{name:'Delete assignment'}).click();
      assert.equal(await form.locator('select').evaluate(n=>n.validity.valueMissing),true);
      await form.getByLabel('Where is the physical card kept?').selectOption('folder');
      await form.getByRole('button',{name:'Delete assignment'}).click();
      assert.equal(await page.evaluate(() => M.position(data,card('card-0'))),'folder');

      // Forms, map filters, print entry point and persisted role boundaries.
      await page.locator('[data-mode=visits]').click();
      await page.locator('[data-do=visit]').first().click();
      await page.locator('[data-form=visit] [name=note]').fill('Fictional CO note');
      await page.locator('[data-form=visit]').getByRole('button',{name:'Save'}).click();
      await page.getByText('Fictional CO note',{exact:true}).waitFor();
      await page.locator('[data-mode=service]').click();
      await page.evaluate(() => {window.print = () => {window.demoPrinted = true;};});
      await page.locator('[data-do=print-report]').click();
      assert.equal(await page.evaluate(() => window.demoPrinted),true);
      await page.emulateMedia({media:'print'});
      assert.equal(await page.locator('.reportMark:visible').count(),3);
      assert.equal(await page.locator('#reportMap').isVisible(),false);
      assert.equal(await page.locator('.reportPrintMap:visible polygon').count(),24);
      await page.emulateMedia({media:'screen'});
      await navigate(page,'map');
      await page.locator('#color').selectOption('age');
      assert.match(await page.locator('.mapLegend').innerText(), /Under 90 days/);
      assert.equal(await page.locator('#overviewMap .leaflet-overlay-pane path').count(),24);
      await navigate(page,'desk');
      await page.locator('[data-do=assign][data-id=card-0]').click();
      await page.locator('[data-form=assign] button.primary').click();
      await page.locator('[data-do=return][data-id=card-0]').click();
      await page.locator('[data-form=return] textarea').fill('Fictional return note');
      await page.locator('[data-form=return] button.primary').click();
      await page.locator('[data-do=assign][data-id=card-0]').waitFor();
      await navigate(page,'tasks');
      await page.getByText('Fictional return note',{exact:true}).waitFor();
      await navigate(page,'territories');
      await page.locator('[data-do=new-card]').click();
      await page.locator('[data-form=create] [name=number]').fill('DEMO999');
      await page.locator('[data-form=create] button.primary').click();
      await page.locator('#search').fill('DEMO999');
      assert.equal(await page.locator('.cardRow').count(),1);

      // Rapid navigation must not leave a redraw on a removed map.
      await page.evaluate(() => {for(let i=0;i<20;i++){screen='reports';render();screen='home';render();}});
      await page.evaluate(() => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve))));
      await setAppearance(page,'light');
      await page.reload();
      await page.locator('.dashboardHero').waitFor();
      assert.equal(await page.locator('html').getAttribute('data-theme'),'light');
      assert.match(await page.locator('.brandWordmark').getAttribute('src'),/brand-logo-light/);
      assert.equal(await page.evaluate(() => data.loans.some(x=>x.id==='old-loan-0-2')),false);
      await page.emulateMedia({colorScheme:'light'});
      await page.evaluate(() => Theme.set('system'));
      assert.equal(await page.locator('html').getAttribute('data-theme'),'light');
      await page.emulateMedia({colorScheme:'dark'});
      await page.waitForFunction(() => document.documentElement.dataset.theme==='dark');
      if (await page.locator('#menu').isVisible()) await page.locator('#menu').click();
      await page.locator('#demoRole').selectOption('assistant');
      assert.equal(await page.locator('nav [data-go=reports]').count(),0);
      assert.equal(await page.locator('[data-do=delete-loan]').count(),0);
      assert.deepEqual(errors,[]);
      assert.deepEqual(unexpected,[]);
      await context.close();
      console.log(`Fictional demo ${width}px: both languages and themes, Pages bundle, report periods/map, history, local forms and role boundaries passed.`);
    }
  } finally {
    await browser.close();
  }
})().catch(error => {console.error(error);process.exitCode=1;});

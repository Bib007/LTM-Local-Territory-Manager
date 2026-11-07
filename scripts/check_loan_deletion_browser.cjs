'use strict';
const assert = require('node:assert/strict');
const path = require('node:path');
const {spawn} = require('node:child_process');
const {createInterface} = require('node:readline');
const {chromium, webkit} = require(process.env.PLAYWRIGHT_MODULE || 'playwright');

(async () => {
  const child = spawn(process.env.PYTHON || 'python3', [path.join(__dirname, 'fixtures/loan_deletion_server.py')]);
  child.stderr.pipe(process.stderr);
  let browser;
  try {
    const f = await new Promise((resolve, reject) => {
      const timer = setTimeout(() => reject(Error('Fixture timeout')), 15000);
      createInterface({input: child.stdout}).once('line', line => {
        clearTimeout(timer);
        resolve(JSON.parse(line));
      });
      child.once('exit', code => {
        clearTimeout(timer);
        reject(Error('Fixture exit ' + code));
      });
    });
    const engine = process.env.LTM_BROWSER_ENGINE === 'webkit' ? webkit : chromium;
    browser = await engine.launch(process.env.LTM_CHROME && engine===chromium?{executablePath:process.env.LTM_CHROME}:{});
    const errors = [];
    async function open(cookie) {
      const context = await browser.newContext({viewport: {width: 1440, height: 950}});
      await context.addInitScript(() => localStorage.setItem('ltm-language', 'da'));
      await context.route('**/*', route => new URL(route.request().url()).origin === f.origin ? route.continue() : route.abort());
      await context.addCookies([cookie]);
      const page = await context.newPage();
      page.on('pageerror', error => errors.push(String(error)));
      await page.goto(f.origin);
      await page.waitForFunction(() => typeof state !== 'undefined' && state && SaveStatus.kind === 'saved');
      await page.waitForFunction(() => PersonalGuide.data !== null);
      const later = page.locator('[data-personal-guide=later]');
      if (await later.count()) await later.click();
      return page;
    }
    const a = await open(f.admin);
    const b = await open(f.admin);
    const reader = await open(f.reader);
    const deleteButton = (page, id) => page.locator(`[data-action="delete"][data-module="loans"][data-id="${id}"]`);
    const form = a.locator('#deleteLoanForm');
    const dialog = a.locator('#dialog');
    async function history(page) {
      await page.locator('[data-navigation="2:0"]').click();
      await page.locator('[data-work="report-tab"][data-value="Historik"]').click();
    }
    await history(reader);
    assert.equal(await reader.locator('.historyLoan').count(), 7);
    assert.equal(await reader.locator('[data-action=delete][data-module=loans]').count(), 0);
    const forbidden = await reader.evaluate(async id => {
      const response = await fetch('/api/mutate', {
        method: 'POST', headers: {'Content-Type': 'application/json', 'X-Distrikt-Token': token},
        body: JSON.stringify({action: 'delete', data: {module: 'loans', id, history_revision: state.revision, location: 'box'},
          profile_snapshot: state.profile.snapshot})
      });
      return response.status;
    }, f.active);
    assert.equal(forbidden, 403);

    await history(a);
    const before = await a.evaluate(() => ({completions: state.completions, notes: state.notes}));
    await a.getByText('3 tidligere udleveringer', {exact: true}).click();
    await deleteButton(a, f.mistake).click();
    assert.match(await dialog.innerText(), /Kort F42[\s\S]*Fictional mistaken[\s\S]*4\.10\.2025[\s\S]*Afleveret/);
    await form.getByRole('button', {name: 'Annuller'}).click();
    assert.equal(await dialog.isVisible(), false);
    assert.equal(await deleteButton(a, f.mistake).evaluate(button => button === document.activeElement), true);

    await deleteButton(a, f.mistake).click();
    assert.ok(await form.getAttribute('data-history-token'),'The viewed history owns a scoped delete token');
    // A background/local setting save must not force repeated history reloads.
    await b.evaluate(async()=>{await refresh();await mutate('print.profile.save',{side:'front',profile:defaultPrintProfile('front')},{close:false});});
    assert.notEqual(await a.evaluate(()=>state.revision),await b.evaluate(()=>state.revision));
    await form.getByRole('button', {name: 'Slet udlevering'}).click();
    await form.waitFor({state: 'hidden'});
    assert.equal(await deleteButton(a, f.mistake).count(), 0);
    for (const id of [f.older, f.neighbor, f.recent, f.latest, f.active]) {
      assert.equal(await deleteButton(a, id).count(), 1);
    }
    assert.deepEqual(await a.evaluate(() => ({completions: state.completions, notes: state.notes})), before);
    await a.locator('[data-work="report-tab"][data-value="Rapport"]').click();
    await a.locator('#serviceYear').selectOption('2026');
    const s13 = a.locator('.s13Original');
    assert.match(await s13.innerText(), /Fictional same-day neighbor/);
    assert.doesNotMatch(await s13.innerText(), /Fictional mistaken/);
    assert.match(await s13.innerText(), /4\.10\.2025/);
    assert.ok(await a.evaluate(async () => (await (await api('/api/export/s13?year=2026&language=da')).text()).startsWith('%PDF')));

    await a.locator('#navigationLanguage').selectOption('en');
    await history(a);
    await deleteButton(a, f.archived).click();
    assert.match(await dialog.innerText(), /Delete erroneous assignment\?[\s\S]*Card F43[\s\S]*archived after merging[\s\S]*Unknown[\s\S]*Returned/);
    await a.keyboard.press('Escape');
    await dialog.waitFor({state: 'hidden'});
    await deleteButton(a, f.archived).click();
    await form.getByRole('button', {name: 'Delete assignment'}).click();
    await form.waitFor({state: 'hidden'});
    assert.equal(await deleteButton(a, f.archived).count(), 0);

    await deleteButton(a, f.active).click();
    assert.match(await dialog.innerText(), /Fictional active[\s\S]*Still assigned/);
    await form.getByRole('button', {name: 'Delete assignment'}).click();
    assert.equal(await form.locator('select').evaluate(select => select.validity.valueMissing), true);
    await form.getByLabel('Where is the physical card kept?').selectOption('folder');
    await b.evaluate(async id => {
      await refresh();
      await mutate('loan.finish', {id, date: '2025-10-11', complete: true, retain: true}, {close: false});
    }, f.active);
    await form.getByRole('button', {name: 'Delete assignment'}).click();
    await form.getByRole('alert').getByText('History has changed. Refresh and select the assignment again.').waitFor();
    await form.getByRole('button', {name: 'Cancel'}).click();
    await a.evaluate(() => refresh());
    await deleteButton(a, f.active).click();
    await form.getByLabel('Where is the physical card kept?').selectOption('folder');
    await form.getByRole('button', {name: 'Delete assignment'}).click();
    await form.waitFor({state: 'hidden'});
    assert.deepEqual(await a.evaluate(id => [!!loanFor(id), cardLocation(card(id))], f.card), [false, 'folder']);

    await a.locator('[data-navigation="2:2"]').click();
    await a.locator('[data-work=settings-tab][data-value=data]').click();
    await a.locator('.line').filter({hasText: 'F42 · Fictional active · 2025-10-09'}).getByRole('button', {name: 'Restore', exact: true}).click();
    await a.waitForFunction(id => loanFor(id)?.cycle_start === '2025-10-11' && !card(id).in_folder, f.card);

    await history(a);
    await deleteButton(a, f.active).click();
    await form.getByLabel('Where is the physical card kept?').selectOption('box');
    await form.getByRole('button', {name: 'Delete assignment'}).click();
    await form.waitFor({state: 'hidden'});
    await a.locator('[data-navigation="1:0"]').click();
    await a.locator(`[data-card-row="${f.card}"] [data-action="issue"]`).click();
    await a.locator('#issueForm [name=publisher_name]').fill('Fictional new assignment');
    await a.locator('#issueForm button:not([type=button])').click();
    await a.waitForFunction(id => publisherName(loanFor(id)?.publisher_id) === 'Fictional new assignment', f.card);
    await a.locator('[data-navigation="2:2"]').click();
    await a.locator('[data-work=settings-tab][data-value=data]').click();
    await a.locator('.line').filter({hasText: 'F42 · Fictional active · 2025-10-09'}).getByRole('button', {name: 'Restore', exact: true}).click();
    await a.locator('#toast').getByText('The card already has a new active assignment.', {exact: true}).waitFor();
    assert.equal(await a.evaluate(id => publisherName(loanFor(id)?.publisher_id), f.card), 'Fictional new assignment');
    assert.deepEqual(errors, []);
    console.log('History: exact same-day deletion, cancellation and focus, report and PDF, archived/unknown assignment, profile authorization, stale confirmation, physical location and recovery passed.');
  } finally {
    await browser?.close();
    child.kill();
  }
})().catch(error => {
  console.error(error);
  process.exitCode = 1;
});

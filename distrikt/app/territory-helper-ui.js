'use strict';

const TerritoryHelperUI = {
  allowed() {
    return !!state?.beta && (!state.profile || (!state.profile.desk_only &&
      ProfilesUI.canAction('setup.territory-helper.preview')));
  },
  button() {
    return this.allowed()
      ? '<button type="button" data-th-import="open">' + ui('Importér fra Territory Helper') + '</button>'
      : '';
  },
  fields: [
    ['cards', 'Distrikter · CSV', '.csv'],
    ['locations', 'Lokationer · CSV', '.csv'],
    ['ib', 'IB · CSV', '.csv'],
    ['publishers', 'Forkyndere · CSV', '.csv'],
    ['assignments', 'Tildelinger → Altid · CSV', '.csv'],
    ['geometry', 'Distrikter · JSON', '.json,.geojson'],
    ['kml', 'Distrikter · KML', '.kml']
  ],
  open() {
    if (!this.allowed()) return;
    this.session = null;
    this.uploads = [];
    openDialog(`<h2>${ui('Importér fra Territory Helper')}</h2>
      <ol><li>${ui('Åbn Importér / Eksportér i Territory Helper.')}</li>
        <li>${ui('Hent distrikter, lokationer, IB, forkyndere og Tildelinger → Altid som CSV.')}</li>
        <li>${ui('Hent også distrikter som JSON eller KML, hvis du vil have kortgrænserne med.')}</li>
        <li>${ui('Slip alle filerne i feltet. LTM sorterer dem efter type.')}</li></ol>
      <form id="thFilesForm">
        <div id="thDropZone" class="panel" style="border-style:dashed">
          <label for="thFiles">${ui('Træk eksportfiler hertil, eller vælg filer')}</label>
          <input id="thFiles" type="file" accept=".csv,.json,.geojson,.kml" multiple>
          <ul id="thFileList" aria-live="polite"></ul>
        </div>
        <p class="hint">${ui('Vælg mindst distrikternes CSV eller JSON. Tilføj de øvrige filer, hvis du vil have deres data med.')}</p>
        <p id="formError" role="alert"></p>
        <div class="actions"><button class="primary">${ui('Forhåndsvis kort')}</button><button type="button" data-action="close">${ui('Annuller')}</button></div>
      </form>`);
  },
  addFiles(files) {
    for (const file of files) {
      if (!this.uploads.some(old => old.name === file.name && old.size === file.size && old.lastModified === file.lastModified))
        this.uploads.push(file);
    }
    this.showFiles();
  },
  showFiles() {
    const list = el('thFileList');
    list.innerHTML = this.uploads.map((file, index) =>
      `<li>${esc(file.name)} <button type="button" data-th-import="remove" data-index="${index}">${ui('Fjern')}</button></li>`).join('');
  },
  async preview(form) {
    if (!this.allowed()) return;
    const button = form.querySelector('button.primary');
    if (button.disabled) return;
    button.disabled = true;
    const active = () => form.isConnected && el('dialog').open;
    try {
      const selected = this.uploads.slice();
      if (!selected.length || selected.length > this.fields.length)
        throw Error('Vælg én eksportfil på højst 2 MB pr. filtype.');
      const uploads = [];
      for (const file of selected) {
        if (file.size > 2000000) throw Error('Vælg én eksportfil på højst 2 MB pr. filtype.');
        const bytes = new Uint8Array(await file.arrayBuffer());
        let content;
        if (bytes[0] === 255 && bytes[1] === 254 || bytes[0] === 254 && bytes[1] === 255)
          content = new TextDecoder(bytes[0] === 255 ? 'utf-16le' : 'utf-16be').decode(bytes);
        else {
          try { content = new TextDecoder('utf-8', {fatal: true}).decode(bytes); }
          catch { content = new TextDecoder('windows-1252').decode(bytes); }
        }
        uploads.push({name: file.name, content});
      }
      if (!active()) return;
      const response = await api('/api/mutate', {action: 'setup.territory-helper.preview', data: {uploads}});
      const {result} = await response.json();
      if (!active()) return;
      this.session = {...result, saved: new Set(), index: 0};
      this.show();
    } catch (error) {
      if (active()) I18n.errorContent(el('formError'), error.status === 404
        ? 'Denne server har ikke filimporten. Luk LTM Beta helt, og start den nye beta igen.' : error);
    } finally {
      if (active()) button.disabled = false;
    }
  },
  outline(polygon, locations) {
    const locationsWithPoints = locations.filter(a => Number.isFinite(a.lng) && Number.isFinite(a.lat));
    const raw = [...polygon, ...locationsWithPoints.map(a => [a.lng, a.lat])];
    if (!raw.length) return '<p class="hint">' + ui('Ingen geografisk grænse i importen.') + '</p>';
    const cos = Math.cos(raw[0][1] * Math.PI / 180);
    const west = Math.min(...raw.map(p => p[0])), east = Math.max(...raw.map(p => p[0]));
    const south = Math.min(...raw.map(p => p[1])), north = Math.max(...raw.map(p => p[1]));
    const width = (east - west) * cos, height = north - south;
    const scale = Math.min(300 / (width || 0.00001), 156 / (height || 0.00001));
    const xy = ([lng, lat]) => [((lng - west) * cos * scale + (320 - width * scale) / 2).toFixed(2),
      ((north - lat) * scale + (176 - height * scale) / 2).toFixed(2)];
    const dots = locationsWithPoints.map(p => {
      const [x, y] = xy([p.lng, p.lat]);
      return `<circle cx="${x}" cy="${y}" r="2.5" fill="#477596"/>`;
    }).join('');
    return `<svg width="320" height="176" viewBox="0 0 320 176" style="max-width:100%" role="img" ${I18n.attribute('aria', 'Distriktsgrænse')}>
      <polygon points="${polygon.map(p => xy(p).join(',')).join(' ')}" fill="#477596" fill-opacity=".16" stroke="#477596" stroke-width="2"/>${dots}</svg>`;
  },
  list(label, rows, renderer) {
    return `<details><summary>${ui(label)} · ${rows.length}</summary>
      ${rows.length ? '<ul>' + rows.map(row => '<li>' + renderer(row) + '</li>').join('') + '</ul>' : ''}</details>`;
  },
  show() {
    const session = this.session, card = session.cards[session.index];
    const address = row => esc([row.road, row.number, row.floor, row.door, row.postcode, row.date, row.note].filter(Boolean).join(' · '));
    const warnings = this.fields.filter(([name]) => session.unmatched[name]).map(([name, label]) =>
      `<li>${ui(label)} · ${session.unmatched[name]}</li>`).join('');
    const sources = this.fields.filter(([name]) => session.sources?.[name]).map(([name, label]) =>
      `<li>${ui(label)} · ${esc(session.sources[name])}</li>`).join('');
    openDialog(`<h2>${ui('Gennemgå importen kort for kort')}</h2>
      <p>${ui('Godkendte kort')} · ${session.saved.size} / ${session.cards.length}</p>
      ${sources ? `<details><summary>${ui('Genkendte eksportfiler')}</summary><ul>${sources}</ul></details>` : ''}
      ${warnings ? `<details><summary>${ui('Rækker uden entydigt kort')}</summary><ul>${warnings}</ul></details>` : ''}
      <label for="thReviewCard">${ui('Distriktskort')}</label>
      <select id="thReviewCard">${session.cards.map((item, i) =>
        `<option value="${i}"${i === session.index ? ' selected' : ''}>${esc(item.number)} ${esc(item.name)}${session.saved.has(i) ? ' ✓' : ''}</option>`).join('')}</select>
      <h3>${esc(card.number)} ${esc(card.name)}</h3>${this.outline(card.polygon, card.locations)}
      ${card.note ? `<details><summary>${ui('Importeret kortnotat')}</summary><p style="white-space:pre-wrap;overflow-wrap:anywhere">${esc(card.note)}</p></details>` : ''}
      ${this.list('Lokationer', card.locations, address)}
      ${this.list('IB', card.ib, address)}
      ${this.list('Tildelinger', card.assignments, row => esc([row.publisher, row.assigned, row.returned].filter(Boolean).join(' · ')) +
        (row.completed ? ' · ' + ui('Gennemgået') : ''))}
      ${card.loan_review.some(row => row.status === 'outside') ? `<p class="hint">${ui('Tildelinger uden for LTM’s historikperiode springes over.')}</p>` : ''}
      ${card.errors.length ? `<ul>${card.errors.map(error => `<li>${esc(I18n.text(error))}</li>`).join('')}</ul>` : ''}
      <p id="formError" role="alert"></p>
      <div class="actions"><button type="button" data-th-import="previous" ${session.index === 0 ? 'disabled' : ''}>${ui('Forrige')}</button>
        <button type="button" data-th-import="next" ${session.index === session.cards.length - 1 ? 'disabled' : ''}>${ui('Næste')}</button>
        <button type="button" class="primary" data-th-import="save" ${card.errors.length || session.saved.has(session.index) ? 'disabled' : ''}>${ui('Godkend og gem dette kort')}</button>
        <button type="button" data-action="close">${ui('Luk')}</button></div>`);
  },
  async save(button) {
    const session = this.session, index = session.index;
    if (button.disabled || session.saved.has(index)) return;
    const generation = openDialog.generation;
    button.disabled = true;
    try {
      await mutate('setup.territory-helper.apply', {token: session.token, index}, {close: false});
      session.saved.add(index);
      if (this.session !== session || openDialog.generation !== generation || !el('dialog').open) return;
      if (index < session.cards.length - 1) session.index++;
      this.show();
    } catch {
      if (button.isConnected) button.disabled = false;
    }
  }
};

document.addEventListener('submit', event => {
  if (event.target.id !== 'thFilesForm') return;
  event.preventDefault();
  TerritoryHelperUI.preview(event.target);
});
document.addEventListener('change', event => {
  if (event.target.id === 'thFiles') {
    TerritoryHelperUI.addFiles(event.target.files);
    event.target.value = '';
    return;
  }
  if (event.target.id !== 'thReviewCard') return;
  TerritoryHelperUI.session.index = Number(event.target.value);
  TerritoryHelperUI.show();
});
document.addEventListener('dragover', event => {
  if (event.target.closest?.('#thDropZone')) event.preventDefault();
});
document.addEventListener('drop', event => {
  if (!event.target.closest?.('#thDropZone')) return;
  event.preventDefault();
  if (event.dataTransfer?.files.length) TerritoryHelperUI.addFiles(event.dataTransfer.files);
});
document.addEventListener('click', event => {
  const button = event.target.closest('[data-th-import]');
  if (!button || button.disabled) return;
  const action = button.dataset.thImport;
  if (action === 'open') return TerritoryHelperUI.open();
  if (action === 'remove') {
    TerritoryHelperUI.uploads.splice(Number(button.dataset.index), 1);
    return TerritoryHelperUI.showFiles();
  }
  if (action === 'save') return TerritoryHelperUI.save(button);
  TerritoryHelperUI.session.index += action === 'next' ? 1 : -1;
  TerritoryHelperUI.show();
});

'use strict';

const TerritoryHelperUI = {
  allowed() {
    return state?.territory_helper_available && location.hostname === '127.0.0.1' &&
      (!state.profile || (!state.profile.desk_only && ProfilesUI.has('connections.manage',
        'cards.view', 'cards.edit', 'geo.view', 'geo.edit')));
  },
  button() {
    return this.allowed()
      ? '<button type="button" data-th-import="open">' + ui('Importér fra Territory Helper') + '</button>'
      : '';
  },
  open() {
    if (!this.allowed()) return;
    openDialog(`<h2>${ui('Importér fra Territory Helper')}</h2>
      <p>${ui('Hent nummer, navn og grænse for ét distriktskort.')}</p>
      <form id="thImportForm">
        <label for="thCongregation">${ui('Menigheds-id i Territory Helper')}</label>
        <input id="thCongregation" name="congregation" inputmode="numeric" pattern="[1-9][0-9]{0,9}" maxlength="10" required>
        <label for="thNumber">${ui('Kortnummer')}</label>
        <input id="thNumber" name="number" maxlength="10" required>
        <div class="actions"><button class="primary">${ui('Log ind og hent kort')}</button></div>
        <p id="thImportStatus" role="status"></p>
      </form>`);
  },
  async load(form) {
    const button = form.querySelector('button');
    if (button.disabled || !form.reportValidity() || !this.allowed()) return;
    const feedback = el('thImportStatus'), generation = openDialog.generation;
    const active = () => form.isConnected && el('dialog').open && openDialog.generation === generation;
    const popup = window.open('about:blank', '_blank', 'popup,width=600,height=700');
    if (!popup) {
      I18n.errorContent(feedback, 'Tillad pop-op-vinduer for at logge ind hos Territory Helper.');
      return;
    }
    button.disabled = true;
    feedback.textContent = I18n.text('Venter på login hos Territory Helper…');
    let dispose = () => {};
    try {
      const {authorize_url, state: expected} = await (await api('/api/territory-helper/begin',
        Object.fromEntries(new FormData(form)))).json();
      if (!active()) return;
      const url = new URL(authorize_url);
      if (url.origin !== 'https://www.territoryhelper.com' || url.pathname !== '/api/authpkce')
        throw Error('Territory Helper returnerede et ugyldigt svar.');
      const code = await new Promise((resolve, reject) => {
        const result = event => {
          if (event.origin !== location.origin || event.source !== popup ||
              event.data?.type !== 'ltm-territory-helper' || event.data.state !== expected) return;
          if (event.data.error || !event.data.code) reject(Error('Login hos Territory Helper blev afbrudt.'));
          else resolve(event.data.code);
        };
        const expires = Date.now() + 300000;
        const timer = setInterval(() => {
          if (!active() || popup.closed) reject(Error('Login hos Territory Helper blev afbrudt.'));
          else if (Date.now() >= expires) reject(Error('Login hos Territory Helper er udløbet. Start importen igen.'));
        }, 500);
        dispose = () => {
          clearInterval(timer);
          window.removeEventListener('message', result);
        };
        window.addEventListener('message', result);
        popup.location.replace(url.href);
      });
      popup.close();
      dispose();
      if (!active()) return;
      feedback.textContent = I18n.text('Henter distriktskort…');
      const card = await (await api('/api/territory-helper/preview', {state: expected, code})).json();
      if (active()) this.show(card);
    } catch (error) {
      if (active()) I18n.errorContent(feedback, error);
    } finally {
      dispose();
      if (!popup.closed) popup.close();
      if (active()) button.disabled = false;
    }
  },
  show(card) {
    const points = card.polygon.map(([lng, lat]) => [lng * Math.cos(card.polygon[0][1] * Math.PI / 180), -lat]);
    const west = Math.min(...points.map(p => p[0])), north = Math.min(...points.map(p => p[1]));
    const width = Math.max(...points.map(p => p[0])) - west;
    const height = Math.max(...points.map(p => p[1])) - north;
    const scale = Math.min(300 / width, 156 / height);
    const outline = points.map(([x, y]) => [((x - west) * scale + (320 - width * scale) / 2).toFixed(2),
      ((y - north) * scale + (176 - height * scale) / 2).toFixed(2)].join(',')).join(' ');
    openDialog(`<h2>${ui('Forhåndsvis distriktskort')}</h2>
      <p><strong>${esc(card.number)}</strong> ${esc(card.name)}</p>
      <svg width="320" height="176" viewBox="0 0 320 176" style="max-width:100%" role="img" ${I18n.attribute('aria', 'Distriktsgrænse')}>
        <polygon points="${outline}" fill="#477596" fill-opacity=".16" stroke="#477596" stroke-width="2"/>
      </svg>
      <p>${ui('Kortet gemmes som under opbygning. Gennemgå grænsen og tilføj adresser, før det udleveres.')}</p>
      <p id="formError" role="alert"></p>
      <div class="actions"><button type="button" id="thSaveCard" class="primary">${ui('Gem som under opbygning')}</button>
        <button type="button" data-action="close">${ui('Annuller')}</button></div>`);
    const save = el('thSaveCard');
    save.addEventListener('click', async () => {
      save.disabled = true;
      try {
        await mutate('geo.assign', {...card, address_ids: [], planned: true},
          {message: I18n.text('Kort under opbygning gemt')});
      } catch {
        if (save.isConnected) save.disabled = false;
      }
    });
  }
};

if (location.pathname === '/territory-helper-return') {
  const query = new URLSearchParams(location.search);
  history.replaceState(null, '', location.pathname);
  window.opener?.postMessage({type: 'ltm-territory-helper', state: query.get('state'),
    code: query.get('code'), error: query.get('error')}, location.origin);
} else {
  document.addEventListener('click', event => {
    if (event.target.closest('[data-th-import="open"]')) TerritoryHelperUI.open();
  });
  document.addEventListener('submit', event => {
    if (event.target.id !== 'thImportForm') return;
    event.preventDefault();
    TerritoryHelperUI.load(event.target);
  });
}

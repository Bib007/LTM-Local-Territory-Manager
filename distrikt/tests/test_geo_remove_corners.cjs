'use strict';
// Fictional editor drafts. All deletion goes through the actual Leaflet handlers.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
let markers = [], stopped = 0;
const nodes = {geoSelection: {innerHTML: ''}};
const context = {
  document: {addEventListener() {}},
  window: {addEventListener() {}},
  el: id => nodes[id],
  ui: text => text,
  I18n: {text: text => text, format: (text, values) => text.replace('{number}', values.number)},
  L: {
    divIcon: options => options,
    marker(point, options) {
      const marker = {point, options, events: {}, addTo() {markers.push(this); return this;},
        on(event, handler) {this.events[event] = handler; return this;}};
      return marker;
    },
    polygon: () => ({addTo() {return this;}}),
    polyline: () => ({addTo() {return this;}}),
    DomEvent: {stopPropagation() {stopped++;}}
  }
};
vm.createContext(context);
for (const name of ['geo.js', 'main-boundary.js']) {
  vm.runInContext(fs.readFileSync(path.join(__dirname, '../app', name), 'utf8'), context);
}
const geo = vm.runInContext('GeoUI', context);
const main = vm.runInContext('MainBoundaryUI', context);
context.MainBoundaryUI = main;
const saved = [[10,55], [10.02,55], [10.02,55.02], [10,55.02]];
geo.map = {getBounds: () => ({pad: () => ({contains: () => true})})};
geo.draftLayer = {clearLayers() {markers = [];}};
let panels = 0;
geo.updatePanel = () => {panels++;};
main.panel = () => {panels++;};
(async () => {
  for (const whole of [false, true]) {
    geo.whole = whole;
    geo.polygon = saved.map(point => [...point]);
    geo.ids = new Set(['fictional-address']);
    geo.dirty = false;
    if (whole) await main.handle('erase');
    else await geo.handle('erase');
    assert.equal(geo.mode, 'erase');
    assert.equal(geo.dirty, false, 'choosing the tool does not change the draft');
    assert.equal(markers.length, 4);
    assert.equal(markers[1].options.keyboard, true);
    assert.equal(markers[1].options.title, 'Fjern hjørne 2');
    markers[1].events.click({originalEvent: {}});
    assert.deepEqual(JSON.parse(JSON.stringify(geo.polygon)), [saved[0], saved[2], saved[3]]);
    assert.equal(geo.dirty, true);
    assert.equal(markers.length, 3, 'remaining marker indices are rebuilt');
    markers[0].events.click({originalEvent: {}});
    assert.equal(geo.polygon.length, 2);
    assert.equal(geo.ids.has('fictional-address'), true);
    assert.equal(saved.length, 4, 'the saved polygon is separate from the draft');
    geo.removeCorner(-1);
    geo.removeCorner(99);
    assert.equal(geo.polygon.length, 2);
  }
  assert.equal(stopped, 4, 'a tap cannot also append a map corner');
  assert.ok(panels >= 6);
  console.log('Corner removal passes for individual cards and the whole boundary.');
})().catch(error => {console.error(error); process.exitCode = 1;});

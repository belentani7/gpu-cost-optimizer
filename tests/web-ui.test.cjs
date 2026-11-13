const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const model = require('../docs/calculator.js');

class Element {
  constructor(id = '') {
    this.id = id;
    this.value = '';
    this.checked = false;
    this.hidden = false;
    this.textContent = '';
    this.dataset = {};
    this.style = {};
    this.children = [];
    this.listeners = {};
    this.files = [];
    this.attributes = {};
  }
  addEventListener(name, callback) { this.listeners[name] = callback; }
  append(...items) { this.children.push(...items); }
  replaceChildren(...items) { this.children = items; }
  setAttribute(name, value) { this.attributes[name] = value; }
  removeAttribute(name) { delete this.attributes[name]; }
  click() { this.clicked = true; }
  focus() { this.focused = true; }
}

function createApp() {
  const ids = [
    'workflow-file', 'load-sample', 'clear-draft', 'app-status', 'estimate-form',
    'workflow-name', 'pipeline', 'model', 'scheduler-type', 'steps', 'width',
    'height', 'batch-size', 'gpu', 'safety-checker', 'remember-draft', 'results',
    'results-title', 'metrics', 'stage-list', 'comparison-rows', 'recommendation',
    'export-workflow', 'export-result',
  ];
  const elements = Object.fromEntries(ids.map((id) => [id, new Element(id)]));
  elements.results.hidden = true;
  elements.steps.value = '30';
  elements.width.value = '1024';
  elements.height.value = '1024';
  elements['batch-size'].value = '1';
  elements.gpu.value = 'a100';
  const document = {
    getElementById: (id) => elements[id],
    createElement: (tag) => new Element(tag),
  };
  const saved = new Map();
  const downloads = [];
  const context = {
    document,
    GpuCostOptimizer: model,
    localStorage: {
      getItem: (key) => saved.get(key) || null,
      setItem: (key, value) => saved.set(key, value),
      removeItem: (key) => saved.delete(key),
    },
    URL: { createObjectURL: (blob) => { downloads.push(blob); return 'blob:test'; }, revokeObjectURL: () => {} },
    Blob: class Blob { constructor(parts, options) { this.parts = parts; this.options = options; } },
    setTimeout,
    Intl,
    console,
  };
  const source = fs.readFileSync(path.join(__dirname, '../docs/site.js'), 'utf8');
  vm.runInNewContext(source, context, { filename: 'docs/site.js' });
  return { elements, saved, downloads };
}

test('sample workflow calculates, compares GPUs, and enables reproducible exports', () => {
  const { elements, downloads } = createApp();
  elements['load-sample'].listeners.click();
  elements['estimate-form'].listeners.submit({ preventDefault() {} });

  assert.equal(elements.results.hidden, false);
  assert.match(elements['results-title'].textContent, /example_character_generation/);
  assert.equal(elements['stage-list'].children.length, 5);
  assert.equal(elements['comparison-rows'].children.length, 7);
  assert.match(elements.recommendation.textContent, /estimated/i);

  elements['export-workflow'].listeners.click();
  elements['export-result'].listeners.click();
  assert.equal(downloads.length, 2);
  assert.equal(JSON.parse(downloads[0].parts[0]).guidance_scale, 7.5);
  assert.equal(JSON.parse(downloads[1].parts[0]).pricing.status, 'historical_reference');
});

test('invalid edits keep the last estimate visible and explain the failure', () => {
  const { elements } = createApp();
  elements['load-sample'].listeners.click();
  elements['estimate-form'].listeners.submit({ preventDefault() {} });
  const lastTitle = elements['results-title'].textContent;

  elements.steps.value = '1001';
  elements['estimate-form'].listeners.submit({ preventDefault() {} });

  assert.equal(elements.results.hidden, false);
  assert.equal(elements['results-title'].textContent, lastTitle);
  assert.equal(elements['app-status'].dataset.kind, 'error');
  assert.match(elements['app-status'].textContent, /steps must be an integer/i);
  assert.match(elements.results.attributes['aria-label'], /Last valid estimate/);
});

test('valid JSON imports preserve unedited fields in workflow export', async () => {
  const { elements, downloads } = createApp();
  const input = elements['workflow-file'];
  input.files = [{ text: async () => JSON.stringify({
    name: 'imported-workflow',
    scheduler: { type: 'euler_a', steps: 24 },
    resolution: [512, 512],
    custom_metadata: { owner: 'local-user' },
  }) }];

  await input.listeners.change({ currentTarget: input });
  assert.equal(elements['workflow-name'].value, 'imported-workflow');
  elements['estimate-form'].listeners.submit({ preventDefault() {} });
  elements['export-workflow'].listeners.click();

  assert.deepEqual(JSON.parse(downloads[0].parts[0]).custom_metadata, { owner: 'local-user' });
});

test('public page presents the free core and optional proposed service rates', () => {
  const html = fs.readFileSync(path.join(__dirname, '../docs/index.html'), 'utf8');

  assert.match(html, /Base[\s\S]*?Free/);
  assert.match(html, /Support[\s\S]*?€89\s*\/\s*month/);
  assert.match(html, /Managed[\s\S]*?€149\s*\/\s*month/);
  assert.match(html, /Consulting[\s\S]*?€89\s*\/\s*hour/);
  assert.match(html, /proposed/i);
  assert.match(html, /No core feature is paywalled/i);
});


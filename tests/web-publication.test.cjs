const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');

const root = path.join(__dirname, '..');

test('Vercel serves the real static landing without a legacy build', () => {
  const config = JSON.parse(fs.readFileSync(path.join(root, 'vercel.json'), 'utf8'));
  assert.equal(config.builds, undefined);
  assert.deepEqual(config.rewrites, [{ source: '/', destination: '/docs/index.html' }]);
});

test('landing renders the actual offline calculator and one accessible main/footer', () => {
  const html = fs.readFileSync(path.join(root, 'docs/index.html'), 'utf8');
  assert.match(html, /<main\b[^>]*id="top"[^>]*>[\s\S]*<\/main>/);
  assert.equal((html.match(/<\/main>/g) || []).length, 1);
  assert.equal((html.match(/<footer\b/g) || []).length, 1);
  for (const id of ['estimate-form', 'workflow-file', 'gpu', 'results', 'comparison-rows']) {
    assert.match(html, new RegExp('id="' + id + '"'));
  }
  for (const asset of ['site.css', 'calculator.js', 'site.js']) {
    assert.ok(html.includes('"' + asset + '"'), 'Missing calculator asset: ' + asset);
    assert.ok(fs.existsSync(path.join(root, 'docs', asset)));
  }
  assert.doesNotMatch(html, /Hero Shader WebGL/);
});

test('Pages artifact includes the landing assets', () => {
  const workflow = fs.readFileSync(path.join(root, '.github/workflows/deploy-pages.yml'), 'utf8');
  assert.match(workflow, /cp -R assets brand _site\//);
  assert.match(workflow, /path: _site/);
});

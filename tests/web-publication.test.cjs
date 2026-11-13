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

test('landing executes its WebGL block as JavaScript', () => {
  const html = fs.readFileSync(path.join(root, 'docs/index.html'), 'utf8');
  assert.match(html, /<main>\s*[\s\S]*<\/main>/);
  assert.match(html, /<script>\s*\/\* Hero Shader WebGL \*\//);
  assert.match(html, /\}\)\(\);\s*<\/script>\s*<!-- page-fix:1 -->/);
  assert.doesNotMatch(html, /<\/footer>\s*\/\* Hero Shader WebGL \*\//);
  assert.match(html, /content="\/brand\/og-image\.svg"/);
  assert.match(html, /href="\/assets\/favicon\.svg"/);
});

test('Pages artifact includes the landing assets', () => {
  const workflow = fs.readFileSync(path.join(root, '.github/workflows/deploy-pages.yml'), 'utf8');
  assert.match(workflow, /cp -R assets brand _site\//);
  assert.match(workflow, /path: _site/);
});

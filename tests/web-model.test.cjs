const test = require('node:test');
const assert = require('node:assert/strict');
const model = require('../docs/calculator.js');

const sample = {
  name: 'example_character_generation',
  pipeline: 'stable-diffusion',
  model: 'sd-xl-base',
  scheduler: { type: 'euler_a', steps: 30 },
  resolution: [768, 768],
  batch_size: 1,
  guidance_scale: 7.5,
  safety_checker: true,
  vae_tiling: false,
};

test('browser profile mirrors Python heuristic for the canonical workflow', () => {
  const result = model.profileWorkflow(sample, 'a100');

  assert.equal(result.workflow_name, 'example_character_generation');
  assert.equal(result.gpu, 'a100');
  assert.deepEqual(result.steps.map((step) => step.step_name), [
    'vae_encode', 'text_encode', 'denoise', 'vae_decode', 'safety_check',
  ]);
  assert.equal(result.total_seconds, 1.351);
  assert.equal(result.vram_estimate_gb, 6.68);
});

test('comparison includes each GPU and marks VRAM feasibility', () => {
  const rows = model.compareGpus({ ...sample, resolution: [4096, 4096], batch_size: 40 });

  assert.equal(rows.length, 7);
  assert.ok(rows.every((row) => row.estimated_vram_gb > row.vram_gb));
  assert.ok(rows.every((row) => row.meets_vram === false));
});

test('rejects unknown GPUs and invalid workflow bounds', () => {
  assert.throws(() => model.profileWorkflow(sample, 'made-up'), /Unknown GPU/);
  assert.throws(() => model.validateWorkflow({ ...sample, resolution: [0, 512] }), /resolution/);
  assert.throws(() => model.validateWorkflow({ ...sample, scheduler: { steps: 1001 } }), /steps/);
  assert.throws(() => model.validateWorkflow({ ...sample, batch_size: 4097 }), /batch_size/);
});

test('result export identifies simulated model and historical rates', () => {
  const result = model.buildResult(sample, 'a100');

  assert.equal(result.model.kind, 'simulated');
  assert.equal(result.pricing.status, 'historical_reference');
  assert.match(result.disclaimer, /not a benchmark/i);
  assert.equal(result.inputs.name, sample.name);
});

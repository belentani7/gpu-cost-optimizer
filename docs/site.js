/* Offline calculator controls for docs/index.html. No workflow data leaves this page. */
(function startGpuOptimizerSite(root) {
  'use strict';

  const model = root.GpuCostOptimizer;
  if (!model || !root.document) return;

  const byId = (id) => root.document.getElementById(id);
  const fields = {
    name: 'workflow-name',
    pipeline: 'pipeline',
    model: 'model',
    scheduler_type: 'scheduler-type',
    steps: 'steps',
    width: 'width',
    height: 'height',
    batch_size: 'batch-size',
    gpu: 'gpu',
    safety_checker: 'safety-checker',
  };
  const storageKey = 'gpuopt.workflow.v1';
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

  let workflowBase = {};
  let lastWorkflow = null;
  let lastResult = null;

  function setStatus(message, kind) {
    const status = byId('app-status');
    status.textContent = message;
    status.dataset.kind = kind || 'info';
  }

  function clone(value) {
    return JSON.parse(JSON.stringify(value));
  }

  function applyWorkflow(workflow) {
    const value = clone(workflow);
    const scheduler = value.scheduler || {};
    const resolution = value.resolution || [512, 512];
    byId(fields.name).value = value.name || '';
    byId(fields.pipeline).value = value.pipeline || '';
    byId(fields.model).value = value.model || '';
    byId(fields.scheduler_type).value = scheduler.type || 'euler_a';
    byId(fields.steps).value = String(scheduler.steps === undefined ? 30 : scheduler.steps);
    byId(fields.width).value = String(resolution[0]);
    byId(fields.height).value = String(resolution[1]);
    byId(fields.batch_size).value = String(value.batch_size === undefined ? 1 : value.batch_size);
    byId(fields['safety_checker']).checked = Boolean(value.safety_checker);
    const gpu = value.target_gpu && model.GPUS[model.normalizeGpu
      ? model.normalizeGpu(value.target_gpu)
      : String(value.target_gpu).toLowerCase().replace(/[-\s]/g, '')];
    byId(fields.gpu).value = gpu ? String(value.target_gpu).toLowerCase().replace(/[-\s]/g, '') : 'a100';
    workflowBase = value;
  }

  function readWorkflow() {
    const workflow = clone(workflowBase);
    const scheduler = workflow.scheduler && typeof workflow.scheduler === 'object' && !Array.isArray(workflow.scheduler)
      ? workflow.scheduler
      : {};
    workflow.name = byId(fields.name).value.trim() || 'unnamed';
    workflow.pipeline = byId(fields.pipeline).value.trim();
    workflow.model = byId(fields.model).value.trim();
    scheduler.type = byId(fields.scheduler_type).value.trim() || 'euler_a';
    scheduler.steps = Number(byId(fields.steps).value);
    workflow.scheduler = scheduler;
    workflow.resolution = [Number(byId(fields.width).value), Number(byId(fields.height).value)];
    workflow.batch_size = Number(byId(fields.batch_size).value);
    workflow.safety_checker = byId(fields.safety_checker).checked;
    return workflow;
  }

  function saveDraft() {
    if (!byId('remember-draft').checked) return;
    try {
      root.localStorage.setItem(storageKey, JSON.stringify(readWorkflow()));
    } catch (error) {
      setStatus(`Could not save this draft on the device: ${error.message}`, 'error');
    }
  }

  function element(tag, text, className) {
    const node = root.document.createElement(tag);
    if (text !== undefined) node.textContent = text;
    if (className) node.className = className;
    return node;
  }

  function money(value, digits) {
    return new Intl.NumberFormat(undefined, {
      style: 'currency', currency: 'USD', minimumFractionDigits: digits,
      maximumFractionDigits: digits,
    }).format(value);
  }

  function renderResult(workflow, gpu) {
    const result = model.buildResult(workflow, gpu);
    const selected = result.comparisons.find((row) => row.gpu === gpu);
    const feasible = selected && selected.meets_vram;
    const metrics = byId('metrics');
    metrics.replaceChildren();
    [
      ['Simulated runtime', `${result.profile.total_seconds.toFixed(3)} s`, ''],
      ['Estimated VRAM', `${result.profile.vram_estimate_gb.toFixed(2)} GB`, feasible ? 'metric-fit' : 'metric-no-fit'],
      ['Estimated cost / run', money(selected.estimated_cost, 6), ''],
    ].forEach(([label, value, className]) => {
      const item = element('div');
      item.append(element('dt', label), element('dd', value, className));
      metrics.append(item);
    });

    const stageList = byId('stage-list');
    stageList.replaceChildren();
    const longest = Math.max(...result.profile.steps.map((step) => step.elapsed_seconds), 0.0001);
    result.profile.steps.forEach((step) => {
      const row = element('li');
      const name = element('span', step.step_name, 'stage-name');
      const track = element('span', undefined, 'stage-track');
      const fill = element('span', undefined, 'stage-fill');
      fill.style.width = `${Math.max(0, Math.min(100, step.elapsed_seconds / longest * 100))}%`;
      track.append(fill);
      row.append(name, track, element('span', `${step.elapsed_seconds.toFixed(4)} s`, 'stage-value'));
      stageList.append(row);
    });

    const comparisons = byId('comparison-rows');
    comparisons.replaceChildren();
    result.comparisons.forEach((row) => {
      const tr = element('tr');
      if (row.gpu === gpu) tr.dataset.selected = 'true';
      const values = [
        row.gpu.toUpperCase(),
        money(row.price_per_hour, 2),
        `${row.estimated_time_seconds.toFixed(3)} s`,
        money(row.estimated_cost, 6),
        `${row.estimated_vram_gb.toFixed(2)} / ${row.vram_gb} GB`,
      ];
      values.forEach((value) => tr.append(element('td', value)));
      tr.append(element('td', row.meets_vram ? 'Fits estimate' : 'Over capacity', row.meets_vram ? 'fit-yes' : 'fit-no'));
      comparisons.append(tr);
    });

    const recommendation = result.comparisons.find((row) => row.meets_vram);
    byId('recommendation').textContent = recommendation
      ? `Lowest estimated cost among GPUs that fit this VRAM heuristic: ${recommendation.gpu.toUpperCase()} at ${money(recommendation.estimated_cost, 6)} per run. This is not a provider quote.`
      : 'No listed GPU fits the estimated VRAM requirement. Increase memory or revise the workflow before renting compute.';
    byId('results-title').textContent = `Estimate: ${result.workflow_name}`;
    byId('results').hidden = false;
    byId('results').removeAttribute('aria-label');
    lastWorkflow = clone(workflow);
    lastResult = result;
    setStatus('Estimate updated. Timing and VRAM are simulated; bundled prices are historical references.', 'success');
  }

  function download(filename, data) {
    const blob = new root.Blob([JSON.stringify(data, null, 2) + '\n'], { type: 'application/json' });
    const url = root.URL.createObjectURL(blob);
    const anchor = root.document.createElement('a');
    anchor.href = url;
    anchor.download = filename;
    anchor.click();
    root.setTimeout(() => root.URL.revokeObjectURL(url), 0);
  }

  byId('load-sample').addEventListener('click', () => {
    applyWorkflow(sample);
    setStatus('Sample workflow loaded. Adjust its fields and calculate an estimate.', 'info');
  });

  byId('estimate-form').addEventListener('submit', (event) => {
    event.preventDefault();
    try {
      const workflow = readWorkflow();
      model.validateWorkflow(workflow);
      const gpu = byId(fields.gpu).value;
      renderResult(workflow, gpu);
      saveDraft();
    } catch (error) {
      setStatus(`Unable to calculate: ${error.message}`, 'error');
      byId('results').setAttribute('aria-label', 'Last valid estimate; the latest calculation failed');
    }
  });

  byId('workflow-file').addEventListener('change', async (event) => {
    const input = event.currentTarget || byId('workflow-file');
    const file = input.files && input.files[0];
    if (!file) return;
    try {
      const imported = JSON.parse(await file.text());
      model.validateWorkflow(imported);
      applyWorkflow(imported);
      setStatus('Workflow imported and validated. Calculate to update the estimate.', 'success');
    } catch (error) {
      setStatus(`Could not import workflow: ${error.message}`, 'error');
    } finally {
      input.value = '';
    }
  });

  byId('export-workflow').addEventListener('click', () => {
    if (!lastWorkflow) return setStatus('Calculate a valid workflow before exporting it.', 'error');
    download('gpuopt-workflow.json', lastWorkflow);
  });
  byId('export-result').addEventListener('click', () => {
    if (!lastResult) return setStatus('Calculate a valid workflow before exporting its estimate.', 'error');
    download('gpuopt-estimate.json', lastResult);
  });

  byId('remember-draft').addEventListener('change', (event) => {
    if (event.currentTarget.checked) saveDraft();
    else root.localStorage.removeItem(storageKey);
  });
  byId('estimate-form').addEventListener('input', saveDraft);
  byId('estimate-form').addEventListener('change', saveDraft);
  byId('clear-draft').addEventListener('click', () => {
    root.localStorage.removeItem(storageKey);
    byId('remember-draft').checked = false;
    setStatus('Saved draft cleared from this device.', 'success');
  });

  try {
    const saved = root.localStorage.getItem(storageKey);
    if (saved) {
      const draft = JSON.parse(saved);
      model.validateWorkflow(draft);
      applyWorkflow(draft);
      byId('remember-draft').checked = true;
      setStatus('Your saved local draft was restored. It remains on this device.', 'info');
    }
  } catch (error) {
    root.localStorage.removeItem(storageKey);
    setStatus(`Saved draft could not be restored and was cleared: ${error.message}`, 'error');
  }
})(typeof globalThis !== 'undefined' ? globalThis : this);

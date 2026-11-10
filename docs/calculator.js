/* Public, deterministic browser mirror of optimizer/profiler.py and pricing.py. */
(function attachGpuOptimizer(root) {
  'use strict';

  const GPUS = {
    a100: { price_per_hour: 2.21, vram_gb: 80, fp16_tflops: 312, provider: 'runpod' },
    h100: { price_per_hour: 3.70, vram_gb: 80, fp16_tflops: 989, provider: 'runpod' },
    l40s: { price_per_hour: 1.86, vram_gb: 48, fp16_tflops: 362, provider: 'runpod' },
    rtx4090: { price_per_hour: 0.74, vram_gb: 24, fp16_tflops: 165, provider: 'runpod' },
    rtx3090: { price_per_hour: 0.44, vram_gb: 24, fp16_tflops: 71, provider: 'runpod' },
    a10g: { price_per_hour: 0.80, vram_gb: 24, fp16_tflops: 125, provider: 'runpod' },
    v100: { price_per_hour: 0.36, vram_gb: 16, fp16_tflops: 31.4, provider: 'runpod' },
  };
  const MODEL = {
    name: 'gpu-cost-optimizer heuristic v1',
    kind: 'simulated',
    timing_reference: 'A100-class GPU at 1024x1024, 30 steps, batch size 1',
    vram_reference: 'Heuristic estimate; model and runtime dependent',
  };
  const PRICING = {
    status: 'historical_reference',
    period: '2024-2025',
    currency: 'USD',
    source_note: 'Bundled reference rates; not live provider prices or a quote',
  };
  const DISCLAIMER = 'Timing and VRAM are simulated estimates, not a benchmark or measurement. Historical rates are references only; verify current provider prices, availability, runtime, and output quality before production use.';

  function round(value, digits) {
    const factor = 10 ** digits;
    return Math.round((value + Number.EPSILON) * factor) / factor;
  }

  function normalizeGpu(gpu) {
    return String(gpu).toLowerCase().replace(/[-\s]/g, '');
  }

  function validateWorkflow(workflow) {
    if (!workflow || typeof workflow !== 'object' || Array.isArray(workflow)) {
      throw new Error('Workflow must be a JSON object');
    }
    const resolution = workflow.resolution === undefined ? [512, 512] : workflow.resolution;
    if (!Array.isArray(resolution) || resolution.length !== 2 || resolution.some((n) => !Number.isInteger(n) || n < 1 || n > 16384)) {
      throw new Error('resolution must contain two integers between 1 and 16384');
    }
    const scheduler = workflow.scheduler === undefined ? {} : workflow.scheduler;
    if (!scheduler || typeof scheduler !== 'object' || Array.isArray(scheduler)) {
      throw new Error('scheduler must be a JSON object');
    }
    const steps = scheduler.steps === undefined ? 30 : scheduler.steps;
    if (!Number.isInteger(steps) || steps < 1 || steps > 1000) {
      throw new Error('scheduler.steps must be an integer between 1 and 1000');
    }
    const batch = workflow.batch_size === undefined ? 1 : workflow.batch_size;
    if (!Number.isInteger(batch) || batch < 1 || batch > 4096) {
      throw new Error('batch_size must be an integer between 1 and 4096');
    }
    return workflow;
  }

  function profileWorkflow(workflow, gpu) {
    validateWorkflow(workflow);
    const gpuId = normalizeGpu(gpu || 'a100');
    const gpuInfo = GPUS[gpuId];
    if (!gpuInfo) {
      throw new Error(`Unknown GPU: ${gpu}. Available: ${Object.keys(GPUS).sort().join(', ')}`);
    }
    const resolution = workflow.resolution || [512, 512];
    const scheduler = workflow.scheduler || {};
    const batch = workflow.batch_size === undefined ? 1 : workflow.batch_size;
    const megapixels = (resolution[0] * resolution[1]) / 1000000;
    const steps = scheduler.steps === undefined ? 30 : scheduler.steps;
    const base = [
      ['vae_encode', 0.12 * megapixels],
      ['text_encode', 0.08],
      ['denoise', 1.8 * megapixels * (steps / 30)],
      ['vae_decode', 0.15 * megapixels],
      ['safety_check', workflow.safety_checker ? 0.05 : 0],
    ];
    const timings = base.map(([step_name, seconds]) => ({
      step_name,
      elapsed_seconds: round((seconds * batch) * (312 / gpuInfo.fp16_tflops), 4),
      vram_peak_mb: 0,
    }));
    const total = timings.reduce((sum, step) => sum + step.elapsed_seconds, 0);
    const estimatedVram = 4 + megapixels * 2 + batch * 1.5;

    return {
      workflow_name: workflow.name || 'unnamed',
      gpu: gpu,
      steps: timings,
      total_seconds: round(total, 4),
      vram_estimate_gb: round(estimatedVram, 2),
    };
  }

  function compareGpus(workflow) {
    const results = Object.entries(GPUS).map(([gpu, info]) => {
      const profile = profileWorkflow(workflow, gpu);
      const cost = (profile.total_seconds / 3600) * info.price_per_hour;
      const meets = profile.vram_estimate_gb <= info.vram_gb;
      return {
        gpu,
        provider: info.provider,
        price_per_hour: info.price_per_hour,
        vram_gb: info.vram_gb,
        estimated_vram_gb: profile.vram_estimate_gb,
        estimated_time_seconds: profile.total_seconds,
        estimated_cost: round(cost, 6),
        meets_vram: meets,
        score: round(meets ? cost : cost * 10, 6),
      };
    });
    return results.sort((a, b) => a.score - b.score);
  }

  function buildResult(workflow, selectedGpu) {
    const profile = profileWorkflow(workflow, selectedGpu);
    return {
      workflow_name: profile.workflow_name,
      inputs: JSON.parse(JSON.stringify(workflow)),
      selected_gpu: selectedGpu,
      profile,
      comparisons: compareGpus(workflow),
      model: { ...MODEL },
      pricing: { ...PRICING },
      disclaimer: DISCLAIMER,
    };
  }

  const api = { GPUS, MODEL, PRICING, DISCLAIMER, validateWorkflow, profileWorkflow, compareGpus, buildResult };
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
  root.GpuCostOptimizer = api;
})(typeof globalThis !== 'undefined' ? globalThis : this);

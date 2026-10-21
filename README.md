# GPU Cost Optimizer

**Modelar antes de gastar.** Herramienta de estimación de costes y optimización de workflows de difusión. Compara tiempos simulados, resoluciones, pasos del scheduler y límites de VRAM sin consumir GPU.

> **Transparencia:** este proyecto calcula estimaciones heurísticas; **no ejecuta ni cronometra GPUs reales**, no garantiza ahorros ni calidad visual, y no consulta tarifas actuales automáticamente. Los porcentajes sugeridos son hipótesis para comprobar con benchmarks reales. Los precios integrados son referencias históricas de 2024–2025, **no presupuestos vigentes en 2026**.

## Instalación reproducible

Python 3.9 o superior. Desde el repositorio existente:

```bash
git clone https://github.com/belentani7/gpu-cost-optimizer.git
cd gpu-cost-optimizer
python -m pip install -e ".[dev]"
gpuopt --help
gpuopt list-gpus
```

No se asume que este paquete esté publicado en PyPI.

## Uso completo

Se entrega un archivo de ejemplo funcional en [`examples/workflow.json`](examples/workflow.json). No es necesario inventar un JSON antes de usar la aplicación.

```bash
# Perfil estimado de coste / latencia
gpuopt profile examples/workflow.json --gpu a100

# Propuesta de configuración ajustada al objetivo
gpuopt optimize examples/workflow.json --target-cost 0.50 --gpu a100

# Comparación heurística de GPU
gpuopt compare examples/workflow.json --gpus a100,h100,l40s

# Informe Markdown con plan y escenarios
gpuopt report examples/workflow.json --gpu a100 --output optimization-report.md

# Tarifas de REFERENCIA HISTÓRICA, no tarifas de compra actuales
gpuopt list-gpus
```

## Contrato JSON

```json
{
  "name": "character_generation",
  "pipeline": "stable-diffusion",
  "model": "sd-xl-base",
  "scheduler": {"type": "euler_a", "steps": 50},
  "resolution": [1024, 1024],
  "batch_size": 1,
  "guidance_scale": 7.5,
  "safety_checker": true,
  "vae_tiling": false
}
```

## Qué incluye

- `optimizer/profiler.py`: modelo de duración **simulada** por etapa y GPU.
- `optimizer/analyzer.py`: cuellos de botella y alternativas con ahorro **estimado**.
- `optimizer/strategies.py`: transformaciones del workflow, sin renderizar ni alterar originales.
- `optimizer/recommender.py`: recomendaciones heurísticas y comparación de GPUs.
- `optimizer/pricing.py`: tabla de precios históricos de referencia y funciones para estimar coste.
- `optimizer/report.py`: resumen y exportación Markdown.
- `optimizer/cli.py`: entrada `gpuopt` y cinco comandos reales.
- `docs/index.html`: página de producto estática existente.

Los ahorros pueden ser negativos, nulos o distintos a los estimados. Comprueba rendimiento, compatibilidad de modelo y calidad visual en el proveedor elegido antes de cambiar un workload productivo. Para costes reales, sustituye las tarifas históricas por precios actuales del proveedor y considera descuentos, almacenamiento, tráfico y tiempo de arranque.

## Calidad y publicación

```bash
python -m compileall -q optimizer tests
python -m pytest -q
gpuopt --help
gpuopt list-gpus
gpuopt profile examples/workflow.json --gpu a100
```

No aprobar una publicación si CI no llega a ejecutar los pasos o si falla cualquier prueba. El paquete no necesita secretos ni acceso a servicios externos para la demostración offline.

## Licencia

MIT · BELENTANI / 2026

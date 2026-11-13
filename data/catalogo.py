"""gpu-cost-optimizer — banco de datos canónico.

Generado por repo-forge desde el árbol real. Es la única fuente de verdad del
repositorio: si un dato no está aquí, no se afirma en ningún otro sitio.
"""
from __future__ import annotations

REPO = {
    "nombre": "gpu-cost-optimizer",
    "remoto": "https://github.com/belentani7/gpu-cost-optimizer",
    "tipo": "python-tool",
    "modelo": 'herramienta de coste de GPU',
    "publico": 'quien entrena o genera sin quemar presupuesto',
    "licencia": "MIT",
    "medido": {
        "archivos": 57,
        "lineas": 4479,
        "bytes": 174044,
        "html": 8,
        "tests": 8,
    },
    "modulos": ['Simulador', 'Comparativa', 'Límites de VRAM', 'Informe'],
    "paleta": {
        "bg": "#0f1419",
        "ink": "#e8eef6",
        "accent": "#28ade8",
    },
}


def resumen() -> str:
    """Una línea legible con el estado medido."""
    m = REPO["medido"]
    return f"{REPO['nombre']}: {m['archivos']} archivos, {m['lineas']} líneas, {m['html']} páginas HTML"


if __name__ == "__main__":
    print(resumen())

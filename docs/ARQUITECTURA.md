

<!-- repo-forge:docs-arquitectura:inicio -->
# Arquitectura

## Tipo

herramienta de línea de comandos en Python

## Piezas observadas

| Pieza | Evidencia |
|---|---|
| Lenguajes | HTML 41.0%, Python 36.8%, Markdown 10.6%, CSS 5.3%, JavaScript 5.0%, JSON 1.2% |
| Puntos de entrada | optimizer/cli.py |
| Páginas HTML | 8 |
| Tests | 8 archivos |
| Dependencias de paquete | 0 |

## Capas propuestas

```text
contenido/      datos y textos versionados
plataforma/     ficha, diseño y contrato del producto
brand/          tokens, marca y activos
scripts/        verificación y operación
tests/          pruebas ejecutables
```

La propuesta no mueve archivos existentes: describe dónde debe vivir lo nuevo para que
el repositorio siga siendo legible.

## Deuda declarada

- 6 lenguajes: coste de contexto alto.

<!-- repo-forge:arquitectura -->
<!-- repo-forge:docs-arquitectura:fin -->

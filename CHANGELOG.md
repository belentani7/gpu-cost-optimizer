# Changelog

## [1.0.0] - 2025-10-15

### Added
- Initial repository setup with CI/CD (GitHub Actions)
- Standardized issue templates (bug_report.yml)
- Pull request template
- Security workflow (CodeQL scanning)
- Dependabot configuration
- Code of Conduct (Contributor Covenant 2.1)
- Security Policy (SECURITY.md)
- Contribution Guidelines (CONTRIBUTING.md)

### Security
- Enabled Dependabot alerts and security updates
- Added CodeQL workflow for automated security scanning

<!-- repo-forge:changelog:inicio -->
# Changelog

Formato: [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/).
Versionado: [SemVer](https://semver.org/lang/es/).

## [No publicado]

### Añadido

- `gpuopt report --format json`: informe legible por máquina con la misma
  etiqueta de simulación y precios históricos que el resto de salidas.
- Gobernanza pública real: `CONTRIBUTING.md` y `CODE_OF_CONDUCT.md` (Contributor
  Covenant 2.1), ahora versionados y exigidos por `scripts/doctor.py`.
- Pruebas de regresión del nuevo formato de informe (`report --format json`).

### Corregido

- El gate `python scripts/doctor.py` pasa de 45/47 a 47/47.
- `.gitignore` desordenado por bloques duplicados; ya no ignora
  `CONTRIBUTING.md` ni `CODE_OF_CONDUCT.md`.
- README: fecha de medición, tabla de estado y marcadores `repo-forge`
  cuadruplicados; `unittest discover` (que solo ejecutaba 7 de 112 tests)
  sustituido por `pytest`; el ejemplo `gpuopt report --format json` anunciado
  en la web ahora existe de verdad.
- CI: el smoke test del CLI verifica también el informe JSON.
- Configuración de lint unificada en `pyproject.toml` (eliminado `ruff.toml`
  con ajustes contradictorios); hallazgos de ruff corregidos
  (`F841`, `B007`, `B905`, `UP015`).
- `Makefile test` ejecuta la suite completa (`pytest`) en lugar de
  `unittest discover`.
- HTML: `<meta charset>` duplicado en `docs/index.html`.
- Ficha de máximo potencial, marca, plataforma y fases de monetización (`plataforma/`).
- Banco de datos canónico (`data/`) y doctor de reglas (`scripts/doctor.py`).
- Gobernanza pública: contribución, conducta, seguridad y plantillas de GitHub.

<!-- repo-forge:changelog -->
<!-- repo-forge:changelog:fin -->

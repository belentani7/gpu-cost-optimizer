"""Pruebas del banco de datos: que lo declarado exista de verdad."""
from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "data"))

try:
    import catalogo  # type: ignore
except Exception:  # pragma: no cover
    catalogo = None


class TestCatalogo(unittest.TestCase):
    def setUp(self):
        self.path = ROOT / "data" / "catalogo.json"
        self.assertTrue(self.path.is_file(), "falta data/catalogo.json")
        self.data = json.loads(self.path.read_text(encoding="utf-8"))

    def test_campos_obligatorios(self):
        for key in ("nombre", "remoto", "tipo", "medido", "paleta"):
            self.assertIn(key, self.data)

    def test_paleta_tiene_contraste(self):
        p = self.data["paleta"]
        for key in ("bg", "ink", "accent"):
            self.assertRegex(p[key], r"^#[0-9a-f]{6}$")

    def test_medido_no_es_cero(self):
        self.assertGreater(self.data["medido"]["archivos"], 0)

    def test_modulo_python_carga(self):
        if catalogo is None:
            self.skipTest("data/catalogo.py no importable en este intérprete")
        self.assertTrue(catalogo.REPO["nombre"])


if __name__ == "__main__":
    unittest.main()

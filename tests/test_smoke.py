"""Prueba de humo: que el repositorio se pueda leer y el doctor responda."""
from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


class TestHumo(unittest.TestCase):
    def test_doctor_existe(self):
        self.assertTrue((ROOT / "scripts" / "doctor.py").is_file())

    def test_doctor_corre(self):
        r = subprocess.run([sys.executable, str(ROOT / "scripts" / "doctor.py")],
                           capture_output=True, text=True, cwd=str(ROOT))
        self.assertIn("comprobaciones", r.stdout, r.stderr[-800:])

    def test_biblia(self):
        self.assertTrue((ROOT / "BIBLIA.md").is_file())


if __name__ == "__main__":
    unittest.main()

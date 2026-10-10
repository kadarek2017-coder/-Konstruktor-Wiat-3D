"""Rama Kumiki dostępna z głównego Konstruktora Wiat 3D."""
from pathlib import Path
import runpy

runpy.run_path(str(Path(__file__).resolve().parents[1] / "testy_kumiki" / "podglad_obj.py"), run_name="__main__")

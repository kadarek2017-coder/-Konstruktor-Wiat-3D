"""Eksperymentalna kontrola API Kumiki. Nie zmienia głównej aplikacji.

Uruchom:
    python3 -m pip install kumiki
    python3 testy_kumiki/sprawdz_kumiki.py

Ten skrypt weryfikuje dostępność potrzebnych funkcji. Sam model CAD
będzie kolejnym etapem, po potwierdzeniu zgodności wersji API.
"""
import inspect
import sys

try:
    import kumiki
except ImportError:
    print("BRAK KUMIKI: zainstaluj osobno: python3 -m pip install kumiki")
    sys.exit(2)

required = [
    "create_axis_aligned_timber",
    "cut_basic_mortise_and_tenon_joint_on_face_aligned_timbers",
    "Frame",
    "export_frame_obj",
]
missing = []
for name in required:
    obj = getattr(kumiki, name, None)
    if obj is None:
        missing.append(name)
        print(f"BRAK: {name}")
    else:
        try:
            signature = str(inspect.signature(obj))
        except (ValueError, TypeError):
            signature = "(sygnatura niedostępna)"
        print(f"OK: {name}{signature}")

if missing:
    print("API różni się od dokumentacji. Nie generowano geometrii.")
    sys.exit(1)

print("API wykryte. Następny test: ustawienie dwóch elementów i eksport OBJ.")
print("Przekroje docelowe: słup 200 × 200 mm, belka 100 × 200 mm.")

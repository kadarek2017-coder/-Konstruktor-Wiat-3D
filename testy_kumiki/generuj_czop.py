"""Próba wygenerowania rzeczywistego czopa i gniazda w Kumiki 0.8.0.

Uruchom w aktywnym .venv-kumiki:
    python testy_kumiki/generuj_czop.py

Jeżeli API lub orientacja nie pasują, wypisuje etap i błąd.
Nie zmienia głównej aplikacji. Wymiary są w milimetrach.
"""
from pathlib import Path
import traceback
import kumiki as k

OUT = Path(__file__).resolve().parent / "wyniki"
OUT.mkdir(exist_ok=True)

def step(label, fn):
    print(f"→ {label}", flush=True)
    try:
        result = fn()
        print(f"  OK: {type(result).__name__}", flush=True)
        return result
    except Exception as exc:
        print(f"  BŁĄD: {type(exc).__name__}: {exc}", flush=True)
        traceback.print_exc()
        raise SystemExit(1) from exc

def enum_member(enum_cls, *names):
    for name in names:
        member = getattr(enum_cls, name, None)
        if member is not None:
            return member
    raise ValueError(f"Brak oczekiwanego wariantu {enum_cls}: {names}; dostępne: {list(enum_cls)}")

def vec(*values):
    return k.Matrix(list(values))

def make_post():
    # Słup pionowy, 200 x 200 mm, 2200 mm wysokości.
    return k.create_axis_aligned_timber(
        bottom_position=vec(0, 0, 0),
        length=2200,
        size=vec(200, 200),
        length_direction=enum_member(k.TimberFace, "TOP", "Top"),
    )

def make_beam():
    # Belka pozioma 100 x 200 mm, 1600 mm długości.
    # Pozycja belki dobrana poglądowo do próby styku ze słupem.
    return k.create_axis_aligned_timber(
        bottom_position=vec(-800, 0, 2200),
        length=1600,
        size=vec(100, 200),
        length_direction=enum_member(k.TimberFace, "RIGHT", "Right"),
    )

post = step("Tworzenie słupa 200×200 mm", make_post)
beam = step("Tworzenie belki 100×200 mm", make_beam)

print("Uwaga: wariant testowy wymaga sprawdzenia orientacji elementów.")
print("Połączenie wymaga końca jednego elementu dochodzącego do boku drugiego.")
joint = step(
    "Wycięcie czopa i gniazda",
    lambda: k.cut_basic_mortise_and_tenon_joint_on_face_aligned_timbers(
        tenon_timber=post,
        mortise_timber=beam,
        tenon_end=enum_member(k.TimberEnd, "TOP", "Top"),
    ),
)

print("Atrybuty Joint:", [x for x in dir(joint) if not x.startswith("_")])
print("Liczba operacji joint.cuttings:", len(getattr(joint, "cuttings", [])))
for i, cutting in enumerate(getattr(joint, "cuttings", []), 1):
    print(f"  cutting {i}: {type(cutting).__name__}")
    print("   atrybuty:", [x for x in dir(cutting) if not x.startswith("_")])

# Kumiki 0.8.0 zwraca Joint jako zestaw operacji cięcia.
# Żeby nie zgadywać sposobu ich zastosowania, próbujemy oficjalnych helperów API,
# a gdy ich brak — wypisujemy diagnostykę potrzebną do następnej poprawki.
candidates = [
    "cut_timbers_with_joints",
    "cut_timbers",
    "apply_joints",
    "create_frame",
    "frame_from_joints",
]
helper = next(((name, getattr(k, name)) for name in candidates if callable(getattr(k, name, None))), None)
if helper is None:
    print("DIAGNOSTYKA: brak oczywistego helpera stosującego Joint w głównym module.")
    print("Funkcje Kumiki zawierające 'cut', 'joint' lub 'frame':")
    print([x for x in dir(k) if any(word in x.lower() for word in ("cut", "joint", "frame"))])
    print("Joint został utworzony poprawnie; potrzebujemy tylko właściwej ścieżki Joint → CutTimber → Frame.")
    raise SystemExit(3)

name, fn = helper
print(f"Znaleziono helper API: {name}")
import inspect
print("Sygnatura:", inspect.signature(fn))
print("Na tym etapie nie wywołuję go automatycznie bez potwierdzenia parametrów.")
raise SystemExit(4)

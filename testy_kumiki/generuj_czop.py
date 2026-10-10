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
        width_direction=enum_member(k.TimberFace, "RIGHT", "Right"),
        ticket="SLUP_200x200",
    )

def make_beam():
    # Belka pozioma 100 x 200 mm, 1600 mm długości.
    # Początek belki jest dokładnie na osi/górnym końcu słupa.\n    # To spełnia warunek Kumiki: koniec elementu z czopem dochodzi do boku belki.
    return k.create_axis_aligned_timber(
        bottom_position=vec(-800, 0, 2200),
        length=1600,
        size=vec(100, 200),
        length_direction=enum_member(k.TimberFace, "RIGHT", "Right"),
        ticket="BELKA_100x200",
    )

post = step("Tworzenie słupa 200×200 mm", make_post)
beam = step("Tworzenie belki 100×200 mm", make_beam)

# Diagnostyka obiektów Timber PRZED wykonaniem Joint.
# Chcemy ustalić, czy długość 2200 mm ginie już podczas tworzenia Timber,
# czy dopiero podczas operacji czopa i gniazda.
def dump_object(label, obj):
    print(f"\n=== {label} ===")
    print("typ:", type(obj))
    try:
        attrs = vars(obj)
    except TypeError:
        attrs = {}
    if attrs:
        for key, value in attrs.items():
            if any(word in key.lower() for word in ("length", "size", "position", "axis", "direction", "start", "end")):
                print(f"  {key} = {value!r}")
    for name in ("length", "size", "bottom_position", "top_position", "axis", "length_direction", "width_direction"):
        try:
            value = getattr(obj, name)
        except Exception:
            continue
        print(f"  {name} = {value!r}")

dump_object("SŁUP TIMBER PRZED JOINT", post)
dump_object("BELKA TIMBER PRZED JOINT", beam)

# Następny test: sprawdzamy API Kumiki zamiast zgadywać konstruktor Frame.
# Wypisujemy sygnatury klas/funkcji potrzebnych do utworzenia CutTimber bez Joint.
import inspect
print("\n=== API KUMIKI DO TESTU BEZ JOINT ===")
for obj_name in ("CutTimber", "Frame"):
    obj = getattr(k, obj_name, None)
    print(f"{obj_name}: {obj!r}")
    if obj is not None:
        try:
            print("  signature:", inspect.signature(obj))
        except Exception as exc:
            print("  signature niedostępna:", exc)
        methods = [n for n in dir(obj) if not n.startswith("_") and any(w in n.lower() for w in ("timber", "cut", "frame", "joint"))]
        print("  metody:", methods)

# Kontrolny eksport słupa bez żadnego połączenia.
# Znamy już prawidłowy konstruktor: CutTimber(timber, cuts=None, joints=None)
# oraz Frame(cut_timbers=[...]).
raw_dir = OUT / "surowy_slup"
raw_dir.mkdir(exist_ok=True)
raw_cut = k.CutTimber(post)
raw_frame = k.Frame(cut_timbers=[raw_cut], name="SUROWY_SLUP")
raw_files = k.export_frame_obj(raw_frame, raw_dir, local=False, combined=False)
print("\n=== SUROWY SŁUP 2200 BEZ JOINT ===")
for p in raw_files:
    print(" ", p)
    verts = []
    with open(p, "r", encoding="utf-8", errors="ignore") as fh:
        for line in fh:
            if line.startswith("v "):
                parts = line.split()
                if len(parts) >= 4:
                    verts.append(tuple(map(float, parts[1:4])))
    if verts:
        mn = tuple(min(v[i] for v in verts) for i in range(3))
        mx = tuple(max(v[i] for v in verts) for i in range(3))
        size = tuple(mx[i] - mn[i] for i in range(3))
        print("  MIN    X,Y,Z =", mn)
        print("  MAX    X,Y,Z =", mx)
        print("  ROZMIAR X,Y,Z =", size)

print("TEST CENTROWANY: belka X=-800..+800 mm, słup kończy się w Z=2200 mm.")
print("Węzeł: X=0, Y=0, Z=2200.")
joint = step(
    "Wycięcie czopa i gniazda",
    lambda: k.cut_basic_mortise_and_tenon_joint_on_face_aligned_timbers(
        tenon_timber=post,
        mortise_timber=beam,
        tenon_end=enum_member(k.TimberEnd, "TOP", "Top"),
    ),
)

print("Liczba elementów w Joint:", len(joint.cuttings))
print("Nazwy elementów:", list(joint.cuttings.keys()))

# Dokumentacja Kumiki: Frame.from_joints łączy operacje Cutting w CutTimber.
frame = step("Złożenie Frame z Joint", lambda: k.Frame.from_joints([joint]))
print("Liczba CutTimber:", len(frame.cut_timbers))

print("\n=== CUTTIMBER PO JOINT ===")
for i, ct in enumerate(frame.cut_timbers):
    print(f"CutTimber #{i+1}: typ={type(ct)}")
    try:
        print("  vars =", vars(ct))
    except Exception as exc:
        print("  vars niedostępne:", exc)
    for name in ("timber", "length", "size", "ticket", "cuttings", "base_timber"):
        try:
            value = getattr(ct, name)
        except Exception:
            continue
        print(f"  {name} = {value!r}")
        if name in ("timber", "base_timber"):
            for sub in ("length", "size", "ticket"):
                try:
                    print(f"    {sub} = {getattr(value, sub)!r}")
                except Exception:
                    pass
if len(frame.cut_timbers) != 2:
    print("UWAGA: oczekiwano dwóch elementów — sprawdź geometrię.")

files = step(
    "Eksport OBJ w globalnym układzie współrzędnych",
    lambda: k.export_frame_obj(frame, OUT, local=False, combined=False),
)
print("Wygenerowane pliki:")
for p in files:
    print(" ", p)

# Diagnostyka rzeczywistych współrzędnych zapisanych w OBJ.
# Dzięki temu nie zgadujemy już orientacji osi Kumiki na podstawie podglądu.
def obj_bounds(path):
    vertices = []
    with open(path, "r", encoding="utf-8", errors="ignore") as fh:
        for line in fh:
            if line.startswith("v "):
                parts = line.split()
                if len(parts) >= 4:
                    vertices.append(tuple(float(v) for v in parts[1:4]))
    if not vertices:
        return None
    mins = tuple(min(v[i] for v in vertices) for i in range(3))
    maxs = tuple(max(v[i] for v in vertices) for i in range(3))
    center = tuple((mins[i] + maxs[i]) / 2 for i in range(3))
    size = tuple(maxs[i] - mins[i] for i in range(3))
    return mins, maxs, center, size

print("\n=== RZECZYWISTE GRANICE OBJ ===")
for p in files:
    bounds = obj_bounds(p)
    if bounds is None:
        print(f"{Path(p).name}: brak wierzchołków OBJ")
        continue
    mins, maxs, center, size = bounds
    fmt = lambda xyz: "(" + ", ".join(f"{v:.1f}" for v in xyz) + ")"
    print(f"{Path(p).name}:")
    print(f"  MIN    X,Y,Z = {fmt(mins)}")
    print(f"  MAX    X,Y,Z = {fmt(maxs)}")
    print(f"  ŚRODEK X,Y,Z = {fmt(center)}")
    print(f"  ROZMIAR X,Y,Z = {fmt(size)}")

print("\nSkopiuj sekcję 'RZECZYWISTE GRANICE OBJ' — na jej podstawie ustawimy elementy dokładnie.")

"""Czop i gniazdo: Kumiki w metrach, wynik OBJ w milimetrach.

Uruchom: python testy_kumiki/generuj_czop.py
Wymaga Kumiki 0.8.0. Nie zmienia głównego modelu wiaty.
"""
from pathlib import Path
from tempfile import TemporaryDirectory
import json
import kumiki as k
import numpy as np
import trimesh

OUT = Path(__file__).resolve().parent / "wyniki"
POST_NAME = "SLUP_200x200"
BEAM_NAME = "BELKA_100x200"


def metres_vector(*millimetres):
    return k.Matrix([k.mm(value) for value in millimetres])


def beam_dimensions(beam_flat=False):
    return (200, 100) if beam_flat else (100, 200)


def post_positions(full_frame=False):
    return {"SLUP_LEWY_200x200": -1200, "SLUP_PRAWY_200x200": 1200} if full_frame else {POST_NAME: 0}


def build_frame(beam_flat=False, full_frame=False):
    """Jedna belka, jeden lub dwa słupy; oś belki na Z=2200 mm."""
    width, height = beam_dimensions(beam_flat)
    length = 3000 if full_frame else 1600
    beam = k.create_axis_aligned_timber(
        bottom_position=metres_vector(-length / 2, 0, 2200), length=k.mm(length),
        size=metres_vector(100, 200), length_direction=k.TimberFace.RIGHT,
        width_direction=k.TimberFace.TOP if beam_flat else k.TimberFace.FRONT,
        ticket=BEAM_NAME,
    )
    joints = []
    for name, x in post_positions(full_frame).items():
        post = k.create_axis_aligned_timber(
            bottom_position=metres_vector(x, 0, 0), length=k.mm(2200),
            size=metres_vector(200, 200), length_direction=k.TimberFace.TOP,
            width_direction=k.TimberFace.RIGHT, ticket=name,
        )
        joints.append(k.cut_mortise_and_tenon_joint_on_face_aligned_timbers(
            arrangement=k.ButtJointTimberArrangement(
                butt_timber=post, receiving_timber=beam, butt_timber_end=k.TimberEnd.TOP,
            ),
            tenon_width_relative_to_joint=k.mm(150),
            tenon_height_relative_to_joint=k.mm(width / 3),
            tenon_length=k.mm(height), mortise_depth=k.mm(height),
        ))
    # Ta sama belka uczestniczy w obu Joint: Frame zbiera oba gniazda.
    return k.Frame.from_joints(joints)


def validate_meshes(meshes, beam_flat=False, full_frame=False):
    """Sprawdź bryły i przekroje wszystkich czopów i gniazd."""
    width, height = beam_dimensions(beam_flat)
    bottom, top = 2200 - height / 2, 2200 + height / 2
    length = 3000 if full_frame else 1600
    positions = post_positions(full_frame)
    expected = {name: ((x - 100, -100, 0), (x + 100, 100, top))
                for name, x in positions.items()}
    expected[BEAM_NAME] = ((-length / 2, -width / 2, bottom),
                           (length / 2, width / 2, top))
    if set(meshes) != set(expected):
        raise ValueError("Eksport ma nieprawidłową liczbę lub nazwy elementów.")
    for name, mesh in meshes.items():
        if mesh.is_empty or not mesh.is_volume:
            raise ValueError(f"{name}: bryła jest pusta lub nie jest zamknięta.")
        if not np.allclose(mesh.bounds, expected[name], atol=0.05, rtol=0):
            raise ValueError(f"{name}: nieprawidłowe granice OBJ: {mesh.bounds.tolist()}")
    expected_beam_volume = length * width * height - len(positions) * 150 * width / 3 * height
    if not np.isclose(meshes[BEAM_NAME].volume, expected_beam_volume, atol=200, rtol=0):
        raise ValueError("Belka nie ma prawidłowej liczby dopasowanych gniazd.")
    for name, x in positions.items():
        expected_post_volume = 200 * 200 * bottom + 150 * width / 3 * height
        if not np.isclose(meshes[name].volume, expected_post_volume, atol=200, rtol=0):
            raise ValueError(f"{name}: błędna objętość słupa lub czopa.")
        section = meshes[name].section(plane_origin=[0, 0, 2200], plane_normal=[0, 0, 1])
        if section is None or not np.allclose(
            section.bounds[:, :2], [[x - 75, -width / 6], [x + 75, width / 6]], atol=0.05, rtol=0
        ):
            raise ValueError(f"{name}: czop ma błędną orientację lub wystaje poza szerokość belki.")
    beam_section = meshes[BEAM_NAME].section(plane_origin=[0, 0, 2200], plane_normal=[0, 0, 1])
    if beam_section is None or len(beam_section.discrete) != len(positions) + 1:
        raise ValueError("Gniazda nie mają zamkniętych obrysów wewnątrz belki.")



def skeleton_parts(beam_flat=False):
    """Nazwy, etykiety i pozycje dwóch ram w rozstawie 3000 mm."""
    parts = {}
    for prefix, label, y in (("PRZOD", "przedni", -1500), ("TYL", "tylny", 1500)):
        for name, side in (("SLUP_LEWY_200x200", "lewy"), ("SLUP_PRAWY_200x200", "prawy")):
            parts[f"{prefix}_{name}"] = f"Słup {label} {side}"
    parts["LACZNIK_LEWY"] = "Belka łącząca lewa"
    parts["LACZNIK_PRAWY"] = "Belka łącząca prawa"
    parts[f"PRZOD_{BEAM_NAME}"] = "Belka ramy przedniej"
    parts[f"TYL_{BEAM_NAME}"] = "Belka ramy tylnej"
    return parts


def expand_skeleton(meshes, beam_flat=False):
    result = {}
    for prefix, y in (("PRZOD", -1500), ("TYL", 1500)):
        for name, mesh in meshes.items():
            part = mesh.copy()
            part.apply_translation([0, y, 0])
            result[f"{prefix}_{name}"] = part
    width, height = beam_dimensions(beam_flat)
    for name, x in (("LACZNIK_LEWY", -1200), ("LACZNIK_PRAWY", 1200)):
        part = trimesh.creation.box(extents=[width, 3000 + width, height])
        part.apply_translation([x, 0, 2200 + height])
        result[name] = part
    return result


def validate_skeleton(meshes, beam_flat=False):
    if set(meshes) != set(skeleton_parts(beam_flat)):
        raise ValueError("Szkielet musi zawierać cztery słupy i cztery belki.")
    for prefix, y in (("PRZOD", -1500), ("TYL", 1500)):
        frame = {}
        for name in [*post_positions(True), BEAM_NAME]:
            part = meshes[f"{prefix}_{name}"].copy()
            part.apply_translation([0, -y, 0])
            frame[name] = part
        validate_meshes(frame, beam_flat=beam_flat, full_frame=True)
    width, height = beam_dimensions(beam_flat)
    for name, x in (("LACZNIK_LEWY", -1200), ("LACZNIK_PRAWY", 1200)):
        part = meshes[name]
        expected = [[x-width/2, -(3000+width)/2, 2200+height/2],
                    [x+width/2, (3000+width)/2, 2200+1.5*height]]
        if not part.is_volume or not np.allclose(part.bounds, expected, atol=.05, rtol=0):
            raise ValueError(f"{name}: błędne podparcie lub wymiary belki łączącej.")
        if not np.isclose(part.volume, width*(3000+width)*height, atol=200, rtol=0):
            raise ValueError(f"{name}: błędna objętość belki łączącej.")

def generate(output_dir=OUT, beam_flat=False, full_frame=False, skeleton=False):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    full_frame = full_frame or skeleton
    width, height = beam_dimensions(beam_flat)
    frame = build_frame(beam_flat, full_frame)
    # Eksport i kontrola przed podmianą modeli; wyłącznie publiczne API.
    with TemporaryDirectory(prefix="eksport-", dir=output_dir) as temporary:
        files = k.export_frame_obj(frame, temporary, local=False, combined=False)
        meshes = {}
        for path in files:
            mesh = trimesh.load_mesh(path, process=True)
            mesh.apply_scale(1000)
            meshes[Path(path).stem] = mesh
        validate_meshes(meshes, beam_flat, full_frame)
        if skeleton:
            meshes = expand_skeleton(meshes, beam_flat)
            validate_skeleton(meshes, beam_flat)
        for name, mesh in meshes.items():
            staged = Path(temporary) / f"{name}.obj"
            mesh.export(staged, file_type="obj")
            staged.replace(output_dir / staged.name)
    report = {
        "units": "mm", "kumiki_version": "0.8.0",
        "beam_flat": beam_flat, "full_frame": full_frame, "skeleton": skeleton,
        "part_labels": skeleton_parts(beam_flat) if skeleton else {},
        "beam_axis_z_mm": 2200, "post_shoulder_z_mm": 2200 - height / 2,
        "tenon_top_z_mm": 2200 + height / 2,
        "parts": {name: {"bounds_mm": mesh.bounds.tolist(),
                          "size_mm": mesh.extents.tolist(),
                          "volume_mm3": float(mesh.volume)}
                  for name, mesh in meshes.items()},
    }
    (output_dir / "wymiary.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return report


def main():
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--flat", action="store_true", help="Połóż belkę płasko: szerokość 200, wysokość 100 mm")
    parser.add_argument("--frame", action="store_true", help="Pełna rama: dwa słupy w rozstawie osiowym 2400 mm i belka 3000 mm")
    parser.add_argument("--skeleton", action="store_true", help="Szkielet: dwie ramy i dwie belki łączące, rozstaw ram 3000 mm")
    args = parser.parse_args()
    report = generate(beam_flat=args.flat, full_frame=args.frame, skeleton=args.skeleton)
    width, height = beam_dimensions(args.flat)
    print("=== ZWERYFIKOWANE PLIKI OBJ (MILIMETRY) ===")
    for name, part in report["parts"].items():
        print(f"{name}.obj: rozmiar X,Y,Z = {part['size_mm']}")
    print(f"Belka: szerokość {width} mm, wysokość {height} mm, długość {3000 if args.frame or args.skeleton else 1600} mm.")
    print(f"Spód belki i bark słupa: Z={report['post_shoulder_z_mm']} mm; oś belki: Z=2200 mm.")
    print(f"Koniec czopa: Z={report['tenon_top_z_mm']} mm. Wynik zapisano w:", OUT)
    print("Podgląd: python -m streamlit run testy_kumiki/podglad_obj.py")


if __name__ == "__main__":
    main()

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


def build_frame(beam_flat=False):
    """Oś belki: Z=2200 mm. Przekrój można położyć płasko."""
    width, height = beam_dimensions(beam_flat)
    post = k.create_axis_aligned_timber(
        bottom_position=metres_vector(0, 0, 0), length=k.mm(2200),
        size=metres_vector(200, 200), length_direction=k.TimberFace.TOP,
        width_direction=k.TimberFace.RIGHT, ticket=POST_NAME,
    )
    beam = k.create_axis_aligned_timber(
        bottom_position=metres_vector(-800, 0, 2200), length=k.mm(1600),
        size=metres_vector(100, 200), length_direction=k.TimberFace.RIGHT,
        width_direction=k.TimberFace.TOP if beam_flat else k.TimberFace.FRONT,
        ticket=BEAM_NAME,
    )
    # Jawne osie przekroju czopa: X wzdłuż belki, Y w jej szerokości.
    # Automatyczny wrapper Kumiki odwracał te wymiary dla tej orientacji.
    joint = k.cut_mortise_and_tenon_joint_on_face_aligned_timbers(
        arrangement=k.ButtJointTimberArrangement(
            butt_timber=post, receiving_timber=beam, butt_timber_end=k.TimberEnd.TOP,
        ),
        tenon_width_relative_to_joint=k.mm(150),
        tenon_height_relative_to_joint=k.mm(width / 3),
        tenon_length=k.mm(height), mortise_depth=k.mm(height),
    )
    return k.Frame.from_joints([joint])


def validate_meshes(meshes, beam_flat=False):
    """Sprawdź rzeczywiste wymiary, położenie i zamknięcie brył OBJ."""
    width, height = beam_dimensions(beam_flat)
    bottom, top = 2200 - height / 2, 2200 + height / 2
    expected = {
        POST_NAME: ((-100, -100, 0), (100, 100, top)),
        BEAM_NAME: ((-800, -width / 2, bottom), (800, width / 2, top)),
    }
    if set(meshes) != set(expected):
        raise ValueError("Eksport musi zawierać dokładnie słup i belkę.")
    for name, mesh in meshes.items():
        if mesh.is_empty or not mesh.is_volume:
            raise ValueError(f"{name}: bryła jest pusta lub nie jest zamknięta.")
        if not np.allclose(mesh.bounds, expected[name], atol=0.05, rtol=0):
            raise ValueError(f"{name}: nieprawidłowe granice OBJ: {mesh.bounds.tolist()}")
    if not 0 < meshes[BEAM_NAME].volume < 1600 * 100 * 200:
        raise ValueError("Belka nie ma wyciętego gniazda.")
    if not 200 * 200 * bottom < meshes[POST_NAME].volume < 200 * 200 * top:
        raise ValueError("Słup nie ma prawidłowo wyciętych barków czopa.")
    section = meshes[POST_NAME].section(plane_origin=[0, 0, 2200], plane_normal=[0, 0, 1])
    if section is None or not np.allclose(
        section.bounds[:, :2], [[-75, -width / 6], [75, width / 6]], atol=0.05, rtol=0
    ):
        raise ValueError("Czop ma błędną orientację lub wystaje poza szerokość belki.")


def generate(output_dir=OUT, beam_flat=False):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    width, height = beam_dimensions(beam_flat)
    frame = build_frame(beam_flat)
    # Eksport i kontrola przed podmianą modeli; wyłącznie publiczne API.
    with TemporaryDirectory(prefix="eksport-", dir=output_dir) as temporary:
        files = k.export_frame_obj(frame, temporary, local=False, combined=False)
        meshes = {}
        for path in files:
            mesh = trimesh.load_mesh(path, process=True)
            mesh.apply_scale(1000)
            meshes[Path(path).stem] = mesh
        validate_meshes(meshes, beam_flat)
        for name, mesh in meshes.items():
            staged = Path(temporary) / f"{name}.obj"
            mesh.export(staged, file_type="obj")
            staged.replace(output_dir / staged.name)
    report = {
        "units": "mm", "kumiki_version": "0.8.0",
        "beam_flat": beam_flat,
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
    args = parser.parse_args()
    report = generate(beam_flat=args.flat)
    width, height = beam_dimensions(args.flat)
    print("=== ZWERYFIKOWANE PLIKI OBJ (MILIMETRY) ===")
    for name, part in report["parts"].items():
        print(f"{name}.obj: rozmiar X,Y,Z = {part['size_mm']}")
    print(f"Belka: szerokość {width} mm, wysokość {height} mm, długość 1600 mm.")
    print(f"Spód belki i bark słupa: Z={report['post_shoulder_z_mm']} mm; oś belki: Z=2200 mm.")
    print(f"Koniec czopa: Z={report['tenon_top_z_mm']} mm. Wynik zapisano w:", OUT)
    print("Podgląd: python -m streamlit run testy_kumiki/podglad_obj.py")


if __name__ == "__main__":
    main()

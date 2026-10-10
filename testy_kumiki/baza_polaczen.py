"""Katalog połączeń i dwa zweryfikowane przykłady geometrii Kumiki."""
from pathlib import Path
from tempfile import TemporaryDirectory
import json
import kumiki as k
import numpy as np
import trimesh
if __package__:
    from .generuj_czop import build_frame, metres_vector, validate_meshes
else:
    from generuj_czop import build_frame, metres_vector, validate_meshes

CATALOG = Path(__file__).with_name('polaczenia.json')


def read_catalog():
    return json.loads(CATALOG.read_text(encoding='utf-8'))


def example_meshes(joint_id):
    if joint_id == 'czop_gniazdo':
        frame = build_frame()
    elif joint_id == 'pol_drewna':
        a = k.create_axis_aligned_timber(
            bottom_position=metres_vector(-600, 0, 0), length=k.mm(1200),
            size=metres_vector(100, 200), length_direction=k.TimberFace.RIGHT,
            width_direction=k.TimberFace.FRONT, ticket='BELKA_A')
        b = k.create_axis_aligned_timber(
            bottom_position=metres_vector(0, -600, 0), length=k.mm(1200),
            size=metres_vector(100, 200), length_direction=k.TimberFace.FRONT,
            width_direction=k.TimberFace.RIGHT, ticket='BELKA_B')
        joint = k.cut_basic_plain_cross_lap_joint_on_face_aligned_timbers(
            k.CrossJointTimberArrangement(a, b))
        frame = k.Frame.from_joints([joint])
    else:
        raise ValueError('To połączenie jest pozycją katalogową, bez generatora wycięć.')
    with TemporaryDirectory() as temporary:
        meshes = {}
        for path in k.export_frame_obj(frame, temporary, local=False, combined=False):
            mesh = trimesh.load_mesh(path)
            mesh.apply_scale(1000)
            meshes[Path(path).stem] = mesh
    if joint_id == 'czop_gniazdo':
        validate_meshes(meshes)
    else:
        for name, mesh in meshes.items():
            if not mesh.is_volume or not np.isclose(mesh.volume, 23_000_000, atol=200, rtol=0):
                raise ValueError(f'{name}: błędne wycięcie pół drewna.')
    overlap = trimesh.boolean.intersection(list(meshes.values()), engine='manifold')
    if not overlap.is_empty and abs(overlap.volume) > .1:
        raise ValueError('Przykład połączenia zawiera kolizję brył.')
    return meshes


def example_objects():
    result = {}
    for joint_id in ('czop_gniazdo', 'pol_drewna'):
        meshes = example_meshes(joint_id)
        order = ['SLUP_200x200', 'BELKA_100x200'] if joint_id == 'czop_gniazdo' else ['BELKA_A', 'BELKA_B']
        result[joint_id] = [meshes[name].export(file_type='obj') for name in order]
    return result

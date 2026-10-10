"""Regresja jednostek OBJ i dopasowania rzeczywistego czopa do gniazda."""
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

import numpy as np
import trimesh

from testy_kumiki.generuj_czop import BEAM_NAME, POST_NAME, generate, validate_meshes, validate_skeleton


class GeometryTests(unittest.TestCase):
    beam_flat = False
    width = 100
    bottom, top = 2100, 2300
    post_volume = 85_000_000
    @classmethod
    def setUpClass(cls):
        cls.temporary = TemporaryDirectory()
        cls.addClassCleanup(cls.temporary.cleanup)
        cls.output = Path(cls.temporary.name)
        generate(cls.output, beam_flat=cls.beam_flat)
        cls.post = trimesh.load_mesh(cls.output / f"{POST_NAME}.obj")
        cls.beam = trimesh.load_mesh(cls.output / f"{BEAM_NAME}.obj")

    def test_saved_obj_dimensions_and_cutouts(self):
        np.testing.assert_allclose(self.post.bounds,
                                   [[-100, -100, 0], [100, 100, self.top]], atol=0.05)
        np.testing.assert_allclose(self.beam.bounds,
                                   [[-800, -self.width / 2, self.bottom],
                                    [800, self.width / 2, self.top]], atol=0.05)
        self.assertTrue(self.post.is_volume)
        self.assertTrue(self.beam.is_volume)
        self.assertAlmostEqual(self.post.volume, self.post_volume, delta=100)
        self.assertAlmostEqual(self.beam.volume, 31_000_000, delta=100)

    def test_tenon_is_inside_beam_width_and_has_closed_mortise(self):
        section = self.post.section(plane_origin=[0, 0, 2200], plane_normal=[0, 0, 1])
        np.testing.assert_allclose(section.bounds[:, :2],
                                   [[-75, -self.width / 6], [75, self.width / 6]], atol=0.05)
        beam_section = self.beam.section(plane_origin=[0, 0, 2200], plane_normal=[0, 0, 1])
        # Zewnętrzny obrys i osobny zamknięty obrys gniazda.
        self.assertEqual(len(beam_section.discrete), 2)
        widths = sorted(np.ptp(loop[:, 1]) for loop in beam_section.discrete)
        np.testing.assert_allclose(widths, [self.width / 3, self.width], atol=0.05)

    def test_tenon_and_mortise_have_no_collision(self):
        overlap = trimesh.boolean.intersection([self.post, self.beam], engine="manifold")
        self.assertTrue(overlap.is_empty or abs(overlap.volume) < 0.1)


class FlatGeometryTests(GeometryTests):
    beam_flat = True
    width = 200
    bottom, top = 2150, 2250
    post_volume = 87_000_000


class FullFrameTests(unittest.TestCase):
    def test_two_post_frame_in_both_beam_orientations(self):
        for flat in (False, True):
            with self.subTest(flat=flat), TemporaryDirectory() as temporary:
                output = Path(temporary)
                generate(output, beam_flat=flat, full_frame=True)
                meshes = {name: trimesh.load_mesh(output / f"{name}.obj")
                          for name in ("SLUP_LEWY_200x200", "SLUP_PRAWY_200x200", BEAM_NAME)}
                validate_meshes(meshes, beam_flat=flat, full_frame=True)
                self.assertAlmostEqual(meshes[BEAM_NAME].volume, 58_000_000, delta=200)
                self.assertEqual(len(meshes[BEAM_NAME].section(
                    plane_origin=[0, 0, 2200], plane_normal=[0, 0, 1]
                ).discrete), 3)
                for name in ("SLUP_LEWY_200x200", "SLUP_PRAWY_200x200"):
                    overlap = trimesh.boolean.intersection([meshes[name], meshes[BEAM_NAME]], engine="manifold")
                    self.assertTrue(overlap.is_empty or abs(overlap.volume) < 0.1)


class SkeletonTests(unittest.TestCase):
    def test_exported_skeleton_support_and_no_collisions(self):
        from itertools import combinations
        for flat in (False, True):
            with self.subTest(flat=flat), TemporaryDirectory() as temporary:
                output = Path(temporary)
                report = generate(output, beam_flat=flat, skeleton=True)
                meshes = {name: trimesh.load_mesh(output / f"{name}.obj")
                          for name in report["parts"]}
                self.assertEqual(len(meshes), 8)
                validate_skeleton(meshes, beam_flat=flat)
                self.assertTrue(report["skeleton"])
                for (name_a, a), (name_b, b) in combinations(meshes.items(), 2):
                    # Broad phase: only pairs whose bounding boxes meet.
                    if np.any(a.bounds[1] < b.bounds[0]-.001) or np.any(b.bounds[1] < a.bounds[0]-.001):
                        continue
                    overlap = trimesh.boolean.intersection([a, b], engine="manifold")
                    self.assertTrue(overlap.is_empty or abs(overlap.volume) < 5,
                                    f"{name_a} collides with {name_b}: {overlap.volume}")
                connector = meshes["LACZNIK_LEWY"]
                front = meshes["PRZOD_" + BEAM_NAME]
                self.assertAlmostEqual(connector.bounds[0, 2], front.bounds[1, 2], delta=.001)


if __name__ == "__main__":
    unittest.main()

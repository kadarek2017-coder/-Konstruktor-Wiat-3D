"""Regresja jednostek OBJ i dopasowania rzeczywistego czopa do gniazda."""
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

import numpy as np
import trimesh

from testy_kumiki.generuj_czop import BEAM_NAME, POST_NAME, generate


class GeometryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary = TemporaryDirectory()
        cls.addClassCleanup(cls.temporary.cleanup)
        cls.output = Path(cls.temporary.name)
        generate(cls.output)
        cls.post = trimesh.load_mesh(cls.output / f"{POST_NAME}.obj")
        cls.beam = trimesh.load_mesh(cls.output / f"{BEAM_NAME}.obj")

    def test_saved_obj_dimensions_and_cutouts(self):
        np.testing.assert_allclose(self.post.bounds,
                                   [[-100, -100, 0], [100, 100, 2300]], atol=0.05)
        np.testing.assert_allclose(self.beam.bounds,
                                   [[-800, -50, 2100], [800, 50, 2300]], atol=0.05)
        self.assertTrue(self.post.is_volume)
        self.assertTrue(self.beam.is_volume)
        self.assertAlmostEqual(self.post.volume, 85_000_000, delta=100)
        self.assertAlmostEqual(self.beam.volume, 31_000_000, delta=100)

    def test_tenon_is_inside_beam_width_and_has_closed_mortise(self):
        section = self.post.section(plane_origin=[0, 0, 2200], plane_normal=[0, 0, 1])
        np.testing.assert_allclose(section.bounds[:, :2],
                                   [[-75, -100 / 6], [75, 100 / 6]], atol=0.05)
        beam_section = self.beam.section(plane_origin=[0, 0, 2200], plane_normal=[0, 0, 1])
        # Zewnętrzny obrys i osobny zamknięty obrys gniazda.
        self.assertEqual(len(beam_section.discrete), 2)
        widths = sorted(np.ptp(loop[:, 1]) for loop in beam_section.discrete)
        np.testing.assert_allclose(widths, [100 / 3, 100], atol=0.05)

    def test_tenon_and_mortise_have_no_collision(self):
        overlap = trimesh.boolean.intersection([self.post, self.beam], engine="manifold")
        self.assertTrue(overlap.is_empty or abs(overlap.volume) < 0.1)


if __name__ == "__main__":
    unittest.main()

"""Kontrola katalogu i rzeczywistych wycięć przykładów połączeń."""
import io
import unittest
import numpy as np
import trimesh
from testy_kumiki.baza_polaczen import read_catalog, example_meshes


class JointLibraryTests(unittest.TestCase):
    def test_catalog_distinguishes_supported_geometry(self):
        entries = read_catalog()
        self.assertEqual(len(entries), 12)
        self.assertEqual(len({entry['id'] for entry in entries}), len(entries))
        self.assertEqual({entry['id'] for entry in entries if entry['status'] == 'gotowy_przyklad'},
                         {'czop_gniazdo', 'pol_drewna'})
        with self.assertRaises(ValueError):
            example_meshes('kolki')

    def test_cross_lap_has_complementary_upper_and_lower_notches(self):
        meshes = example_meshes('pol_drewna')
        a, b = meshes['BELKA_A'], meshes['BELKA_B']
        np.testing.assert_allclose(a.bounds, [[-600,-50,-100],[600,50,100]], atol=.01)
        np.testing.assert_allclose(b.bounds, [[-50,-600,-100],[50,600,100]], atol=.01)
        sections = []
        for mesh in (a, b):
            sections.append([len(mesh.section(plane_origin=[0,0,z],plane_normal=[0,0,1]).discrete)
                             for z in (-50,50)])
            self.assertAlmostEqual(mesh.volume, 23_000_000, delta=200)
            self.assertTrue(mesh.is_volume)
        self.assertEqual(sections, [[1,2],[2,1]])
        overlap = trimesh.boolean.intersection([a,b], engine='manifold')
        self.assertTrue(overlap.is_empty or abs(overlap.volume)<.1)

    def test_mortise_tenon_export_keeps_mm_and_closed_hole(self):
        meshes = example_meshes('czop_gniazdo')
        beam = meshes['BELKA_100x200']
        restored = trimesh.load_mesh(io.StringIO(beam.export(file_type='obj')),file_type='obj')
        np.testing.assert_allclose(restored.extents,[1600,100,200],atol=.01)
        self.assertEqual(len(restored.section(plane_origin=[0,0,2200],plane_normal=[0,0,1]).discrete),2)
        self.assertTrue(restored.is_volume)


if __name__ == '__main__':
    unittest.main()

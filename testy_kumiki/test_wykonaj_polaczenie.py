"""Połączenia wykonywane na częściach użytkownika, zamiast nowych przykładów."""
import copy
import unittest
import numpy as np
import trimesh
from testy_kumiki.wykonaj_polaczenie import cut_pair, execute_request, load_obj
from testy_kumiki.baza_polaczen import example_meshes


def box(size,center):
    m=trimesh.creation.box(extents=size);m.apply_translation(center);return m


class ApplyJointTests(unittest.TestCase):
    def test_user_post_and_beam_in_both_directions(self):
        for axis in (0,1):
            post=box([200,200,2200],[800,400,1100])
            size=[1600,100,200] if axis==0 else [100,1600,200]
            beam=box(size,[800,400,2300])
            a,b=cut_pair(post,beam,'czop_gniazdo')
            self.assertAlmostEqual(a.bounds[1,2],2400,delta=.01)
            self.assertAlmostEqual(a.volume,89_000_000,delta=200)
            self.assertAlmostEqual(b.volume,31_000_000,delta=200)
            section=a.section(plane_origin=[0,0,2300],plane_normal=[0,0,1])
            expected=[150,100/3] if axis==0 else [100/3,150]
            np.testing.assert_allclose(section.bounds[1,:2]-section.bounds[0,:2],expected,atol=.01)

    def test_actual_crossing_beams_keep_previous_material_removal(self):
        examples=example_meshes('pol_drewna')
        a,b=cut_pair(examples['BELKA_A'],examples['BELKA_B'],'pol_drewna')
        self.assertAlmostEqual(a.volume,23_000_000,delta=200)
        self.assertAlmostEqual(b.volume,23_000_000,delta=200)

    def test_obj_with_sharp_normals_is_welded_before_validation(self):
        mesh=box([200,200,2200],[0,0,1100])
        mesh.unmerge_vertices()
        mesh.vertex_normals=np.repeat(mesh.face_normals,3,axis=0)
        restored=load_obj(mesh.export(file_type='obj',include_normals=True))
        self.assertTrue(restored.is_volume)
        self.assertAlmostEqual(restored.volume,88_000_000,delta=.1)

    def test_receiving_beam_keeps_an_existing_mortise(self):
        original=box([1600,100,200],[0,0,0])
        old_hole=box([150,100/3,202],[400,0,0])
        beam=trimesh.boolean.difference([original,old_hole],engine='manifold')
        post=box([200,200,2100],[0,0,-1150])
        _,cut_beam=cut_pair(post,beam,'czop_gniazdo')
        self.assertAlmostEqual(cut_beam.volume,30_000_000,delta=200)
        section=cut_beam.section(plane_origin=[0,0,0],plane_normal=[0,0,1])
        self.assertEqual(len(section.discrete),3)

    def test_invalid_geometry_is_rejected_without_modification(self):
        post=box([200,200,2200],[0,0,1100]);beam=box([1600,100,200],[0,0,2700])
        vertices=post.vertices.copy()
        with self.assertRaisesRegex(ValueError,'Góra słupa'):
            cut_pair(post,beam,'czop_gniazdo')
        np.testing.assert_array_equal(post.vertices,vertices)
        with self.assertRaisesRegex(ValueError,'prostopadłych'):
            cut_pair(beam,beam.copy(),'pol_drewna')

    def test_request_changes_selected_parts_and_serializes_cut_meshes(self):
        post=box([200,200,2200],[0,0,1100]);beam=box([1600,100,200],[0,0,2300])
        state={'parts':[{'position':[0,0,1100],'home':[0,0,1100],'definition':{'type':0}},
                        {'position':[0,0,2300],'home':[0,0,2300],'definition':{'type':1}},
                        {'position':[5000,0,0],'home':[5000,0,0],'definition':{'type':0}}]}
        original=copy.deepcopy(state)
        result=execute_request({'joint':'czop_gniazdo','indices':[0,1],'sources':[m.export(file_type='obj') for m in (post,beam)],'state':state,'base_count':0})
        self.assertEqual(state,original)
        self.assertEqual(result['state']['parts'][2],original['parts'][2])
        self.assertIn('mesh',result['state']['parts'][0]['definition'])
        self.assertIn('mesh',result['state']['parts'][1]['definition'])
        self.assertEqual(result['indices'],[0,1])


if __name__=='__main__':
    unittest.main()

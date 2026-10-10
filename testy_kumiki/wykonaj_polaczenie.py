"""Wycięcie czopa lub pół drewna w dwóch rzeczywistych siatkach edytora."""
import copy
import io
from pathlib import Path
from tempfile import TemporaryDirectory
import kumiki as k
import numpy as np
import trimesh
if __package__:
    from .generuj_czop import metres_vector
else:
    from generuj_czop import metres_vector


def load_obj(text):
    if not isinstance(text,str) or len(text)>2_000_000:
        raise ValueError('Nieprawidłowa geometria elementu.')
    mesh=trimesh.load_mesh(io.StringIO(text),file_type='obj')
    if isinstance(mesh,trimesh.Trimesh):
        # OBJExporter zapisuje różne normalne na ostrych krawędziach.
        # Spawaj wspólne pozycje, aby sprawdzać topologię zamiast normalnych.
        mesh.merge_vertices(merge_norm=True,merge_tex=True)
    if not isinstance(mesh,trimesh.Trimesh) or not mesh.is_volume or not np.isfinite(mesh.vertices).all():
        raise ValueError('Element musi być zamkniętą bryłą.')
    if len(mesh.faces)>20000 or np.max(np.abs(mesh.vertices))>1_000_000:
        raise ValueError('Geometria przekracza zakres edytora.')
    # Pierwszy etap obejmuje drewno ustawione zgodnie z osiami modelu.
    if not np.all(np.max(np.abs(mesh.face_normals),axis=1)>1-1e-5):
        raise ValueError('Na razie obsługiwane są elementy w osiach X/Y/Z, bez ukośnego ustawienia.')
    return mesh


def beam_axis(mesh):
    axis=int(np.argmax(mesh.extents[:2]))
    if mesh.extents[axis]<max(mesh.extents[1-axis],mesh.extents[2])*1.5:
        raise ValueError('Wskaż poziomą belkę o jednoznacznym kierunku długości.')
    return axis


def make_beam(mesh,name):
    axis=beam_axis(mesh)
    center=mesh.bounds.mean(axis=0)
    start=center.copy();start[axis]=mesh.bounds[0,axis]
    return k.create_axis_aligned_timber(
        bottom_position=metres_vector(*start),length=k.mm(mesh.extents[axis]),
        size=metres_vector(mesh.extents[1-axis],mesh.extents[2]),
        length_direction=k.TimberFace.RIGHT if axis==0 else k.TimberFace.FRONT,
        width_direction=k.TimberFace.FRONT if axis==0 else k.TimberFace.RIGHT,ticket=name)


def cut_pair(mesh_a,mesh_b,joint_id,preserve_a=False):
    if joint_id=='czop_gniazdo':
        axis=beam_axis(mesh_b);transverse=1-axis
        a,b=mesh_a.bounds,mesh_b.bounds
        center=a.mean(axis=0)
        if mesh_a.extents[2]<max(mesh_a.extents[:2])*1.5:
            raise ValueError('Element A musi być pionowym słupem, element B poziomą belką.')
        if a[1,2]<b[0,2]-.1 or a[1,2]>b[1,2]+.1:
            raise ValueError('Góra słupa musi stykać się ze spodem belki albo znajdować się w jej wysokości. Ustaw elementy przed wycięciem.')
        beam_center=b.mean(axis=0)
        if abs(center[transverse]-beam_center[transverse])>.1:
            raise ValueError('Wyrównaj oś słupa ze środkiem szerokości belki.')
        tenon_width=mesh_a.extents[axis]*.75
        tenon_thickness=mesh_b.extents[transverse]/3
        if tenon_thickness>=mesh_a.extents[transverse] or center[axis]-tenon_width/2<=b[0,axis] or center[axis]+tenon_width/2>=b[1,axis]:
            raise ValueError('Czop nie mieści się wewnątrz przekroju lub długości belki.')
        post=k.create_axis_aligned_timber(
            bottom_position=metres_vector(center[0],center[1],a[0,2]),
            length=k.mm(beam_center[2]-a[0,2]),size=metres_vector(*mesh_a.extents[:2]),
            length_direction=k.TimberFace.TOP,width_direction=k.TimberFace.RIGHT,ticket='A')
        joint=k.cut_mortise_and_tenon_joint_on_face_aligned_timbers(
            k.ButtJointTimberArrangement(butt_timber=post,receiving_timber=make_beam(mesh_b,'B'),butt_timber_end=k.TimberEnd.TOP),
            tenon_width_relative_to_joint=k.mm(tenon_width),tenon_height_relative_to_joint=k.mm(tenon_thickness),
            tenon_length=k.mm(mesh_b.extents[2]),mortise_depth=k.mm(mesh_b.extents[2]))
    elif joint_id=='pol_drewna':
        if beam_axis(mesh_a)==beam_axis(mesh_b):
            raise ValueError('Pół drewna wymaga dwóch prostopadłych poziomych belek.')
        if not np.allclose(mesh_a.bounds[:,2],mesh_b.bounds[:,2],atol=.1,rtol=0):
            raise ValueError('Dla tego wariantu pół drewna belki muszą mieć taką samą wysokość i poziom.')
        overlap=np.minimum(mesh_a.bounds[1],mesh_b.bounds[1])-np.maximum(mesh_a.bounds[0],mesh_b.bounds[0])
        if np.any(overlap<.1):
            raise ValueError('Belki nie przecinają się. Najpierw ustaw je w miejscu połączenia.')
        joint=k.cut_basic_plain_cross_lap_joint_on_face_aligned_timbers(
            k.CrossJointTimberArrangement(make_beam(mesh_a,'A'),make_beam(mesh_b,'B')))
    else:
        raise ValueError('Generator tego połączenia nie jest jeszcze dostępny.')
    with TemporaryDirectory() as directory:
        generated={}
        for path in k.export_frame_obj(k.Frame.from_joints([joint]),directory,local=False,combined=False):
            mesh=trimesh.load_mesh(path);mesh.apply_scale(1000);generated[Path(path).stem]=mesh
    results=[generated['A'],generated['B']]
    # Zachowaj wcześniejsze wycięcia w belkach; nie odtwarzaj usuniętego drewna.
    for i,original in enumerate((mesh_a,mesh_b)):
        if joint_id=='pol_drewna' or i==1 or preserve_a:
            results[i]=trimesh.boolean.intersection([results[i],original],engine='manifold')
        if results[i].is_empty or not results[i].is_volume:
            raise ValueError('Wycięcie nie dało poprawnej, zamkniętej bryły.')
    collision=trimesh.boolean.intersection(results,engine='manifold')
    if not collision.is_empty and abs(collision.volume)>1:
        raise ValueError('Po wycięciu elementy nadal kolidują.')
    return results


def execute_request(request):
    if not isinstance(request,dict) or request.get('joint') not in ('czop_gniazdo','pol_drewna'):
        raise ValueError('Nieznany typ połączenia.')
    state=request.get('state');indices=request.get('indices');sources=request.get('sources')
    if not isinstance(state,dict) or not isinstance(state.get('parts'),list) or len(state['parts'])>500:
        raise ValueError('Brak prawidłowego projektu.')
    if not isinstance(indices,list) or len(indices)!=2 or indices[0]==indices[1] or any(type(i) is not int or not 0<=i<len(state['parts']) for i in indices):
        raise ValueError('Wybierz dwa różne elementy.')
    if not isinstance(sources,list) or len(sources)!=2:
        raise ValueError('Brak geometrii elementów.')
    meshes=[load_obj(text) for text in sources]
    definition=state['parts'][indices[0]].get('definition')
    preserve_a=definition is None or isinstance(definition,dict) and ('mesh' in definition or 'joint' in definition)
    result=cut_pair(*meshes,request['joint'],preserve_a=preserve_a)
    restored=copy.deepcopy(state)
    for index,mesh in zip(indices,result):
        part=restored['parts'][index]
        center=mesh.bounds.mean(axis=0)
        local=mesh.copy();local.apply_translation(-center)
        part['definition']={'mesh':local.export(file_type='obj'),'connection':request['joint']}
        part['position']=center.tolist()
        # Bazowe pozycje przywracania nie zmieniają się; nowa część zachowuje pozycję po wycięciu.
        if index>=request.get('base_count',0):part['home']=center.tolist()
    return {'state':restored,'message':'Wykonano połączenie w wybranych elementach. Zapisz projekt, aby zachować wycięcia.','indices':indices,'camera':request.get('camera')}

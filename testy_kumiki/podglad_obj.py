"""Podgląd dwóch plików OBJ wygenerowanych przez Kumiki.

Najpierw wygeneruj geometrię:
    python testy_kumiki/generuj_czop.py

Potem uruchom:
    streamlit run testy_kumiki/podglad_obj.py
"""
from pathlib import Path
import io
import json
import subprocess
import sys
import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="Podgląd Kumiki 3D", page_icon="🪚", layout="wide")
st.title("🪚 Podgląd Kumiki 3D")
st.caption("Wersja podglądu 6 — pełna rama, wybieranie i przeciąganie elementów")

app_dir = Path(__file__).resolve().parent
base = app_dir / "wyniki"
try:
    saved_report = json.loads((base / "wymiary.json").read_text(encoding="utf-8"))
except (OSError, ValueError):
    saved_report = {}
saved_flat = bool(saved_report.get("beam_flat", False))


def request_generation():
    st.session_state["regenerate_model"] = True


beam_flat = st.checkbox(
    "Połóż belkę płasko — szerokość 200 mm, wysokość 100 mm",
    value=saved_flat, key="beam_flat", on_change=request_generation,
)
full_frame = st.checkbox(
    "Pełna rama — dwa słupy i belka 3000 mm", value=bool(saved_report.get("full_frame", True)),
    key="full_frame", on_change=request_generation,
)
if full_frame:
    st.caption("Rozstaw osi słupów: 2400 mm · dwa czopy i dwa gniazda w jednej belce.")
width, height = (200, 100) if beam_flat else (100, 200)
st.caption(f"Słup 200×200 mm · belka: szerokość {width} mm, wysokość {height} mm. Zmiana ustawienia przelicza czop i gniazdo.")
clicked_generate = st.button("Wygeneruj poprawiony model", type="primary")
regenerate_requested = st.session_state.pop("regenerate_model", False)
if clicked_generate or regenerate_requested or full_frame != saved_report.get("full_frame", False):
    with st.spinner("Generowanie i sprawdzanie czopa oraz gniazda…"):
        try:
            result = subprocess.run(
                [sys.executable, str(app_dir / "generuj_czop.py")] + (["--flat"] if beam_flat else []) + (["--frame"] if full_frame else []),
                capture_output=True, text=True, timeout=60, check=False,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            st.error(f"Nie udało się wygenerować modelu: {exc}")
            st.stop()
    if result.returncode:
        st.error("Generowanie nie powiodło się.")
        st.code(result.stderr or result.stdout)
        st.stop()
    st.success("Wygenerowano poprawiony model.")
names = (["SLUP_LEWY_200x200", "SLUP_PRAWY_200x200"] if full_frame else ["SLUP_200x200"]) + ["BELKA_100x200"]
labels = (["Słup lewy", "Słup prawy"] if full_frame else ["Słup"]) + ["Belka"]
paths = [base / f"{name}.obj" for name in names]
missing = [p.name for p in paths if not p.exists()]
if missing:
    st.error("Brakuje plików OBJ: " + ", ".join(missing))
    st.info("Kliknij „Wygeneruj poprawiony model” powyżej.")
    st.stop()

# OBJ jest tekstowy; osadzamy go lokalnie w HTML. Viewer nie wysyła modeli na zewnętrzny serwer.
objs = [p.read_text(encoding="utf-8", errors="ignore") for p in paths]
# Bezpieczne osadzenie w JS jako literały JSON.
obj_json = json.dumps(objs)
try:
    import trimesh
    # Import generatora z tego samego katalogu co podgląd.
    import importlib
    sys.path.insert(0, str(app_dir))
    try:
        import generuj_czop
        importlib.reload(generuj_czop)
    finally:
        sys.path.pop(0)
    meshes = {path.stem: trimesh.load_mesh(io.StringIO(obj), file_type="obj")
              for path, obj in zip(paths, objs)}
    generuj_czop.validate_meshes(meshes, beam_flat=beam_flat, full_frame=full_frame)
except ImportError:
    st.error("Brakuje zależności do sprawdzenia i generowania modelu.")
    st.code("python -m pip install -r testy_kumiki/requirements.txt")
    st.stop()
except (ValueError, OSError) as exc:
    st.error("Wczytane pliki zawierają stary lub błędny model: " + str(exc))
    st.info("Kliknij „Wygeneruj poprawiony model” powyżej. Podgląd pojawi się po poprawnym sprawdzeniu geometrii.")
    st.stop()
st.success(f"Sprawdzono pliki OBJ: czop 150 × {width / 3:.2f} mm mieści się w szerokości belki.")
st.caption(f"Oś belki: 2200 mm · spód belki i bark słupa: {2200 - height / 2:.0f} mm · koniec czopa: {2200 + height / 2:.0f} mm.")
st.table([
    {"Element": name, "X [mm]": round(mesh.extents[0], 2),
     "Y [mm]": round(mesh.extents[1], 2), "Z [mm]": round(mesh.extents[2], 2)}
    for name, mesh in meshes.items()
])

html = """
<div id="wrap" style="position:relative;width:100%;height:760px;border-radius:12px;overflow:hidden;background:#e9e5dd">
 <div id="view" style="width:100%;height:100%"></div>
 <div style="position:absolute;left:14px;top:14px;background:rgba(255,255,255,.93);padding:10px 13px;border-radius:9px;font:14px -apple-system,BlinkMacSystemFont,sans-serif">
  <b>Kumiki — rama i połączenia · wersja 6</b><br>
  Chwyć belkę lub słup lewym przyciskiem i przeciągnij.<br>
  Przeciąganie tła: obrót widoku · rolka: zoom · prawy: przesuwanie widoku
 </div>
 <div style="position:absolute;left:14px;right:14px;bottom:14px;background:rgba(255,255,255,.93);padding:12px;border-radius:9px;font:14px -apple-system,BlinkMacSystemFont,sans-serif">
  <label for="separation">Uniesienie belki: <output id="distance">0</output> mm</label>
  <input id="separation" type="range" min="0" max="500" step="5" value="0" style="width:100%;display:block;margin:8px 0">
  <button id="assemble" type="button">Złóż połączenie</button>
  <button id="separate" type="button">Rozsuń elementy</button>
  <div style="display:flex;flex-wrap:wrap;gap:8px;align-items:center;margin-top:10px">
   <label><input id="show-arrows" type="checkbox"> Strzałki do precyzyjnego przesuwania</label>
   <label for="selected">Element:</label><select id="selected"><option value="-1">Wybierz element…</option></select>
   <label>X <input id="move-x" type="number" value="0" step="10" style="width:75px"> mm</label>
   <label>Y <input id="move-y" type="number" value="0" step="10" style="width:75px"> mm</label>
   <label>Z <input id="move-z" type="number" value="0" step="10" style="width:75px"> mm</label>
   <button id="reset-part" type="button">Przywróć element</button>
   <button id="hide-part" type="button">Ukryj element</button>
   <button id="reset-all" type="button">Złóż całą ramę</button>
   <button id="download-part" type="button">Pobierz element OBJ</button>
  </div>
 </div>
</div>
<script type="importmap">{"imports":{"three":"https://cdn.jsdelivr.net/npm/three@0.180.0/build/three.module.js"}}</script>
<script type="module">
import * as THREE from 'three';
import { OrbitControls } from 'https://cdn.jsdelivr.net/npm/three@0.180.0/examples/jsm/controls/OrbitControls.js';
import { OBJLoader } from 'https://cdn.jsdelivr.net/npm/three@0.180.0/examples/jsm/loaders/OBJLoader.js';
import { OBJExporter } from 'https://cdn.jsdelivr.net/npm/three@0.180.0/examples/jsm/exporters/OBJExporter.js';
import { TransformControls } from 'https://cdn.jsdelivr.net/npm/three@0.180.0/examples/jsm/controls/TransformControls.js';

const objTexts = __OBJS__;
const labels = __LABELS__;
const host=document.getElementById('view');
const scene=new THREE.Scene();
scene.background=new THREE.Color(0xe9e5dd);
const camera=new THREE.PerspectiveCamera(40,host.clientWidth/760,1,20000);
camera.up.set(0,0,1);
const renderer=new THREE.WebGLRenderer({antialias:true});
renderer.setPixelRatio(Math.min(devicePixelRatio,2));
renderer.setSize(host.clientWidth,760);
renderer.shadowMap.enabled=true;
renderer.outputColorSpace=THREE.SRGBColorSpace;
renderer.toneMapping=THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure=1.05;
host.appendChild(renderer.domElement);

scene.add(new THREE.HemisphereLight(0xfff8e8,0x756d63,2.4));
const sun=new THREE.DirectionalLight(0xffefd2,3.5);
sun.position.set(-2500,-3000,4500); sun.castShadow=true; scene.add(sun);

const mats=[
 new THREE.MeshStandardMaterial({color:0xb98755,roughness:.78}),
 new THREE.MeshStandardMaterial({color:0xd0a06a,roughness:.78})
];
const loader=new OBJLoader();
const group=new THREE.Group(); scene.add(group);
objTexts.forEach((txt,i)=>{
 const obj=loader.parse(txt);
 const partCenter=new THREE.Box3().setFromObject(obj).getCenter(new THREE.Vector3());
 obj.traverse(o=>{
   if(o.isMesh){
    o.geometry.translate(-partCenter.x,-partCenter.y,-partCenter.z);
    o.material=mats[i===objTexts.length-1?1:0].clone();o.castShadow=true;o.receiveShadow=true;
   }
 });
 obj.position.copy(partCenter);obj.userData.home=partCenter.clone();
 group.add(obj);
});

const box=new THREE.Box3().setFromObject(group);
// Kamera obejmuje również belkę uniesioną o maksymalne 500 mm.
box.max.z+=500;
const center=box.getCenter(new THREE.Vector3());
const size=box.getSize(new THREE.Vector3());
group.position.sub(center);
const maxDim=Math.max(size.x,size.y,size.z,1);
camera.near=Math.max(maxDim/10000,.1);
camera.far=maxDim*20;
camera.updateProjectionMatrix();
camera.position.set(maxDim*1.25,-maxDim*1.45,maxDim*.9);

const controls=new OrbitControls(camera,renderer.domElement);
controls.enableDamping=true; controls.target.set(0,0,0);
const grid=new THREE.GridHelper(maxDim*2,20,0x8d887f,0xc5bfb5);
grid.rotation.x=Math.PI/2; grid.position.z=-size.z/2; scene.add(grid);
const separation=document.getElementById('separation');
const beam=group.children[group.children.length-1];
function setSeparation(value){
 separation.value=String(value);
 beam.position.z=beam.userData.home.z+value;
 document.getElementById('distance').textContent=String(value);
 syncInputs();
}
separation.addEventListener('input',()=>setSeparation(Number(separation.value)));
document.getElementById('assemble').addEventListener('click',()=>setSeparation(0));
document.getElementById('separate').addEventListener('click',()=>setSeparation(350));

const transform=new TransformControls(camera,renderer.domElement);
transform.setMode('translate');transform.setSpace('world');transform.setSize(.75);
scene.add(transform.getHelper());
const showArrows=document.getElementById('show-arrows');
transform.enabled=false;
function updateArrows(){
 transform.enabled=showArrows.checked;
 if(selected&&showArrows.checked)transform.attach(selected);else transform.detach();
}
showArrows.addEventListener('change',updateArrows);
transform.addEventListener('dragging-changed',event=>{controls.enabled=!event.value;});
const select=document.getElementById('selected');
labels.forEach((label,i)=>{const option=document.createElement('option');option.value=String(i);option.textContent=label;select.appendChild(option);});
let selected=null;
function syncInputs(){
 for(const axis of ['x','y','z']){
  const input=document.getElementById('move-'+axis);
  input.disabled=!selected;
  input.value=selected?String(Math.round(selected.position[axis]-selected.userData.home[axis])):'0';
 }
 for(const id of ['reset-part','hide-part','download-part'])document.getElementById(id).disabled=!selected;
 const beamOffset=beam.position.z-beam.userData.home.z;
 separation.value=String(Math.max(0,Math.min(500,beamOffset)));
 document.getElementById('distance').textContent=String(Math.round(beamOffset));
}
function choose(index){
 group.children.forEach(part=>part.traverse(o=>{if(o.isMesh)o.material.emissive.setHex(0x000000);}));
 selected=index>=0?group.children[index]:null;
 select.value=String(index);
 if(selected){selected.visible=true;selected.traverse(o=>{if(o.isMesh)o.material.emissive.setHex(0x302010);});}
 updateArrows();
 syncInputs();
}
select.addEventListener('change',()=>choose(Number(select.value)));
transform.addEventListener('objectChange',syncInputs);
for(const axis of ['x','y','z'])document.getElementById('move-'+axis).addEventListener('change',event=>{
 const value=Number(event.target.value);
 if(selected&&Number.isFinite(value)){selected.position[axis]=selected.userData.home[axis]+value;syncInputs();}
});
document.getElementById('reset-part').addEventListener('click',()=>{if(selected){selected.position.copy(selected.userData.home);selected.visible=true;syncInputs();}});
document.getElementById('hide-part').addEventListener('click',()=>{if(selected){selected.visible=false;choose(-1);}});
document.getElementById('reset-all').addEventListener('click',()=>{
 group.children.forEach(part=>{part.position.copy(part.userData.home);part.visible=true;});choose(-1);syncInputs();
});
document.getElementById('download-part').addEventListener('click',()=>{
 if(!selected)return;
 const exportPart=selected.clone();exportPart.updateMatrixWorld(true);
 const text=new OBJExporter().parse(exportPart);
 const url=URL.createObjectURL(new Blob([text],{type:'text/plain'}));
 const link=document.createElement('a');link.href=url;link.download=labels[Number(select.value)].replaceAll(' ','_')+'.obj';link.click();
 setTimeout(()=>URL.revokeObjectURL(url),1000);
});
const raycaster=new THREE.Raycaster();
const canvas=renderer.domElement;
let pointerStart=null;
let drag=null;
function pointerRay(event){
 const rect=canvas.getBoundingClientRect();
 // Uwzględnij ostatnie przesunięcie również przed kolejną klatką renderowania.
 group.updateMatrixWorld(true);camera.updateMatrixWorld(true);
 raycaster.setFromCamera(new THREE.Vector2((event.clientX-rect.left)/rect.width*2-1,-(event.clientY-rect.top)/rect.height*2+1),camera);
}
canvas.addEventListener('pointerdown',event=>{
 if(event.button!==0||drag)return;
 // Uchwyt strzałki obsługuje TransformControls w swoim trybie.
 if(showArrows.checked&&transform.axis!==null)return;
 pointerStart={id:event.pointerId,x:event.clientX,y:event.clientY};
 pointerRay(event);
 const hit=raycaster.intersectObjects(group.children.filter(part=>part.visible),true)[0];
 if(!hit)return;
 let part=hit.object;while(part.parent!==group)part=part.parent;
 choose(group.children.indexOf(part));
 const plane=new THREE.Plane().setFromNormalAndCoplanarPoint(camera.getWorldDirection(new THREE.Vector3()),hit.point);
 drag={id:event.pointerId,part,plane,offset:part.getWorldPosition(new THREE.Vector3()).sub(hit.point),moved:false};
 // Listener w fazie capture blokuje obrót kamery przed obsługą OrbitControls.
 controls.enabled=false;
 canvas.setPointerCapture(event.pointerId);
 canvas.style.cursor='grabbing';
 event.preventDefault();event.stopImmediatePropagation();
},true);
canvas.addEventListener('pointermove',event=>{
 if(!drag||event.pointerId!==drag.id)return;
 if(!drag.moved&&Math.hypot(event.clientX-pointerStart.x,event.clientY-pointerStart.y)<3)return;
 pointerRay(event);
 const point=raycaster.ray.intersectPlane(drag.plane,new THREE.Vector3());
 if(point){
  drag.moved=true;
  drag.part.position.copy(drag.part.parent.worldToLocal(point.add(drag.offset)));
  syncInputs();
 }
 event.preventDefault();event.stopImmediatePropagation();
},true);
function finishPointer(event){
 if(drag&&event.pointerId===drag.id){
  drag=null;pointerStart=null;controls.enabled=true;canvas.style.cursor='';
  if(canvas.hasPointerCapture(event.pointerId))canvas.releasePointerCapture(event.pointerId);
  event.stopImmediatePropagation();
 }else if(pointerStart&&event.pointerId===pointerStart.id){
  const clicked=Math.hypot(event.clientX-pointerStart.x,event.clientY-pointerStart.y)<5;
  pointerStart=null;
  if(event.type==='pointerup'&&clicked&&!transform.dragging)choose(-1);
 }
}
canvas.addEventListener('pointerup',finishPointer,true);
canvas.addEventListener('pointercancel',finishPointer,true);
canvas.addEventListener('lostpointercapture',finishPointer,true);
syncInputs();

function resize(){const w=host.clientWidth;camera.aspect=w/760;camera.updateProjectionMatrix();renderer.setSize(w,760,false);}
new ResizeObserver(resize).observe(host);
function animate(){if(controls.enabled)controls.update();renderer.render(scene,camera);requestAnimationFrame(animate);}
animate();
</script>
""".replace("__OBJS__", obj_json).replace("__LABELS__", json.dumps(labels, ensure_ascii=False))

components.html(html,height=780,scrolling=False)
st.info("Przesuwanie i ukrywanie służy do oglądania połączeń. Pobieranie OBJ uwzględnia przesunięcie wybranego elementu. Odświeżenie widoku przywraca złożoną ramę.")

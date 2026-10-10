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
st.caption("Wersja podglądu 15 — generator wiaty z dachem")

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
skeleton = st.checkbox(
    "Szkielet przestrzenny — dwie ramy i belki łączące", value=bool(saved_report.get("skeleton", False)),
    key="skeleton", on_change=request_generation,
)
if skeleton:
    full_frame = True
    st.caption("Rozstaw ram: 3000 mm · cztery słupy · cztery belki. Belki łączące leżą na belkach ram; ich połączenia będą dodane w kolejnym etapie.")
if full_frame:
    st.caption("Rozstaw osi słupów: 2400 mm · dwa czopy i dwa gniazda w jednej belce.")
width, height = (200, 100) if beam_flat else (100, 200)
st.caption(f"Słup 200×200 mm · belka: szerokość {width} mm, wysokość {height} mm. Zmiana ustawienia przelicza czop i gniazdo.")
clicked_generate = st.button("Wygeneruj poprawiony model", type="primary")
regenerate_requested = st.session_state.pop("regenerate_model", False)
if clicked_generate or regenerate_requested or full_frame != saved_report.get("full_frame", False) or skeleton != saved_report.get("skeleton", False):
    with st.spinner("Generowanie i sprawdzanie czopa oraz gniazda…"):
        try:
            result = subprocess.run(
                [sys.executable, str(app_dir / "generuj_czop.py")] + (["--flat"] if beam_flat else []) + (["--frame"] if full_frame else []) + (["--skeleton"] if skeleton else []),
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
if skeleton:
    sys.path.insert(0, str(app_dir))
    from generuj_czop import skeleton_parts
    sys.path.pop(0)
    names = list(skeleton_parts(beam_flat))
    labels = list(skeleton_parts(beam_flat).values())
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
    if skeleton:
        generuj_czop.validate_skeleton(meshes, beam_flat=beam_flat)
    else:
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

# Przykłady są wycinane i sprawdzane w Kumiki, a nie imitowane nakładką graficzną.
sys.path.insert(0, str(app_dir))
try:
    from baza_polaczen import read_catalog, example_objects
finally:
    sys.path.pop(0)

@st.cache_data
def load_joint_examples():
    return example_objects()

joint_catalog = read_catalog()
joint_examples = load_joint_examples()


html = """
<div id="wrap" style="position:relative;width:100%;height:760px;border-radius:12px;overflow:hidden;background:#e9e5dd">
 <style>
 #parts-panel{position:absolute;right:14px;top:105px;bottom:235px;width:230px;overflow:auto;background:rgba(255,255,255,.96);border-radius:9px;padding:10px;font:13px -apple-system,BlinkMacSystemFont,sans-serif;box-sizing:border-box}
 #parts-panel summary{font-weight:600;cursor:pointer;padding:6px 0}
 .part-grid{display:grid;grid-template-columns:1fr 1fr;gap:6px}
 .part-card{background:#faf7f0;border:2px solid #ddd5c7;border-radius:7px;padding:5px;cursor:pointer;color:#302820;font:inherit;min-width:0}
 .part-card svg{width:100%;height:54px;display:block;pointer-events:none}
 .part-card span{display:block;overflow-wrap:anywhere;pointer-events:none}
 .part-card small{display:block;color:#6b6258;font-size:10px;pointer-events:none}
 .part-card[aria-pressed="true"]{border-color:#176bb0;background:#eaf4ff}
 .part-card:hover{border-color:#7b9eb8}
 .part-card:focus-visible{outline:3px solid #176bb0;outline-offset:2px}
 #catalog-size{display:grid;grid-template-columns:1fr;gap:4px;margin:7px 0}
 #catalog-size input{width:65px}
 @media(max-width:650px){#parts-panel{width:185px;top:120px;bottom:300px}.part-card svg{height:40px}}
 </style>
 <div id="view" style="width:100%;height:100%"></div>
 <div style="position:absolute;left:14px;top:14px;background:rgba(255,255,255,.93);padding:10px 13px;border-radius:9px;font:14px -apple-system,BlinkMacSystemFont,sans-serif">
  <b>Kumiki — rama i połączenia · wersja 15</b><br>
  Klik = jeden element · Shift/Ctrl/Cmd + klik = dodaj/usuń z zaznaczenia.<br>
  Dwa zaznaczone elementy automatycznie stają się parą A/B do połączenia.<br>
  Chwyć element bez klawisza modyfikującego, aby go przeciągnąć.<br>
  Przeciąganie tła: obrót widoku · rolka: zoom · prawy: przesuwanie widoku
 </div>
 <div id="measurement" style="position:absolute;left:14px;top:100px;background:rgba(255,255,255,.94);padding:7px;border-radius:6px;font:13px sans-serif" hidden></div>
 <aside id="parts-panel" aria-label="Graficzny wybór elementów">
  <details open><summary>Generator wiaty z opisu</summary>\n   <p style="margin:4px 0">Np. „Wiata 7x6 m, 9 słupów, dach dwuspadowy 25 stopni, wysokość 3 m”.</p>\n   <textarea id="carport-prompt" rows="4" style="width:100%;box-sizing:border-box" placeholder="Wiata 7x6 m, 9 słupów, dach dwuspadowy 25 stopni, wysokość 3 m"></textarea>\n   <button id="parse-carport" type="button">Odczytaj opis</button>\n   <p id="carport-preview">Podaj wymiary i liczbę słupów.</p>\n   <label>Wysokość <input id="carport-height" type="number" value="2800" min="1800" max="6000" step="100" style="width:70px"> mm</label><br>\n   <button id="generate-carport" type="button" disabled>Wygeneruj wiatę 3D</button>\n   <small>Model geometryczny — konstrukcja nie została zweryfikowana obliczeniowo.</small>\n  </details>\n  <details open><summary>Katalog — dodaj element</summary>
   <p style="margin:4px 0">Przeciągnij kafelek do widoku 3D albo kliknij, aby dodać.</p>
   <div id="catalog-size">
    <label>Długość <input id="part-length" type="number" min="50" max="20000" step="50" value="3000"> mm</label>
    <label>Szerokość <input id="part-width" type="number" min="10" max="1000" step="10" value="100"> mm</label>
    <label>Wysokość <input id="part-height" type="number" min="10" max="1000" step="10" value="200"> mm</label>
   </div>
   <label>Liczba sztuk <input id="part-count" type="number" min="1" max="100" step="1" value="1" style="width:55px"></label><br>
   <label><input id="custom-size" type="checkbox"> Użyj powyższych wymiarów</label>
   <div id="catalog" class="part-grid" style="margin-top:8px"></div>
   <small>Nowe części mają pełny przekrój. Wycięcia połączeń nie są przeliczane przy przesuwaniu.</small>
  </details>
  <details><summary>Dokładne ustawienie</summary>
   <button id="pin-reference" type="button">Użyj zaznaczonego jako odniesienia</button>
   <p id="reference-name">Odniesienie: brak</p>
   <label><input id="relative-add" type="checkbox"> Dodawaj względem odniesienia</label><br>
   <label>Kierunek <select id="relative-axis"><option value="x">X — wzdłuż</option><option value="y">Y — w bok</option><option value="z">Z — w górę</option></select></label><br>
   <label>Odległość <input id="relative-distance" type="number" value="2000" step="10" style="width:75px"> mm</label><br>
   <label>Pomiar <select id="relative-measure"><option value="centers">Między środkami</option><option value="edges">Prześwit między krawędziami</option></select></label><br>
   <label><input id="align-bottom" type="checkbox" checked> Wyrównaj spód (dla kierunków X/Y)</label><br>
   <label>Rozstaw serii <input id="relative-step" type="number" value="2000" min="1" step="10" style="width:75px"> mm</label><br>
   <button id="position-selected" type="button">Ustaw zaznaczony element</button>
   <small>Odległość ujemna ustawia część w przeciwnym kierunku. To dokładne ustawienie jednorazowe; później możesz przeciągać części niezależnie.</small>
  </details>
  <details><summary>Baza połączeń</summary>
   <label>Kategoria <select id="joint-filter"><option value="all">Wszystkie</option><option value="Ciesielskie">Ciesielskie</option><option value="Stolarskie">Stolarskie</option></select></label>
   <div id="joint-catalog" class="part-grid" style="margin-top:8px"></div>
   <p id="joint-info">Wybierz połączenie, aby zobaczyć opis i dostępność.</p>
   <label>A: <select id="joint-select-a"><option value="-1">Wybierz element A…</option></select></label><br>
   <label>B: <select id="joint-select-b"><option value="-1">Wybierz element B…</option></select></label><br>
   <button id="clear-joint-pair" type="button">Wyczyść parę</button><br>
   <button id="set-joint-a" type="button">Zaznaczony → element A</button>
   <button id="set-joint-b" type="button">Zaznaczony → element B</button>
   <p id="joint-pair">A: brak · B: brak</p>
   <button id="apply-joint" type="button" disabled>Wykonaj połączenie w A i B</button>
   <p style="font-size:11px">Czop–gniazdo: A = słup, B = belka. Pół drewna: dwie prostopadłe belki. Najpierw ustaw części w miejscu styku. Czop przedłuża górę słupa do góry belki.</p>
   <button id="add-joint-example" type="button" disabled>Dodaj przykład z wycięciami</button>
   <small>Przykład dodaje nowe części. „Wykonaj połączenie” wycina w Twoich częściach A i B. Po przesunięciu wycięcia nie przeliczają się automatycznie.</small>
  </details>
  <details open><summary>Elementy w modelu</summary><div id="model-parts" class="part-grid"></div></details>
  <p id="model-counts" style="margin:8px 0"></p>
  <button id="save-project" type="button">Zapisz projekt</button>
  <button id="load-project" type="button">Wczytaj projekt</button>
  <input id="project-file" type="file" accept=".json,application/json" hidden>
  <div id="part-status" role="status" aria-live="polite" style="margin-top:8px"></div>
 </aside>
 <div style="position:absolute;left:14px;right:14px;bottom:14px;background:rgba(255,255,255,.93);padding:12px;border-radius:9px;font:14px -apple-system,BlinkMacSystemFont,sans-serif">
  <label for="separation">Uniesienie belek: <output id="distance">0</output> mm</label>
  <input id="separation" type="range" min="0" max="500" step="5" value="0" style="width:100%;display:block;margin:8px 0">
  <button id="assemble" type="button">Złóż połączenie</button>
  <button id="separate" type="button">Rozsuń elementy</button>
  <div style="display:flex;flex-wrap:wrap;gap:8px;align-items:center;margin-top:10px">
   <label><input id="pair-mode" type="checkbox"> Zaznacz dwa elementy do połączenia</label>
   <label><input id="show-arrows" type="checkbox"> Strzałki do precyzyjnego przesuwania</label>
   <label for="selected">Element:</label><select id="selected"><option value="-1">Wybierz element…</option></select>
   <label>X <input id="move-x" type="number" value="0" step="10" style="width:75px"> mm</label>
   <label>Y <input id="move-y" type="number" value="0" step="10" style="width:75px"> mm</label>
   <label>Z <input id="move-z" type="number" value="0" step="10" style="width:75px"> mm</label>
   <button id="reset-part" type="button">Przywróć element</button>
   <button id="hide-part" type="button">Ukryj element</button>
   <button id="fit-all" type="button">Pokaż wszystkie elementy</button>
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
const modelConfig = __MODEL__;
const jointCatalog=__JOINTS__;
const jointObjTexts=__EXAMPLES__;
const restoredProject=__RESTORE__;
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
    o.material=mats[labels[i].startsWith('Belka')?1:0].clone();o.castShadow=true;o.receiveShadow=true;
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
const beams=group.children.filter((part,i)=>labels[i].startsWith('Belka'));
function setSeparation(value){
 separation.value=String(value);
 beams.forEach(part=>{part.position.z=part.userData.home.z+value;});
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
const selectedIndices=new Set();
let reference=null;
const dimensionLine=new THREE.Line(new THREE.BufferGeometry(),new THREE.LineBasicMaterial({color:0x176bb0,depthTest:false}));
dimensionLine.renderOrder=10;dimensionLine.visible=false;scene.add(dimensionLine);
function updateDimension(){
 const badge=document.getElementById('measurement');
 dimensionLine.visible=Boolean(reference&&selected&&reference!==selected&&reference.visible&&selected.visible);
 badge.hidden=!dimensionLine.visible;if(!dimensionLine.visible)return;
 group.updateMatrixWorld(true);
 const a=new THREE.Box3().setFromObject(reference),b=new THREE.Box3().setFromObject(selected);
 const p=a.getCenter(new THREE.Vector3()),q=b.getCenter(new THREE.Vector3());
 const axis=document.getElementById('relative-axis').value;
 let value=q[axis]-p[axis];const sign=value<0?-1:1;
 const edges=document.getElementById('relative-measure').value==='edges';
 if(edges){p[axis]+=sign*(a.max[axis]-a.min[axis])/2;q[axis]-=sign*(b.max[axis]-b.min[axis])/2;value=q[axis]-p[axis];}
 const end=p.clone();end[axis]=q[axis];
 dimensionLine.geometry.setFromPoints([p,end,q]);
 badge.textContent=(edges?'Krawędzie':'Środki')+' · '+axis.toUpperCase()+': '+value.toFixed(1)+' mm';
}

document.getElementById('pin-reference').addEventListener('click',()=>{
 if(!selected){document.getElementById('part-status').textContent='Najpierw zaznacz element odniesienia.';return;}
 reference=selected;document.getElementById('reference-name').textContent='Odniesienie: '+labels[group.children.indexOf(reference)];
});
function relativePosition(part,serial=0){
 if(!reference||reference===part)throw new Error('Wskaż inny element odniesienia.');
 const axis=document.getElementById('relative-axis').value;
 const distance=Number(document.getElementById('relative-distance').value);
 const step=Number(document.getElementById('relative-step').value);
 if(!['x','y','z'].includes(axis)||!Number.isFinite(distance)||Math.abs(distance)>100000||!Number.isFinite(step)||step<=0||step>100000)throw new Error('Sprawdź odległość i rozstaw serii (do 100000 mm).');
 group.updateMatrixWorld(true);part.updateMatrixWorld(true);
 const a=new THREE.Box3().setFromObject(reference),b=new THREE.Box3().setFromObject(part);
 const ac=a.getCenter(new THREE.Vector3()),bc=b.getCenter(new THREE.Vector3());
 const desired=ac.clone();const signed=distance+serial*step;
 desired[axis]+=signed;
 if(document.getElementById('relative-measure').value==='edges')desired[axis]+=(signed<0?-1:1)*((a.max[axis]-a.min[axis]+b.max[axis]-b.min[axis])/2);
 if(axis!=='z'&&document.getElementById('align-bottom').checked)desired.z=a.min.z+(b.max.z-b.min.z)/2;
 const worldOrigin=part.getWorldPosition(new THREE.Vector3()).add(desired.sub(bc));
 return group.worldToLocal(worldOrigin);
}
document.getElementById('position-selected').addEventListener('click',()=>{
 try{
  if(!selected)throw new Error('Zaznacz element do ustawienia.');
  selected.position.copy(relativePosition(selected));syncInputs();
  document.getElementById('part-status').textContent='Ustawiono element w podanej odległości. Wymiary w mm.';
 }catch(error){document.getElementById('part-status').textContent=error.message;}
});
const partCards=[];
const basePartCount=group.children.length;
const baseOriginals=group.children.map(part=>part.clone());
const baseLabels=labels.slice();
function timberIcon(part){
 // Miniatura rzeczywistej siatki OBJ: rzut izometryczny, osobny od kamery sceny.
 const vertices=[];const faces=[];
 const view=new THREE.Vector3(1,-1,.8).normalize();
 const right=new THREE.Vector3(1,1,0).normalize();
 const up=new THREE.Vector3().crossVectors(view,right).normalize();
 part.updateMatrix();
 part.traverse(mesh=>{
  if(!mesh.isMesh)return;
  mesh.updateMatrix();
  const geometry=mesh.geometry;const positions=geometry.attributes.position;
  const projected=[];
  for(let i=0;i<positions.count;i++){
   const v=new THREE.Vector3().fromBufferAttribute(positions,i).applyMatrix4(mesh.matrix);
   const point=[v.dot(right),-v.dot(up),v.dot(view)];projected.push(point);vertices.push(point);
  }
  const indices=geometry.index;
  const count=indices?indices.count:positions.count;
  for(let i=0;i<count;i+=3){
   const points=[0,1,2].map(j=>projected[indices?indices.getX(i+j):i+j]);
   const a=new THREE.Vector3(...points[0]),b=new THREE.Vector3(...points[1]),c=new THREE.Vector3(...points[2]);
   const normal=b.sub(a).cross(c.sub(a)).normalize();
   const light=.65+.3*Math.abs(normal.dot(new THREE.Vector3(.3,-.5,1).normalize()));
   const shade='rgb('+[211,163,105].map(value=>Math.round(value*light)).join(',')+')';
   faces.push({points,shade,depth:points.reduce((a,p)=>a+p[2],0)/3});
  }
 });
 const xs=vertices.map(p=>p[0]),ys=vertices.map(p=>p[1]);
 const minX=Math.min(...xs),minY=Math.min(...ys);
 const scale=Math.min(88/Math.max(1,Math.max(...xs)-minX),48/Math.max(1,Math.max(...ys)-minY));
 faces.sort((a,b)=>a.depth-b.depth);
 const offsetX=50-(Math.max(...xs)-minX)*scale/2,offsetY=30-(Math.max(...ys)-minY)*scale/2;
 return '<svg viewBox="0 0 100 60" aria-hidden="true">'+faces.map(f=>'<polygon points="'+f.points.map(p=>[(p[0]-minX)*scale+offsetX,(p[1]-minY)*scale+offsetY].join(',')).join(' ')+'" fill="'+f.shade+'" stroke="#986b3d" stroke-width=".3"/>').join('')+'</svg>';
}
function registerPart(index){
 const part=group.children[index];
 const option=document.createElement('option');option.value=String(index);option.textContent=labels[index];
 // Początkowe opcje są już dodane powyżej.
 if(index>=select.options.length-1)select.appendChild(option);
 const card=document.createElement('button');card.type='button';card.className='part-card';
 card.setAttribute('aria-pressed','false');card.setAttribute('aria-label','Wybierz: '+labels[index]);
 card.innerHTML=timberIcon(part);
 const caption=document.createElement('span');caption.textContent=labels[index];card.appendChild(caption);
 const size=new THREE.Box3();part.traverse(o=>{if(o.isMesh){o.geometry.computeBoundingBox();size.union(o.geometry.boundingBox);}});
 const dimensions=size.getSize(new THREE.Vector3()).toArray().map(Math.round).join(' × ');
 const detail=document.createElement('small');detail.textContent=dimensions+' mm';card.appendChild(detail);
 card.addEventListener('click',event=>selectPart(index,event.shiftKey));
 for(const id of ['joint-select-a','joint-select-b']){
  const choice=document.createElement('option');choice.value=String(index);choice.textContent=labels[index];document.getElementById(id).appendChild(choice);
 }
 document.getElementById('model-parts').appendChild(card);partCards.push(card);
}
group.children.forEach((part,index)=>registerPart(index));
const catalog=[
 {label:'Słup',length:2200,width:200,height:200,axis:'z',angle:0},
 {label:'Belka na sztorc',length:3000,width:100,height:200,axis:'x',angle:0},
 {label:'Belka płasko',length:3000,width:200,height:100,axis:'x',angle:0},
 {label:'Miecz',length:900,width:100,height:100,axis:'z',angle:45},
 {label:'Krokiew',length:3500,width:80,height:180,axis:'x',angle:-12},
 {label:'Płatew',length:3000,width:140,height:200,axis:'x',angle:0}
];
function catalogPart(type,dimensions=null){
 const spec=catalog[type];const custom=document.getElementById('custom-size').checked;
 const dims=dimensions||['length','width','height'].map(key=>custom?Number(document.getElementById('part-'+key).value):spec[key]);
 if(dims.some((n,i)=>!Number.isFinite(n)||n<(i===0?50:10)||n>(i===0?20000:1000)))throw new Error('Sprawdź wymiary: długość 50–20000 mm, przekrój 10–1000 mm.');
 const [length,width,height]=dims;
 const geometry=new THREE.BoxGeometry(...(spec.axis==='z'?[width,height,length]:[length,width,height]));
 geometry.rotateY(spec.angle*Math.PI/180);
 const part=new THREE.Group();part.add(new THREE.Mesh(geometry,mats[spec.axis==='z'?0:1].clone()));
 part.userData.definition={type,dimensions:dims};
 return part;
}
function addCatalogPart(type,event=null){
 try{
  const count=Number(document.getElementById('part-count').value);
  if(!Number.isInteger(count)||count<1||count>100)throw new Error('Liczba sztuk musi być całkowita: od 1 do 100.');
  if(group.children.length+count>500)throw new Error('Projekt może zawierać maksymalnie 500 elementów.');
  const first=catalogPart(type);
  if(document.getElementById('relative-add').checked)relativePosition(first);
  let position=controls.target.clone();
  if(event){
   pointerRay(event);
   const plane=new THREE.Plane().setFromNormalAndCoplanarPoint(camera.getWorldDirection(new THREE.Vector3()),position);
   const hit=raycaster.ray.intersectPlane(plane,new THREE.Vector3());if(hit)position=hit;
  }
  group.updateMatrixWorld(true);const origin=group.worldToLocal(position);
  const spacing=new THREE.Box3().setFromObject(first).getSize(new THREE.Vector3()).y+150;
  for(let i=0;i<count;i++){
   const part=i===0?first:catalogPart(type,first.userData.definition.dimensions);
   if(document.getElementById('relative-add').checked)part.position.copy(relativePosition(part,i));
   else part.position.copy(origin).add(new THREE.Vector3(0,(i-(count-1)/2)*spacing,0));
   part.userData.home=part.position.clone();part.userData.added=true;
   part.traverse(o=>{if(o.isMesh){o.castShadow=true;o.receiveShadow=true;}});
   group.add(part);
   const index=group.children.length-1;labels.push(catalog[type].label+' '+(index+1));
   if(catalog[type].label.startsWith('Belka'))beams.push(part);
   registerPart(index);
  }
  choose(group.children.length-count);
  if(count>1)fitAll();
  document.getElementById('part-status').textContent='Dodano '+count+' szt.: '+catalog[type].label+'. Każdą część możesz przeciągnąć osobno.';
 }catch(error){document.getElementById('part-status').textContent=error.message;}
}
function meshPart(definition){
 if(typeof definition.mesh!=='string'||definition.mesh.length>2000000)throw new Error('Nieprawidłowa geometria wyciętego elementu.');
 const part=loader.parse(definition.mesh);
 let hasMesh=false;part.traverse(o=>{if(o.isMesh){hasMesh=true;o.material=mats[0].clone();}});
 if(!hasMesh)throw new Error('Brak geometrii wyciętego elementu.');
 part.userData.definition=definition;return part;
}
function jointPart(jointId,member){
 const text=jointObjTexts[jointId]?.[member];if(!text)throw new Error('Nieznany przykład połączenia.');
 const part=loader.parse(text);
 const center=new THREE.Box3().setFromObject(part).getCenter(new THREE.Vector3());
 part.traverse(o=>{if(o.isMesh){o.geometry.translate(-center.x,-center.y,-center.z);o.material=mats[member%2].clone();}});
 part.userData.definition={joint:jointId,member};part.userData.exampleCenter=center;
 return part;
}
function jointDiagram(id){
 const shapes={
  wrab:'<path d="M10 42h80v12H10z"/><path d="M20 35l48-27 8 14-22 12v8H40v-1L28 47z"/>',
  miecz_czop:'<path d="M14 6h13v48H14zM14 6h75v13H14z"/><path d="M25 44l36-30 8 9-36 30z"/>',
  nakladka:'<path d="M8 18h42v10h42v13H50V31H8z"/>',
  jaskolczy:'<path d="M8 17h37l-6 9 6 9H8zM92 17H55l-6 9 6 9h37z"/>',
  czop_podwojny:'<path d="M8 10h34v9h17v8H42v7h17v8H42v9H8zM67 10h24v41H67z"/>',
  kolki:'<path d="M8 12h30v38H8zM65 12h28v38H65z"/><path d="M32 20h39v5H32zM32 36h39v5H32z"/>',
  wpust_pioro:'<path d="M8 12h35v14h15v9H43v14H8zM91 12H66v37h25z"/>',
  obce_pioro:'<path d="M8 12h29v37H8zM68 12h24v37H68z"/><path d="M30 26h46v9H30z"/>',
  zakladka:'<path d="M8 15h55v12H37v16H8zM46 34h20V18h26v28H46z"/>',
  wczepy:'<path d="M8 10h34v8h15v8H42v8h15v8H42v8H8zM91 10H65v40h26z"/>'
 };
 return '<svg viewBox="0 0 100 60" aria-hidden="true"><g fill="#d1a36a" stroke="#986b3d" stroke-width="1">'+(shapes[id]||'')+'</g></svg>';
}
let selectedJoint=null;
let jointA=-1,jointB=-1;
function syncPair(){
 document.getElementById('joint-select-a').value=String(jointA);
 document.getElementById('joint-select-b').value=String(jointB);
 refreshSelection();
 document.getElementById('joint-pair').textContent='A: '+(labels[jointA]||'brak')+' · B: '+(labels[jointB]||'brak');
 document.getElementById('apply-joint').disabled=jointA<0||jointB<0||jointA===jointB||!selectedJoint||!jointObjTexts[selectedJoint.id];
}
function setPairMember(role,index){
 if(role==='a'){jointA=index;if(jointB===index)jointB=-1;}
 else{jointB=index;if(jointA===index)jointA=-1;}
 if(index>=0)choose(index);syncPair();
}
for(const [id,role] of [['joint-select-a','a'],['joint-select-b','b']])document.getElementById(id).addEventListener('change',event=>setPairMember(role,Number(event.target.value)));
document.getElementById('clear-joint-pair').addEventListener('click',()=>{jointA=-1;jointB=-1;syncPair();});
document.getElementById('pair-mode').addEventListener('change',event=>{
 if(event.target.checked){jointA=-1;jointB=-1;syncPair();}
});
function syncJointPairFromSelection(){
 const pair=[...selectedIndices].filter(i=>i>=0&&i<group.children.length).slice(0,2);
 jointA=pair.length>0?pair[0]:-1;
 jointB=pair.length>1?pair[1]:-1;
}
function selectPart(index,additive=false){
 if(index<0){
  selectedIndices.clear();
  jointA=-1;jointB=-1;
  choose(-1);syncPair();return;
 }
 if(additive){
  if(selectedIndices.has(index))selectedIndices.delete(index);
  else selectedIndices.add(index);
 }else{
  selectedIndices.clear();
  selectedIndices.add(index);
 }
 const active=selectedIndices.has(index)?index:([ ...selectedIndices ].at(-1)??-1);
 choose(active);
 syncJointPairFromSelection();
 syncPair();
 const count=selectedIndices.size;
 document.getElementById('part-status').textContent=count
  ?('Zaznaczono '+count+(count===1?' element.':' elementy.'))
  :'Brak zaznaczenia.';
}
for(const [id,role] of [['set-joint-a','a'],['set-joint-b','b']])document.getElementById(id).addEventListener('click',()=>{
 if(!selected){document.getElementById('part-status').textContent='Najpierw zaznacz element w modelu.';return;}
 setPairMember(role,group.children.indexOf(selected));
});
document.getElementById('apply-joint').addEventListener('click',()=>{
 if(jointA<0||jointB<0||jointA===jointB||!selectedJoint)return;
 const sources=[jointA,jointB].map(index=>{
  const part=group.children[index].clone();part.updateMatrixWorld(true);return new OBJExporter().parse(part);
 });
 document.getElementById('apply-joint').disabled=true;
 document.getElementById('part-status').textContent='Wycinanie i sprawdzanie połączenia…';
 window.parent.postMessage({type:'kumiki:apply',request:{id:Date.now()+'-'+Math.random(),joint:selectedJoint.id,
  indices:[jointA,jointB],base_count:basePartCount,state:projectState(),sources,
  camera:{position:camera.position.toArray(),target:controls.target.toArray()}}},'*');
});
const jointCards=[];
jointCatalog.forEach(entry=>{
 const card=document.createElement('button');card.type='button';card.className='part-card';
 card.setAttribute('aria-pressed','false');
 if(jointObjTexts[entry.id]){
  const assembly=new THREE.Group();jointObjTexts[entry.id].forEach((text,i)=>{
   const part=jointPart(entry.id,i);part.position.copy(part.userData.exampleCenter);
   // Uwzględnij pozycję części w miniaturze całego węzła.
   part.traverse(o=>{if(o.isMesh)o.geometry.translate(part.position.x,part.position.y,part.position.z);});
   assembly.add(part);
  });card.innerHTML=timberIcon(assembly);
 }else card.innerHTML=jointDiagram(entry.id);
 const title=document.createElement('span');title.textContent=entry.name;card.appendChild(title);
 const status=document.createElement('small');status.textContent=jointObjTexts[entry.id]?'Wycięcia: przykład 3D':'Katalog — bez generatora';card.appendChild(status);
 card.addEventListener('click',()=>{
  selectedJoint=entry;
  jointCards.forEach(({card,item})=>card.setAttribute('aria-pressed',String(item===entry)));
  document.getElementById('joint-info').textContent=entry.category+'. '+entry.description+' '+entry.parameters;
  document.getElementById('add-joint-example').disabled=!jointObjTexts[entry.id];syncPair();
 });
 document.getElementById('joint-catalog').appendChild(card);jointCards.push({card,item:entry});
});
document.getElementById('joint-filter').addEventListener('change',event=>{
 jointCards.forEach(({card,item})=>{card.hidden=event.target.value!=='all'&&!item.category.includes(event.target.value);});
});
document.getElementById('add-joint-example').addEventListener('click',()=>{
 try{
  if(!selectedJoint||!jointObjTexts[selectedJoint.id])throw new Error('Wybierz gotowy przykład połączenia.');
  if(group.children.length+2>500)throw new Error('Projekt może zawierać maksymalnie 500 elementów.');
  const id=selectedJoint.id;
  const parts=[jointPart(id,0),jointPart(id,1)];
  const assemblyCenter=new THREE.Box3();
  parts.forEach(part=>{part.position.copy(part.userData.exampleCenter);assemblyCenter.expandByObject(part);});
  const origin=assemblyCenter.getCenter(new THREE.Vector3());
  group.updateMatrixWorld(true);const destination=group.worldToLocal(controls.target.clone());
  parts.forEach((part,member)=>{
   part.position.sub(origin).add(destination);part.userData.home=part.position.clone();part.userData.added=true;
   part.traverse(o=>{if(o.isMesh){o.castShadow=true;o.receiveShadow=true;}});
   group.add(part);const index=group.children.length-1;
   labels.push((id==='czop_gniazdo'&&member===0?'Słup':'Belka')+' — '+selectedJoint.name+' '+(index+1));
   registerPart(index);if(labels[index].startsWith('Belka'))beams.push(part);
  });choose(group.children.length-2);fitAll();
  document.getElementById('part-status').textContent='Dodano dwa elementy z rzeczywistymi wycięciami: '+selectedJoint.name;
 }catch(error){document.getElementById('part-status').textContent=error.message;}
});
function fitAll(){
 group.updateMatrixWorld(true);
 const box=new THREE.Box3();group.children.filter(part=>part.visible).forEach(part=>box.expandByObject(part));
 if(box.isEmpty())return;
 const target=box.getCenter(new THREE.Vector3()),size=box.getSize(new THREE.Vector3());
 const direction=camera.position.clone().sub(controls.target).normalize();
 const radius=Math.max(size.length()/2,100);
 const distance=radius/Math.sin(Math.atan(Math.tan(camera.fov*Math.PI/360)*Math.min(camera.aspect,1)))*1.15;
 controls.target.copy(target);camera.position.copy(target).addScaledVector(direction,distance);
 camera.far=Math.max(20000,distance*4);camera.updateProjectionMatrix();controls.update();
}
document.getElementById('fit-all').addEventListener('click',fitAll);
function projectState(){
 return {format:'kumiki-layout',version:1,model:modelConfig,
  parts:group.children.map((part,i)=>({label:labels[i],position:part.position.toArray(),home:part.userData.home.toArray(),visible:part.visible,
   definition:part.userData.definition||null}))};
}
function saveProject(){
 const data=projectState();
 const url=URL.createObjectURL(new Blob([JSON.stringify(data,null,2)],{type:'application/json'}));
 const link=document.createElement('a');link.href=url;link.download='projekt-wiaty.json';link.click();
 setTimeout(()=>URL.revokeObjectURL(url),1000);
 document.getElementById('part-status').textContent='Zapisano układ, wymiary i widoczność elementów w pliku projektu.';
}
function loadProject(data){
 if(!data||data.format!=='kumiki-layout'||data.version!==1||!Array.isArray(data.parts)||data.parts.length<basePartCount||data.parts.length>500)throw new Error('Nieprawidłowy plik projektu.');
 if(!data.model||Object.keys(modelConfig).some(key=>data.model[key]!==modelConfig[key]))throw new Error('Najpierw ustaw te same opcje: belka płasko, pełna rama i szkielet przestrzenny, co w zapisanym projekcie.');
 const vector=value=>Array.isArray(value)&&value.length===3&&value.every(n=>typeof n==='number'&&Number.isFinite(n)&&Math.abs(n)<=1000000);
 // Sprawdź całość przed zastąpieniem bieżącego układu.
 const staged=data.parts.map((entry,i)=>{
  if(!entry||typeof entry.label!=='string'||entry.label.length>100||typeof entry.visible!=='boolean'||!vector(entry.position)||!vector(entry.home))throw new Error('Projekt zawiera błędne dane elementu.');
  if(i<basePartCount){
   if(entry.label!==baseLabels[i]||new THREE.Vector3(...entry.home).distanceTo(group.children[i].userData.home)>.001)throw new Error('Projekt nie pasuje do elementów bazowych.');
   if(entry.definition===null)return baseOriginals[i].clone();
   if(entry.definition?.mesh)return meshPart(entry.definition);
   throw new Error('Nieznana geometria bazowego elementu.');
  }
  const def=entry.definition;
  if(def?.mesh)return meshPart(def);
  if(def&&typeof def.joint==='string'&&Number.isInteger(def.member)&&[0,1].includes(def.member))return jointPart(def.joint,def.member);
  if(!def||!Number.isInteger(def.type)||!catalog[def.type]||!Array.isArray(def.dimensions)||def.dimensions.length!==3||def.dimensions.some(n=>typeof n!=='number'))throw new Error('Projekt zawiera nieznany typ elementu.');
  return catalogPart(def.type,def.dimensions);
 });
 selectedIndices.clear();choose(-1);jointA=-1;jointB=-1;syncPair();reference=null;document.getElementById('reference-name').textContent='Odniesienie: brak';
 while(group.children.length>basePartCount){
  const part=group.children[group.children.length-1];group.remove(part);
  part.traverse(o=>{if(o.isMesh){o.geometry.dispose();o.material.dispose();}});
 }
 labels.length=basePartCount;
 staged.forEach((part,i)=>{if(part){
  if(i<basePartCount){
   const original=group.children[i];original.clear();
   [...part.children].forEach(child=>original.add(child));original.userData.definition=data.parts[i].definition;
  }else{group.add(part);labels.push(data.parts[i].label);part.userData.added=true;}
 }});
 data.parts.forEach((entry,i)=>{
  const part=group.children[i];part.position.fromArray(entry.position);part.visible=entry.visible;
  if(i>=basePartCount)part.userData.home=new THREE.Vector3(...entry.home);
  part.traverse(o=>{if(o.isMesh){o.castShadow=true;o.receiveShadow=true;}});
 });
 beams.length=0;group.children.forEach((part,i)=>{if(labels[i].startsWith('Belka'))beams.push(part);});
 select.replaceChildren();const placeholder=document.createElement('option');placeholder.value='-1';placeholder.textContent='Wybierz element…';select.appendChild(placeholder);
 document.getElementById('model-parts').replaceChildren();partCards.length=0;
 for(const id of ['joint-select-a','joint-select-b']){
  const list=document.getElementById(id);list.replaceChildren();const empty=document.createElement('option');empty.value='-1';empty.textContent='Wybierz element…';list.appendChild(empty);
 }
 group.children.forEach((part,i)=>registerPart(i));choose(-1);fitAll();
 document.getElementById('part-status').textContent='Wczytano projekt: '+group.children.length+' elementów.';
}
document.getElementById('save-project').addEventListener('click',saveProject);
const projectFile=document.getElementById('project-file');
document.getElementById('load-project').addEventListener('click',()=>projectFile.click());
projectFile.addEventListener('change',async()=>{
 const file=projectFile.files[0];if(!file)return;
 try{
  if(file.size>2000000)throw new Error('Plik projektu jest zbyt duży.');
  loadProject(JSON.parse(await file.text()));
 }catch(error){document.getElementById('part-status').textContent=error.message;}
 finally{projectFile.value='';}
});


let parsedCarport=null;
function parseCarport(text){
 const t=text.toLowerCase().replaceAll('×','x').replaceAll(',','.');
 const pair=t.match(/([0-9]+(?:\.[0-9]+)?)\s*x\s*([0-9]+(?:\.[0-9]+)?)\s*(m|mm)?/);
 const wm=t.match(/szeroko[a-ząćęłńóśźż]*\s*(?:ma\s*mieć\s*)?([0-9]+(?:\.[0-9]+)?)\s*(m|mm)?/);
 const lm=t.match(/długo[a-ząćęłńóśźż]*\s*(?:ma\s*mieć\s*)?([0-9]+(?:\.[0-9]+)?)\s*(m|mm)?/);
 const pm=t.match(/([0-9]+)\s*(?:słup[a-ząćęłńóśźż]*|slup[a-z]*)/);
 const mm=(v,u)=>Number(v)*(u==='mm'?1:1000);
 const width=wm?mm(wm[1],wm[2]||'m'):pair?mm(pair[1],pair[3]||'m'):null;
 const length=lm?mm(lm[1],lm[2]||'m'):pair?mm(pair[2],pair[3]||'m'):null;
 const posts=pm?Number(pm[1]):null;
 const roof=t.includes('jednospad')?'single':t.includes('dwuspad')?'gable':'none';
 const angleMatch=t.match(/([0-9]+(?:\.[0-9]+)?)\s*(?:stopni|°)/);
 const angle=angleMatch?Number(angleMatch[1]):roof==='none'?0:20;
 const heightMatch=t.match(/wysoko[a-ząćęłńóśźż]*\s*(?:ma\s*mieć\s*)?([0-9]+(?:\.[0-9]+)?)\s*(m|mm)?/);
 const height=heightMatch?mm(heightMatch[1],heightMatch[2]||'m'):null;
 if(!width||!length||width<2000||length<2000||width>20000||length>20000)throw new Error('Podaj wymiary od 2 do 20 m, np. 7x6 m.');
 if(!Number.isInteger(posts)||posts<4||posts>40)throw new Error('Podaj od 4 do 40 słupów.');
 if(angle<0||angle>60)throw new Error('Kąt dachu musi mieć od 0 do 60 stopni.');
 return {width,length,posts,roof,angle,height};
}
function carportPostPositions(w,l,n){
 const a=[];
 if(n===9){for(const y of [-l/2,0,l/2])for(const x of [-w/2,0,w/2])a.push([x,y]);return a;}
 const p=2*(w+l);
 for(let i=0;i<n;i++){let d=i*p/n,x=-w/2,y=-l/2;if(d<=w)x+=d;else if((d-=w)<=l){x=w/2;y+=d;}else if((d-=l)<=w){x=w/2-d;y=l/2;}else{x=-w/2;y=l/2-(d-w);}a.push([x,y]);}
 return a;
}
function addCarportMember(type,dims,pos,label){
 const part=catalogPart(type,dims);part.position.copy(pos);part.userData.home=part.position.clone();part.userData.added=true;
 part.traverse(o=>{if(o.isMesh){o.castShadow=true;o.receiveShadow=true;}});
 group.add(part);labels.push(label);const i=group.children.length-1;if(catalog[type].label.startsWith('Belka'))beams.push(part);registerPart(i);return i;
}
document.getElementById('parse-carport').addEventListener('click',()=>{
 try{parsedCarport=parseCarport(document.getElementById('carport-prompt').value);if(parsedCarport.height)document.getElementById('carport-height').value=String(parsedCarport.height);const roofName=parsedCarport.roof==='gable'?'dach dwuspadowy':parsedCarport.roof==='single'?'dach jednospadowy':'bez automatycznego dachu';document.getElementById('carport-preview').textContent='Odczytano: '+parsedCarport.width/1000+' x '+parsedCarport.length/1000+' m · '+parsedCarport.posts+' słupów · '+roofName+(parsedCarport.roof!=='none'?' '+parsedCarport.angle+'°':'')+'.';document.getElementById('generate-carport').disabled=false;}
 catch(e){parsedCarport=null;document.getElementById('generate-carport').disabled=true;document.getElementById('carport-preview').textContent=e.message;}
});


document.getElementById('generate-carport').addEventListener('click',()=>{
 try{
  if(!parsedCarport)throw new Error('Najpierw odczytaj opis.');
  const h=Number(document.getElementById('carport-height').value);
  if(!Number.isFinite(h)||h<1800||h>6000)throw new Error('Wysokość: 1800–6000 mm.');
  const {width:w,length:l,posts:n}=parsedCarport;
  if(group.children.length+n+4>500)throw new Error('Za dużo elementów w projekcie.');
  group.updateMatrixWorld(true);const origin=group.worldToLocal(controls.target.clone());const start=group.children.length;
  carportPostPositions(w,l,n).forEach((p,k)=>addCarportMember(0,[h,200,200],origin.clone().add(new THREE.Vector3(p[0],p[1],h/2)),'Słup wiaty '+(k+1)));
  addCarportMember(1,[w+200,140,200],origin.clone().add(new THREE.Vector3(0,-l/2,h+100)),'Belka wiaty przód');
  addCarportMember(1,[w+200,140,200],origin.clone().add(new THREE.Vector3(0,l/2,h+100)),'Belka wiaty tył');
  const a=addCarportMember(1,[l+200,140,200],origin.clone().add(new THREE.Vector3(-w/2,0,h+100)),'Belka wiaty lewa');
  const b=addCarportMember(1,[l+200,140,200],origin.clone().add(new THREE.Vector3(w/2,0,h+100)),'Belka wiaty prawa');
  group.children[a].rotation.z=Math.PI/2;group.children[b].rotation.z=Math.PI/2;
  selectPart(start);fitAll();
  document.getElementById('part-status').textContent='Wygenerowano wiatę '+w/1000+' x '+l/1000+' m: '+n+' słupów i 4 belki. Wszystkie elementy można edytować.';
 }catch(e){document.getElementById('part-status').textContent=e.message;}
});

catalog.forEach((spec,type)=>{
 const card=document.createElement('button');card.type='button';card.className='part-card';card.draggable=true;
 card.innerHTML=timberIcon(catalogPart(type));
 const caption=document.createElement('span');caption.textContent=spec.label;card.appendChild(caption);
 const detail=document.createElement('small');detail.textContent=spec.length+' / '+spec.width+' × '+spec.height+' mm';card.appendChild(detail);
 card.addEventListener('click',()=>addCatalogPart(type));
 card.addEventListener('dragstart',event=>{event.dataTransfer.setData('application/x-timber',String(type));event.dataTransfer.effectAllowed='copy';});
 document.getElementById('catalog').appendChild(card);
});
function syncInputs(){
 const totals=[['Słup','Słupy'],['Belka','Belki'],['Miecz','Miecze'],['Krokiew','Krokwie'],['Płatew','Płatwie']];
 document.getElementById('model-counts').textContent=totals.map(([prefix,name])=>name+': '+labels.filter(label=>label.startsWith(prefix)).length).join(' · ');
 for(const axis of ['x','y','z']){
  const input=document.getElementById('move-'+axis);
  input.disabled=!selected;
  input.value=selected?String(Math.round(selected.position[axis]-selected.userData.home[axis])):'0';
 }
 for(const id of ['reset-part','hide-part','download-part'])document.getElementById(id).disabled=!selected;
 partCards.forEach((card,i)=>{
  card.setAttribute('aria-pressed',String(group.children[i]===selected||i===jointA||i===jointB));
  card.style.opacity=group.children[i].visible?'1':'.45';
 });
 const beamOffset=beam.position.z-beam.userData.home.z;
 separation.value=String(Math.max(0,Math.min(500,beamOffset)));
 document.getElementById('distance').textContent=String(Math.round(beamOffset));
}
function refreshSelection(){
 group.children.forEach((part,i)=>part.traverse(o=>{
  if(o.isMesh)o.material.emissive.setHex(i===jointA?0x123b70:i===jointB?0x12552b:selectedIndices.has(i)?0x302010:0x000000);
 }));
 partCards.forEach((card,i)=>{
  card.setAttribute('aria-pressed',String(selectedIndices.has(i)));
  card.style.borderColor=i===jointA?'#176bb0':i===jointB?'#218944':selectedIndices.has(i)?'#b7793f':'';
  card.title=(i===jointA?'Element A · ':i===jointB?'Element B · ':selectedIndices.has(i)?'Zaznaczony · ':'')+labels[i];
 });
}
function choose(index){
 selected=index>=0?group.children[index]:null;
 select.value=String(index);
 if(selected)selected.visible=true;
 updateArrows();syncInputs();refreshSelection();
}
select.addEventListener('change',()=>selectPart(Number(select.value)));
transform.addEventListener('objectChange',syncInputs);
for(const axis of ['x','y','z'])document.getElementById('move-'+axis).addEventListener('change',event=>{
 const value=Number(event.target.value);
 if(selected&&Number.isFinite(value)){selected.position[axis]=selected.userData.home[axis]+value;syncInputs();}
});
document.getElementById('reset-part').addEventListener('click',()=>{if(selected){selected.position.copy(selected.userData.home);selected.visible=true;syncInputs();}});
document.getElementById('hide-part').addEventListener('click',()=>{if(selected){selected.visible=false;selectPart(-1);}});
document.getElementById('reset-all').addEventListener('click',()=>{
 group.children.forEach(part=>{part.position.copy(part.userData.home);part.visible=true;});selectPart(-1);syncInputs();
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
canvas.addEventListener('dragover',event=>{
 if(Array.from(event.dataTransfer.types).includes('application/x-timber')){event.preventDefault();event.dataTransfer.dropEffect='copy';}
});
canvas.addEventListener('drop',event=>{
 const data=event.dataTransfer.getData('application/x-timber');
 if(data==='')return;
 const type=Number(data);if(!Number.isInteger(type)||!catalog[type])return;
 event.preventDefault();addCatalogPart(type,event);
});
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
 const additive=event.shiftKey||event.ctrlKey||event.metaKey;
 if(!additive&&!document.getElementById('pair-mode').checked&&showArrows.checked&&transform.axis!==null)return;
 pointerStart={id:event.pointerId,x:event.clientX,y:event.clientY};
 pointerRay(event);
 const hit=raycaster.intersectObjects(group.children.filter(part=>part.visible),true)[0];
 if(!hit)return;
 let part=hit.object;while(part.parent!==group)part=part.parent;
 const index=group.children.indexOf(part);
 if(additive||document.getElementById('pair-mode').checked){
  pointerStart=null;selectPart(index,true);
  event.preventDefault();event.stopImmediatePropagation();return;
 }
 selectPart(index);
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
  if(event.type==='pointerup'&&clicked&&!transform.dragging)selectPart(-1);
 }
}
canvas.addEventListener('pointerup',finishPointer,true);
canvas.addEventListener('pointercancel',finishPointer,true);
canvas.addEventListener('lostpointercapture',finishPointer,true);
syncInputs();
if(restoredProject){
 try{
  loadProject(restoredProject.state);
  if(restoredProject.indices){[jointA,jointB]=restoredProject.indices;choose(jointA);syncPair();}
  if(restoredProject.camera){camera.position.fromArray(restoredProject.camera.position);controls.target.fromArray(restoredProject.camera.target);controls.update();}
  document.getElementById('part-status').textContent=restoredProject.message;
 }catch(error){document.getElementById('part-status').textContent=error.message;}
}

function resize(){const w=host.clientWidth;camera.aspect=w/760;camera.updateProjectionMatrix();renderer.setSize(w,760,false);}
new ResizeObserver(resize).observe(host);
function animate(){if(controls.enabled)controls.update();updateDimension();renderer.render(scene,camera);requestAnimationFrame(animate);}
animate();
</script>
""".replace("__OBJS__", obj_json).replace("__LABELS__", json.dumps(labels, ensure_ascii=False)).replace("__RESTORE__", json.dumps(st.session_state.get("joint_response"))).replace("__JOINTS__", json.dumps(joint_catalog, ensure_ascii=False)).replace("__EXAMPLES__", json.dumps(joint_examples)).replace("__MODEL__", json.dumps({"beam_flat": beam_flat, "full_frame": full_frame, "skeleton": skeleton}))

editor_component = components.declare_component("kumiki_editor", path=str(app_dir / "frontend"))
request = editor_component(html=html, key="kumiki_editor", default=None)
if isinstance(request, dict) and request.get("id") != st.session_state.get("handled_joint_request"):
    st.session_state["handled_joint_request"] = request.get("id")
    try:
        sys.path.insert(0, str(app_dir))
        try:
            from wykonaj_polaczenie import execute_request
        finally:
            sys.path.pop(0)
        response = execute_request(request)
    except Exception as exc:
        response = {"state": request.get("state"), "indices": request.get("indices"),
                    "camera": request.get("camera"), "message": "Połączenie nie zostało wykonane: " + str(exc)}
    st.session_state["joint_response"] = response
    st.rerun()
st.info("Katalog dodaje pełne elementy bez wycięć. Zapisz projekt do JSON, aby zachować dodane części i ich położenie. Po odświeżeniu możesz go wczytać przy tych samych ustawieniach modelu. Przesuwanie i ukrywanie służy do oglądania połączeń. Pobieranie OBJ uwzględnia przesunięcie wybranego elementu. Odświeżenie widoku przywraca bazowy model; zapisany układ można wczytać z pliku JSON.")

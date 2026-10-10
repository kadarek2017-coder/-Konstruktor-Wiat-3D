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
st.caption("Wersja podglądu 8 — graficzny katalog, dodawanie i przeciąganie elementów")

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
  <b>Kumiki — rama i połączenia · wersja 8</b><br>
  Wybierz kafelek lub chwyć element w widoku i przeciągnij.<br>
  Przeciąganie tła: obrót widoku · rolka: zoom · prawy: przesuwanie widoku
 </div>
 <aside id="parts-panel" aria-label="Graficzny wybór elementów">
  <details open><summary>Katalog — dodaj element</summary>
   <p style="margin:4px 0">Przeciągnij kafelek do widoku 3D albo kliknij, aby dodać.</p>
   <div id="catalog-size">
    <label>Długość <input id="part-length" type="number" min="50" max="20000" step="50" value="3000"> mm</label>
    <label>Szerokość <input id="part-width" type="number" min="10" max="1000" step="10" value="100"> mm</label>
    <label>Wysokość <input id="part-height" type="number" min="10" max="1000" step="10" value="200"> mm</label>
   </div>
   <label><input id="custom-size" type="checkbox"> Użyj powyższych wymiarów</label>
   <div id="catalog" class="part-grid" style="margin-top:8px"></div>
   <small>Nowe części mają pełny przekrój. Wycięcia połączeń nie są przeliczane przy przesuwaniu.</small>
  </details>
  <details open><summary>Elementy w modelu</summary><div id="model-parts" class="part-grid"></div></details>
  <div id="part-status" role="status" aria-live="polite" style="margin-top:8px"></div>
 </aside>
 <div style="position:absolute;left:14px;right:14px;bottom:14px;background:rgba(255,255,255,.93);padding:12px;border-radius:9px;font:14px -apple-system,BlinkMacSystemFont,sans-serif">
  <label for="separation">Uniesienie belek: <output id="distance">0</output> mm</label>
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
const partCards=[];
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
 card.addEventListener('click',()=>choose(index));
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
function catalogPart(type){
 const spec=catalog[type];const custom=document.getElementById('custom-size').checked;
 const dims=['length','width','height'].map(key=>custom?Number(document.getElementById('part-'+key).value):spec[key]);
 if(dims.some((n,i)=>!Number.isFinite(n)||n<(i===0?50:10)||n>(i===0?20000:1000)))throw new Error('Sprawdź wymiary: długość 50–20000 mm, przekrój 10–1000 mm.');
 const [length,width,height]=dims;
 const geometry=new THREE.BoxGeometry(...(spec.axis==='z'?[width,height,length]:[length,width,height]));
 geometry.rotateY(spec.angle*Math.PI/180);
 const part=new THREE.Group();part.add(new THREE.Mesh(geometry,mats[spec.axis==='z'?0:1].clone()));
 return part;
}
function addCatalogPart(type,event=null){
 try{
  const part=catalogPart(type);
  let position=controls.target.clone();
  if(event){
   pointerRay(event);
   const plane=new THREE.Plane().setFromNormalAndCoplanarPoint(camera.getWorldDirection(new THREE.Vector3()),position);
   const hit=raycaster.ray.intersectPlane(plane,new THREE.Vector3());if(hit)position=hit;
  }
  group.updateMatrixWorld(true);part.position.copy(group.worldToLocal(position));
  part.userData.home=part.position.clone();part.userData.added=true;
  part.traverse(o=>{if(o.isMesh){o.castShadow=true;o.receiveShadow=true;}});
  group.add(part);
  const index=group.children.length-1;labels.push(catalog[type].label+' '+(index+1));
  if(catalog[type].label.startsWith('Belka'))beams.push(part);
  registerPart(index);choose(index);
  document.getElementById('part-status').textContent='Dodano: '+labels[index]+'. Chwyć element w widoku i przeciągnij.';
 }catch(error){document.getElementById('part-status').textContent=error.message;}
}
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
 for(const axis of ['x','y','z']){
  const input=document.getElementById('move-'+axis);
  input.disabled=!selected;
  input.value=selected?String(Math.round(selected.position[axis]-selected.userData.home[axis])):'0';
 }
 for(const id of ['reset-part','hide-part','download-part'])document.getElementById(id).disabled=!selected;
 partCards.forEach((card,i)=>{
  card.setAttribute('aria-pressed',String(group.children[i]===selected));
  card.style.opacity=group.children[i].visible?'1':'.45';
 });
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
st.info("Katalog dodaje pełne elementy bez wycięć. Dodane części i ich położenie są tymczasowe — odświeżenie widoku je usuwa. Przesuwanie i ukrywanie służy do oglądania połączeń. Pobieranie OBJ uwzględnia przesunięcie wybranego elementu. Odświeżenie widoku przywraca złożoną ramę.")

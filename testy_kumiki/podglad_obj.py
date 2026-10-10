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
st.caption("Wersja podglądu 4 — belka na sztorc lub płasko, rozsuwanie połączenia")

app_dir = Path(__file__).resolve().parent
base = app_dir / "wyniki"
try:
    saved_flat = bool(json.loads((base / "wymiary.json").read_text(encoding="utf-8")).get("beam_flat", False))
except (OSError, ValueError):
    saved_flat = False


def request_generation():
    st.session_state["regenerate_model"] = True


beam_flat = st.checkbox(
    "Połóż belkę płasko — szerokość 200 mm, wysokość 100 mm",
    value=saved_flat, key="beam_flat", on_change=request_generation,
)
width, height = (200, 100) if beam_flat else (100, 200)
st.caption(f"Słup 200×200 mm · belka: szerokość {width} mm, wysokość {height} mm. Zmiana ustawienia przelicza czop i gniazdo.")
clicked_generate = st.button("Wygeneruj poprawiony model", type="primary")
regenerate_requested = st.session_state.pop("regenerate_model", False)
if clicked_generate or regenerate_requested:
    with st.spinner("Generowanie i sprawdzanie czopa oraz gniazda…"):
        try:
            result = subprocess.run(
                [sys.executable, str(app_dir / "generuj_czop.py")] + (["--flat"] if beam_flat else []),
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
paths = [base / "SLUP_200x200.obj", base / "BELKA_100x200.obj"]
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
    generuj_czop.validate_meshes(meshes, beam_flat=beam_flat)
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
  <b>Kumiki — czop i gniazdo · wersja 4</b><br>
  Lewy przycisk: obrót · rolka: zoom · prawy: przesuwanie
 </div>
 <div style="position:absolute;left:14px;right:14px;bottom:14px;background:rgba(255,255,255,.93);padding:12px;border-radius:9px;font:14px -apple-system,BlinkMacSystemFont,sans-serif">
  <label for="separation">Uniesienie belki: <output id="distance">0</output> mm</label>
  <input id="separation" type="range" min="0" max="500" step="5" value="0" style="width:100%;display:block;margin:8px 0">
  <button id="assemble" type="button">Złóż połączenie</button>
  <button id="separate" type="button">Rozsuń elementy</button>
 </div>
</div>
<script type="importmap">{"imports":{"three":"https://cdn.jsdelivr.net/npm/three@0.180.0/build/three.module.js"}}</script>
<script type="module">
import * as THREE from 'three';
import { OrbitControls } from 'https://cdn.jsdelivr.net/npm/three@0.180.0/examples/jsm/controls/OrbitControls.js';
import { OBJLoader } from 'https://cdn.jsdelivr.net/npm/three@0.180.0/examples/jsm/loaders/OBJLoader.js';

const objTexts = __OBJS__;
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
 obj.traverse(o=>{
   if(o.isMesh){o.material=mats[i];o.castShadow=true;o.receiveShadow=true;}
 });
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
function setSeparation(value){
 separation.value=String(value);
 group.children[1].position.z=value;
 document.getElementById('distance').textContent=String(value);
}
separation.addEventListener('input',()=>setSeparation(Number(separation.value)));
document.getElementById('assemble').addEventListener('click',()=>setSeparation(0));
document.getElementById('separate').addEventListener('click',()=>setSeparation(350));

function resize(){const w=host.clientWidth;camera.aspect=w/760;camera.updateProjectionMatrix();renderer.setSize(w,760,false);}
new ResizeObserver(resize).observe(host);
function animate(){controls.update();renderer.render(scene,camera);requestAnimationFrame(animate);}
animate();
</script>
""".replace("__OBJS__", obj_json)

components.html(html,height=780,scrolling=False)
st.success("Wczytano oba pliki OBJ. Sprawdź, czy czop i gniazdo są widoczne oraz czy belka i słup są ustawione prawidłowo.")
st.info("To jest ekran testowy. Nie zmienia jeszcze głównego modelu wiaty.")

import json, math
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
import plotly.graph_objects as go

VERSION = "1.2"
st.set_page_config(page_title=f"Konstruktor Wiat 3D v{VERSION}", page_icon="🏗️", layout="wide", initial_sidebar_state="collapsed")
st.title(f"Konstruktor Wiat 3D v{VERSION}")
st.caption("Parametryczny model drewnianej wiaty + ręczna biblioteka elementów 3D")

ELEMENT_LIBRARY={"Słup":{"a":.20,"b":.20,"length":3.0,"dir":"Z"},"Belka":{"a":.10,"b":.20,"length":3.0,"dir":"X"},"Krokiew":{"a":.08,"b":.18,"length":4.0,"dir":"X"},"Płatew":{"a":.10,"b":.20,"length":3.0,"dir":"Y"},"Łata":{"a":.04,"b":.06,"length":3.0,"dir":"X"},"Zastrzał":{"a":.08,"b":.08,"length":.8,"dir":"X"},"Blacha dachowa":{"a":1.10,"b":.005,"length":3.0,"dir":"Y"},"Stopa / kotwa":{"a":.20,"b":.20,"length":.20,"dir":"Z"}}
WOOD_COLORS={"Świerk":"#B98A58","Sosna":"#C49A67","Modrzew":"#A96F43","Dąb":"#8B603B","KVH":"#BE9360","BSH":"#AD7D4E"}
FINISH_COLORS={"Surowe":None,"Olej naturalny":"#9D7046","Impregnat jasny":"#A98055","Impregnat ciemny":"#65462F","Biały":"#DED9CE","Grafit":"#55575A"}
if "custom_elements" not in st.session_state: st.session_state.custom_elements=[]
if "style_overrides" not in st.session_state: st.session_state.style_overrides={}

with st.sidebar:
    st.header("Wymiary")
    W=st.number_input("Szerokość [m]",2.0,15.0,7.0,.1)
    L=st.number_input("Długość [m]",2.0,15.0,6.0,.1)
    roof_type=st.selectbox("Rodzaj dachu",["Jednospadowy","Dwuspadowy","Płaski"])
    Hf=st.number_input("Wysokość okapu/bazowa [m]",2.0,5.0,3.20,.05)
    if roof_type=="Jednospadowy":
        Hb=st.number_input("Wysokość drugiej krawędzi [m]",2.0,5.0,2.70,.05)
        ridge_h=Hf
    elif roof_type=="Dwuspadowy":
        Hb=Hf
        ridge_h=st.number_input("Wysokość kalenicy [m]",Hf,6.0,max(Hf,3.80),.05)
    else:
        Hb=Hf
        ridge_h=Hf
    nside=st.slider("Słupy na jednym boku (tryb automatyczny)",2,6,4)
    post_mode=st.radio("Rozmieszczenie słupów",["Automatyczne","Ręczne"],horizontal=True)
    rafter_direction=st.radio("Kierunek krokwi",["W poprzek (X)","Wzdłuż (Y)"],horizontal=False)
    st.header("Przekroje")
    pc=st.number_input("Słup [cm]",8,30,20,1)/100
    bw=st.number_input("Belka — szerokość [cm]",5,30,10,1)/100
    bh=st.number_input("Belka — wysokość [cm]",10,40,20,1)/100
    rw=st.number_input("Krokiew — szerokość [cm]",4,20,8,1)/100
    rh=st.number_input("Krokiew — wysokość [cm]",8,30,18,1)/100
    spacing=st.number_input("Rozstaw krokwi [m]",.30,1.50,.70,.05)
    overhang=st.number_input("Okap krokwi [m]",0.0,1.0,.25,.05)
    st.header("Konstrukcja")
    braces=st.checkbox("Zastrzały",True)
    brace_len=st.number_input("Długość zastrzału [m]",0.40,1.50,.80,.05)
    show_ground=st.checkbox("Pokaż podłoże",True)
    wood_detail=st.checkbox("Naturalne usłojenie drewna",True)
    st.header("Wygląd konstrukcji")
    base_wood=st.selectbox("Drewno konstrukcji",list(WOOD_COLORS.keys()),index=0)
    base_finish=st.selectbox("Wykończenie konstrukcji",list(FINISH_COLORS.keys()),index=0)
    base_wood_color=FINISH_COLORS.get(base_finish) or WOOD_COLORS[base_wood]
    st.caption("Domyślny wygląd całej konstrukcji. Wybrane elementy można nadpisać niżej.")

# Edycja wyglądu pojedynczych elementów i grup
with st.expander("🎨 Kolorowanie elementów / grup", expanded=False):
    style_scope=st.radio("Zakres",["Grupa elementów","Pojedynczy element"],horizontal=True)
    group_options=["Słupy","Belki","Krokwie","Zastrzały"]
    if style_scope=="Grupa elementów":
        style_target=st.selectbox("Wybierz grupę",group_options)
        style_key=f"group:{style_target}"
    else:
        single_options=[f"S{i}" for i in range(1,len(posts)+1)] if "posts" in locals() else []
        single_options += [f"K{i}" for i in range(1,30)]
        single_options += [f"R{el['id']} — {el['type']}" for el in st.session_state.custom_elements]
        style_target=st.selectbox("Wybierz element",single_options or ["Brak elementów"])
        style_key=f"single:{style_target.split(' — ')[0]}"
    sc1,sc2=st.columns(2)
    with sc1: style_wood=st.selectbox("Drewno",list(WOOD_COLORS.keys()),key="stylewood")
    with sc2: style_finish=st.selectbox("Wykończenie",list(FINISH_COLORS.keys()),key="stylefinish")
    if st.button("Zastosuj wygląd"):
        st.session_state.style_overrides[style_key]={"wood":style_wood,"finish":style_finish}
        st.rerun()
    if st.button("Przywróć wygląd domyślny"):
        st.session_state.style_overrides.pop(style_key,None)
        st.rerun()

def style_color(group, element_id=None):
    data=None
    if element_id:
        data=st.session_state.style_overrides.get(f"single:{element_id}")
    if data is None:
        data=st.session_state.style_overrides.get(f"group:{group}")
    if data is None:
        return base_wood_color
    return FINISH_COLORS.get(data["finish"]) or WOOD_COLORS.get(data["wood"],base_wood_color)

# Edytowalna lista słupów
auto_ys=[i*L/(nside-1) for i in range(nside)]
auto_posts=[{"X [m]":x,"Y [m]":y} for x in (0.0,W) for y in auto_ys]
if "manual_posts" not in st.session_state:
    st.session_state.manual_posts=auto_posts

if post_mode=="Ręczne":
    st.subheader("Rozmieszczenie słupów")
    st.caption("Dodawaj i usuwaj wiersze. X = pozycja po szerokości, Y = pozycja po długości.")
    edited=st.data_editor(
        pd.DataFrame(st.session_state.manual_posts),
        num_rows="dynamic", use_container_width=True,
        column_config={
            "X [m]":st.column_config.NumberColumn(min_value=0.0,max_value=float(W),step=0.1),
            "Y [m]":st.column_config.NumberColumn(min_value=0.0,max_value=float(L),step=0.1),
        },
        key="posts_editor"
    )
    posts=[{"X [m]":float(r["X [m]"]),"Y [m]":float(r["Y [m]"])}
           for _,r in edited.dropna().iterrows()]
    st.session_state.manual_posts=posts
else:
    posts=auto_posts

st.subheader("🧰 Biblioteka elementów")
element_type=st.selectbox("Element do dodania",list(ELEMENT_LIBRARY.keys()))
preset=ELEMENT_LIBRARY[element_type]
p1,p2,p3=st.columns(3)
with p1: ex=st.number_input("X elementu [m]",0.0,float(W),0.0,.1)
with p2: ey=st.number_input("Y elementu [m]",0.0,float(L),0.0,.1)
with p3: ez=st.number_input("Z elementu [m]",0.0,8.0,0.0,.1)
q1,q2,q3,q4=st.columns(4)
with q1: direction=st.selectbox("Kierunek",["X","Y","Z"],index=["X","Y","Z"].index(preset["dir"]))
with q2: ea=st.number_input("A [m]",.005,2.0,float(preset["a"]),.01,key="ea")
with q3: eb=st.number_input("B [m]",.005,2.0,float(preset["b"]),.01,key="eb")
with q4: elen=st.number_input("Długość [m]",.05,15.0,float(preset["length"]),.05,key="elen")
is_wood=element_type in ["Słup","Belka","Krokiew","Płatew","Łata","Zastrzał"]
m1,m2=st.columns(2)
if is_wood:
    with m1: material=st.selectbox("Rodzaj drewna",list(WOOD_COLORS.keys()))
    with m2: finish=st.selectbox("Wykończenie",list(FINISH_COLORS.keys()))
else:
    material="Stal/blacha" if element_type in ["Blacha dachowa","Stopa / kotwa"] else "Inny"
    finish="Fabryczne"
if st.button("➕ Dodaj element do konstrukcji"):
    st.session_state.custom_elements.append({"id":len(st.session_state.custom_elements)+1,"type":element_type,"x":ex,"y":ey,"z":ez,"a":ea,"b":eb,"length":elen,"direction":direction,"material":material,"finish":finish})
    st.rerun()
if st.session_state.custom_elements:
    edited_custom=st.data_editor(pd.DataFrame(st.session_state.custom_elements),use_container_width=True,hide_index=True,
        disabled=["id","type","material","finish"],key="custom_editor")
    if st.button("💾 Zastosuj zmiany elementów"):
        st.session_state.custom_elements=edited_custom.to_dict("records")
        st.rerun()
    if st.button("🗑️ Usuń ostatni element"):
        st.session_state.custom_elements.pop(); st.rerun()

fig=go.Figure()

def box(x0,x1,y0,y1,z0,z1,name,opacity=1.0,color=None):
    x=[x0,x1,x1,x0,x0,x1,x1,x0]
    y=[y0,y0,y1,y1,y0,y0,y1,y1]
    z=[z0,z0,z0,z0,z1,z1,z1,z1]
    fig.add_trace(go.Mesh3d(
        x=x,y=y,z=z,
        i=[0,0,0,1,1,2,4,4,4,5,5,6],
        j=[1,2,4,2,5,3,5,6,0,6,1,7],
        k=[2,3,5,5,6,7,6,7,7,7,2,3],
        flatshading=False, opacity=opacity, name=name, color=color,
        lighting=dict(ambient=.72,diffuse=.72,specular=.08,roughness=.92,fresnel=.03),
        lightposition=dict(x=120,y=-180,z=220),
        hovertemplate=f"{name}<extra></extra>", showscale=False
    ))
    if wood_detail and opacity >= .99 and color not in ("#8B9198","#8A8A82"):
        # delikatne linie włókien na dwóch widocznych płaszczyznach — efekt drewna bez jaskrawych tekstur
        dx=x1-x0; dy=y1-y0; dz=z1-z0
        grain="#6F4E32"
        if dz >= max(dx,dy):
            for t in (.28,.55,.78):
                xx=x0+dx*t
                fig.add_trace(go.Scatter3d(x=[xx,xx],y=[y0,y0],z=[z0+.05*dz,z1-.05*dz],
                    mode="lines",line=dict(width=1,color=grain),opacity=.22,hoverinfo="skip",showlegend=False))
        elif dx >= dy:
            for t in (.30,.62):
                zz=z0+dz*t
                fig.add_trace(go.Scatter3d(x=[x0+.04*dx,x1-.04*dx],y=[y0,y0],z=[zz,zz],
                    mode="lines",line=dict(width=1,color=grain),opacity=.20,hoverinfo="skip",showlegend=False))
        else:
            for t in (.30,.62):
                zz=z0+dz*t
                fig.add_trace(go.Scatter3d(x=[x0,x0],y=[y0+.04*dy,y1-.04*dy],z=[zz,zz],
                    mode="lines",line=dict(width=1,color=grain),opacity=.20,hoverinfo="skip",showlegend=False))

def roof_h(y, x=None):
    if roof_type=="Jednospadowy":
        return Hf+(Hb-Hf)*(y/L)
    if roof_type=="Płaski":
        return Hf
    if x is None:
        return Hf
    half=W/2
    return Hf+(ridge_h-Hf)*(1-abs(x-half)/half)

# słupy
for j,p in enumerate(posts,1):
    x=max(0.0,min(W,p["X [m]"]))
    y=max(0.0,min(L,p["Y [m]"]))
    h=roof_h(y,x)-bh
    box(x-pc/2,x+pc/2,y-pc/2,y+pc/2,0,h,f"S{j}",color=style_color("Słupy",f"S{j}"))

# belki podłużne, podążające za spadkiem — dzielone na segmenty dla poprawnej geometrii
segments=max(12,int(L/.25))
for x in (0,W):
    for s in range(segments):
        y0=L*s/segments; y1=L*(s+1)/segments
        z0=roof_h((y0+y1)/2)-bh
        box(x-bw/2,x+bw/2,y0,y1,z0,z0+bh,"Belka podłużna",color=style_color("Belki"))

# belki czołowa i tylna
for y,h in ((0,Hf),(L,Hb)):
    box(-pc/2,W+pc/2,y-bw/2,y+bw/2,h-bh,h,"Belka poprzeczna",color=style_color("Belki"))

# krokwie — kierunek wybierany przez użytkownika
if rafter_direction=="W poprzek (X)":
    rn=max(2,math.ceil(L/spacing)+1)
    positions=[i*L/(rn-1) for i in range(rn)]
    for i,y in enumerate(positions,1):
        if roof_type=="Dwuspadowy":
            segs=max(12,int(W/.25))
            for s in range(segs):
                x0=-overhang+(W+2*overhang)*s/segs
                x1=-overhang+(W+2*overhang)*(s+1)/segs
                xm=max(0,min(W,(x0+x1)/2))
                h=roof_h(y,xm)
                box(x0,x1,y-rw/2,y+rw/2,h,h+rh,f"K{i}",color=style_color("Krokwie",f"K{i}"))
        else:
            h=roof_h(y)
            box(-overhang,W+overhang,y-rw/2,y+rw/2,h,h+rh,f"K{i}",color=style_color("Krokwie",f"K{i}"))
    rafter_len=W+2*overhang
else:
    rn=max(2,math.ceil(W/spacing)+1)
    positions=[i*W/(rn-1) for i in range(rn)]
    for i,x in enumerate(positions,1):
        segs=max(12,int(L/.25))
        for s in range(segs):
            y0=-overhang+(L+2*overhang)*s/segs
            y1=-overhang+(L+2*overhang)*(s+1)/segs
            ym=max(0,min(L,(y0+y1)/2))
            h=roof_h(ym,x)
            box(x-rw/2,x+rw/2,y0,y1,h,h+rh,f"K{i}",color=style_color("Krokwie",f"K{i}"))
    rafter_len=L+2*overhang

# zastrzały — wizualizowane jako grube elementy ukośne
if braces:
    def member(x1,y1,z1,x2,y2,z2,name,width=9):
        fig.add_trace(go.Scatter3d(
            x=[x1,x2],y=[y1,y2],z=[z1,z2],mode="lines",
            line=dict(width=width,color=style_color("Zastrzały")),name=name,
            hovertemplate=f"{name}<extra></extra>",showlegend=False
        ))
    b=min(brace_len,L/3)
    # zastrzały wzdłuż obu boków przy przednich i tylnych słupach
    for x in (0,W):
        member(x,0,roof_h(0)-bh-b,x,b,roof_h(b)-bh,"Zastrzał")
        member(x,L,roof_h(L)-bh-b,x,L-b,roof_h(L-b)-bh,"Zastrzał")
    # zastrzały czołowe
    bx=min(brace_len,W/3)
    member(0,0,Hf-bh-bx,bx,0,Hf-bh,"Zastrzał")
    member(W,0,Hf-bh-bx,W-bx,0,Hf-bh,"Zastrzał")

# elementy ręczne z biblioteki
for el in st.session_state.custom_elements:
    x,y,z,a,b,ln=el["x"],el["y"],el["z"],el["a"],el["b"],el["length"]
    mat=el.get("material","Świerk")
    fin=el.get("finish","Surowe")
    if el["type"] in ["Blacha dachowa","Stopa / kotwa"]:
        elcolor="#8B9198"
    else:
        override=st.session_state.style_overrides.get(f'single:R{el["id"]}')
        if override:
            mat=override["wood"]; fin=override["finish"]
        elcolor=FINISH_COLORS.get(fin) or WOOD_COLORS.get(mat,"#C9A66B")
    if el["direction"]=="X": box(x,x+ln,y-a/2,y+a/2,z,z+b,f'{el["type"]} R{el["id"]} — {mat}',color=elcolor)
    elif el["direction"]=="Y": box(x-a/2,x+a/2,y,y+ln,z,z+b,f'{el["type"]} R{el["id"]} — {mat}',color=elcolor)
    else: box(x-a/2,x+a/2,y-b/2,y+b/2,z,z+ln,f'{el["type"]} R{el["id"]} — {mat}',color=elcolor)

# podłoże
if show_ground:
    box(-.35,W+.35,-.35,L+.35,-.035,0,"Podłoże",.10,color="#8A8A82")

fig.update_layout(
    height=900, margin=dict(l=0,r=0,t=5,b=0),
    scene=dict(
        bgcolor="#F3F0E9",
        xaxis=dict(title="Szerokość [m]",backgroundcolor="#F3F0E9",gridcolor="#D8D2C7",showbackground=True),
        yaxis=dict(title="Długość [m]",backgroundcolor="#F3F0E9",gridcolor="#D8D2C7",showbackground=True),
        zaxis=dict(title="Wysokość [m]",backgroundcolor="#F3F0E9",gridcolor="#D8D2C7",showbackground=True),
        aspectmode="data",camera=dict(eye=dict(x=1.45,y=-1.65,z=1.05))
    ),
    showlegend=False
)

# Nowy renderer Three.js — pełne, nieprzezroczyste bryły z oświetleniem i cieniami
three_data={"W":W,"L":L,"Hf":Hf,"Hb":Hb,"bh":bh,"bw":bw,"pc":pc,"rw":rw,"rh":rh,
            "posts":posts,"rafters":positions,"rafter_direction":rafter_direction,
            "roof_type":roof_type,"ridge_h":ridge_h,"overhang":overhang,"wood":base_wood_color,"braces":braces,"brace_len":brace_len}
three_json=json.dumps(three_data,ensure_ascii=False)
three_html=f"""
<div id="three-view" style="width:100%;height:760px;border-radius:12px;overflow:hidden;background:#e8e4dc"></div>
<script type="importmap">{{"imports":{{"three":"https://cdn.jsdelivr.net/npm/three@0.180.0/build/three.module.js"}}}}</script>
<script type="module">
import * as THREE from 'three';
import {{ OrbitControls }} from 'https://cdn.jsdelivr.net/npm/three@0.180.0/examples/jsm/controls/OrbitControls.js';
const d={three_json};
const host=document.getElementById('three-view');
const scene=new THREE.Scene(); scene.background=new THREE.Color(0xe8e4dc);
const camera=new THREE.PerspectiveCamera(42,host.clientWidth/760,.05,100);
camera.position.set(d.W*1.15,-d.L*1.35,Math.max(d.Hf,d.Hb)+4);
const renderer=new THREE.WebGLRenderer({{antialias:true,alpha:false}});
renderer.setPixelRatio(Math.min(window.devicePixelRatio,2)); renderer.setSize(host.clientWidth,760);
renderer.shadowMap.enabled=true; renderer.shadowMap.type=THREE.PCFSoftShadowMap;
renderer.outputColorSpace=THREE.SRGBColorSpace; renderer.toneMapping=THREE.ACESFilmicToneMapping; renderer.toneMappingExposure=1.05;
host.appendChild(renderer.domElement);
const controls=new OrbitControls(camera,renderer.domElement); controls.enableDamping=true;
controls.target.set(d.W/2,d.L/2,Math.min(d.Hf,d.Hb)/2);
scene.add(new THREE.HemisphereLight(0xfff7e8,0x8b8174,2.2));
const sun=new THREE.DirectionalLight(0xfff2d6,3.2); sun.position.set(-5,-7,10); sun.castShadow=true;
sun.shadow.mapSize.set(2048,2048); scene.add(sun);
const wood=new THREE.MeshStandardMaterial({{color:d.wood,roughness:.78,metalness:0}});
const groundMat=new THREE.MeshStandardMaterial({{color:0xb9b5aa,roughness:1}});
function addBox(cx,cy,cz,sx,sy,sz,mat=wood){{
 const g=new THREE.BoxGeometry(Math.max(sx,.01),Math.max(sy,.01),Math.max(sz,.01));
 const m=new THREE.Mesh(g,mat); m.position.set(cx,cy,cz); m.castShadow=true; m.receiveShadow=true; scene.add(m); return m;
}}
function roofH(y,x){{
 if(d.roof_type==='Jednospadowy') return d.Hf+(d.Hb-d.Hf)*(y/d.L);
 if(d.roof_type==='Płaski') return d.Hf;
 const half=d.W/2; return d.Hf+(d.ridge_h-d.Hf)*(1-Math.abs(x-half)/half);
}}
// Jedna belka = jedna ciągła bryła. BoxGeometry jest orientowane wzdłuż wektora p1->p2.
function addMember(p1,p2,width,height,mat=wood){{
 const a=new THREE.Vector3(...p1), b=new THREE.Vector3(...p2);
 const dir=new THREE.Vector3().subVectors(b,a); const len=dir.length();
 if(len<0.0001) return null;
 const mesh=new THREE.Mesh(new THREE.BoxGeometry(width,len,height),mat);
 mesh.position.copy(a).add(b).multiplyScalar(.5);
 // lokalna oś Y bryły zostaje skierowana dokładnie wzdłuż elementu
 mesh.quaternion.setFromUnitVectors(new THREE.Vector3(0,1,0),dir.clone().normalize());
 mesh.castShadow=true; mesh.receiveShadow=true; scene.add(mesh); return mesh;
}}
addBox(d.W/2,d.L/2,-.06,d.W+1,d.L+1,.12,groundMat);
d.posts.forEach(p=>{{const x=p["X [m]"],y=p["Y [m]"],h=roofH(y,x)-d.bh; addBox(x,y,h/2,d.pc,d.pc,h);}});

// belki podłużne — po jednej pełnej bryle na bok
[0,d.W].forEach(x=>{{
 const z0=roofH(0,x)-d.bh/2, z1=roofH(d.L,x)-d.bh/2;
 addMember([x,0,z0],[x,d.L,z1],d.bw,d.bh);
}});
// belki poprzeczne
[[0,d.Hf],[d.L,d.Hb]].forEach(v=>addMember([-d.pc/2,v[0],v[1]-d.bh/2],[d.W+d.pc/2,v[0],v[1]-d.bh/2],d.bw,d.bh));

// pełne drewniane zastrzały 3D — jedna ciągła bryła na element
if(d.braces){{
 const bl=Math.min(d.brace_len,d.L/3);
 [0,d.W].forEach(x=>{{
   addMember([x,0,roofH(0,x)-d.bh-bl],[x,bl,roofH(bl,x)-d.bh],.08,.08);
   addMember([x,d.L,roofH(d.L,x)-d.bh-bl],[x,d.L-bl,roofH(d.L-bl,x)-d.bh],.08,.08);
 }});
 const bx=Math.min(d.brace_len,d.W/3);
 addMember([0,0,d.Hf-d.bh-bx],[bx,0,d.Hf-d.bh],.08,.08);
 addMember([d.W,0,d.Hf-d.bh-bx],[d.W-bx,0,d.Hf-d.bh],.08,.08);
}}

if(d.rafter_direction==='W poprzek (X)'){{
 d.rafters.forEach(y=>{{
   if(d.roof_type==='Dwuspadowy'){{
     const slope=(d.ridge_h-d.Hf)/(d.W/2);
     const ze=d.Hf-slope*d.overhang+d.rh/2, zr=d.ridge_h+d.rh/2;
     addMember([-d.overhang,y,ze],[d.W/2,y,zr],d.rw,d.rh);
     addMember([d.W/2,y,zr],[d.W+d.overhang,y,ze],d.rw,d.rh);
   }} else {{
     const h=roofH(y,d.W/2)+d.rh/2;
     addMember([-d.overhang,y,h],[d.W+d.overhang,y,h],d.rw,d.rh);
   }}
 }});
}} else {{
 d.rafters.forEach(x=>{{
   let z0,z1;
   if(d.roof_type==='Jednospadowy'){{
     const slope=(d.Hb-d.Hf)/d.L;
     z0=d.Hf-slope*d.overhang+d.rh/2;
     z1=d.Hb+slope*d.overhang+d.rh/2;
   }} else {{
     z0=roofH(0,x)+d.rh/2; z1=z0;
   }}
   addMember([x,-d.overhang,z0],[x,d.L+d.overhang,z1],d.rw,d.rh);
 }});
}}
const grid=new THREE.GridHelper(Math.max(d.W,d.L)+2,Math.ceil(Math.max(d.W,d.L)+2),0x8f8a80,0xc7c1b6); grid.rotation.x=Math.PI/2; grid.position.z=.005; scene.add(grid);
function resize(){{const w=host.clientWidth;camera.aspect=w/760;camera.updateProjectionMatrix();renderer.setSize(w,760,false);}}
new ResizeObserver(resize).observe(host);
function animate(){{controls.update();renderer.render(scene,camera);requestAnimationFrame(animate);}} animate();
</script>
"""
st.subheader("🌲 Model 3D — nowy renderer")
st.caption("Three.js: pełne bryły, naturalne światło i cienie. Obracaj myszką, rolką przybliżaj.")
components.html(three_html,height=780,scrolling=False)

with st.expander("Awaryjny podgląd Plotly (stary renderer)",expanded=False):
    st.plotly_chart(fig,use_container_width=True)

c1,c2=st.columns([4.5,1])
with c1:
    st.subheader("Parametry modelu 3D")
    st.caption("Główny podgląd znajduje się powyżej w rendererze Three.js.")
with c2:
    st.subheader("Parametry")
    if roof_type=="Jednospadowy":
        pct=(Hf-Hb)/L*100; deg=math.degrees(math.atan((Hf-Hb)/L))
    elif roof_type=="Dwuspadowy":
        pct=(ridge_h-Hf)/(W/2)*100; deg=math.degrees(math.atan((ridge_h-Hf)/(W/2)))
    else:
        pct=0.0; deg=0.0
    st.metric("Dach",roof_type)
    st.metric("Słupy",len(posts))
    st.metric("Krokwie",rn)
    st.metric("Zastrzały",6 if braces else 0)
    st.metric("Spadek",f"{pct:.1f}% / {deg:.1f}°")
    st.metric("Powierzchnia",f"{W*L:.1f} m²")

st.subheader("📐 Rzut 2D z góry")
st.caption("S = słupy, R = elementy dodane ręcznie. Rzut aktualizuje się razem z modelem 3D.")
plan=go.Figure()
plan.add_shape(type="rect",x0=0,y0=0,x1=W,y1=L,line=dict(width=2))
for j,p in enumerate(posts,1):
    px=float(p["X [m]"]); py=float(p["Y [m]"])
    plan.add_trace(go.Scatter(x=[px],y=[py],mode="markers+text",text=[f"S{j}"],textposition="top center",
        marker=dict(size=13),hovertemplate=f"S{j}<br>X={px:.2f} m<br>Y={py:.2f} m<extra></extra>"))
for el in st.session_state.custom_elements:
    px=float(el["x"]); py=float(el["y"])
    label=f'R{el["id"]}'
    plan.add_trace(go.Scatter(x=[px],y=[py],mode="markers+text",text=[label],textposition="bottom center",
        marker=dict(size=11,symbol="square"),hovertemplate=f'{label} — {el["type"]}<br>X={px:.2f} m<br>Y={py:.2f} m<extra></extra>'))
plan.update_xaxes(title="X — szerokość [m]",range=[-.5,W+.5],scaleanchor="y",scaleratio=1)
plan.update_yaxes(title="Y — długość [m]",range=[-.5,L+.5])
plan.update_layout(height=620,margin=dict(l=10,r=10,t=10,b=10),showlegend=False)
st.plotly_chart(plan,use_container_width=True)

st.subheader("Zestawienie elementów")
if st.session_state.custom_elements: st.info(f"Ręcznie dodane elementy: {len(st.session_state.custom_elements)}")
post_lengths=[roof_h(p["Y [m]"],p["X [m]"])-bh for p in posts] if posts else [0]
rows=[
 {"Element":"Słupy","Ilość":len(posts),"Przekrój":f"{pc*100:.0f}×{pc*100:.0f} cm","Długość":f"{min(post_lengths):.2f}–{max(post_lengths):.2f} m"},
 {"Element":"Belki podłużne","Ilość":2,"Przekrój":f"{bw*100:.0f}×{bh*100:.0f} cm","Długość":f"{L:.2f} m"},
 {"Element":"Belki poprzeczne","Ilość":2,"Przekrój":f"{bw*100:.0f}×{bh*100:.0f} cm","Długość":f"{W+pc:.2f} m"},
 {"Element":"Krokwie","Ilość":rn,"Przekrój":f"{rw*100:.0f}×{rh*100:.0f} cm","Długość":f"{rafter_len:.2f} m"},
 {"Element":"Zastrzały","Ilość":6 if braces else 0,"Przekrój":"do ustalenia","Długość":f"ok. {brace_len:.2f} m"},
]
st.dataframe(rows,use_container_width=True,hide_index=True)

project={"version":VERSION,"roof_type":roof_type,"ridge_height_m":ridge_h,"width_m":W,"length_m":L,"front_height_m":Hf,"back_height_m":Hb,
"posts_per_side":nside,"post_mode":post_mode,"posts":posts,"rafter_direction":rafter_direction,"post_cm":pc*100,"beam_cm":[bw*100,bh*100],
"rafter_cm":[rw*100,rh*100],"rafter_spacing_m":spacing,"overhang_m":overhang,
"braces":braces,"brace_length_m":brace_len,"wood_material":base_wood,"wood_finish":base_finish,"wood_detail":wood_detail,"style_overrides":st.session_state.style_overrides,"custom_elements":st.session_state.custom_elements}
st.download_button("💾 Zapisz projekt",json.dumps(project,indent=2,ensure_ascii=False),
                   "wiata-v1.2.json","application/json")
st.warning("Model służy do projektowania geometrii i zestawienia materiału. Nie zastępuje obliczeń konstrukcyjnych.")

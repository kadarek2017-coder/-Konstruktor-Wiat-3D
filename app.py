import json, math
import pandas as pd
import streamlit as st
import plotly.graph_objects as go

VERSION = "0.9"
st.set_page_config(page_title=f"Konstruktor Wiat 3D v{VERSION}", page_icon="🏗️", layout="wide", initial_sidebar_state="collapsed")
st.title(f"Konstruktor Wiat 3D v{VERSION}")
st.caption("Parametryczny model drewnianej wiaty + ręczna biblioteka elementów 3D")

ELEMENT_LIBRARY={"Słup":{"a":.20,"b":.20,"length":3.0,"dir":"Z"},"Belka":{"a":.10,"b":.20,"length":3.0,"dir":"X"},"Krokiew":{"a":.08,"b":.18,"length":4.0,"dir":"X"},"Płatew":{"a":.10,"b":.20,"length":3.0,"dir":"Y"},"Łata":{"a":.04,"b":.06,"length":3.0,"dir":"X"},"Zastrzał":{"a":.08,"b":.08,"length":.8,"dir":"X"},"Blacha dachowa":{"a":1.10,"b":.005,"length":3.0,"dir":"Y"},"Stopa / kotwa":{"a":.20,"b":.20,"length":.20,"dir":"Z"}}
WOOD_COLORS={"Świerk":"#C9A66B","Sosna":"#D2AE72","Modrzew":"#B77945","Dąb":"#9B6B3E","KVH":"#D0A66A","BSH":"#B98550"}
FINISH_COLORS={"Surowe":None,"Olej naturalny":"#A97845","Impregnat jasny":"#B88958","Impregnat ciemny":"#6F4A2F","Biały":"#E7E3D8","Grafit":"#55575A"}
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
        flatshading=True, opacity=opacity, name=name, color=color,
        hovertemplate=f"{name}<extra></extra>", showscale=False
    ))

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
            box(-overhang,W+overhang,y-rw/2,y+rw/2,h,h+rh,f"K{i}",color=base_wood_color)
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
            box(x-rw/2,x+rw/2,y0,y1,h,h+rh,f"K{i}",color=base_wood_color)
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
    box(-.35,W+.35,-.35,L+.35,-.035,0,"Podłoże",.12)

fig.update_layout(
    height=900, margin=dict(l=0,r=0,t=5,b=0),
    scene=dict(
        xaxis_title="Szerokość [m]",yaxis_title="Długość [m]",zaxis_title="Wysokość [m]",
        aspectmode="data",camera=dict(eye=dict(x=1.45,y=-1.65,z=1.05))
    ),
    showlegend=False
)

c1,c2=st.columns([4.5,1])
with c1:
    st.subheader("Model 3D")
    st.plotly_chart(fig,use_container_width=True)
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
"braces":braces,"brace_length_m":brace_len,"wood_material":base_wood,"wood_finish":base_finish,"style_overrides":st.session_state.style_overrides,"custom_elements":st.session_state.custom_elements}
st.download_button("💾 Zapisz projekt",json.dumps(project,indent=2,ensure_ascii=False),
                   "wiata-v0.9.json","application/json")
st.warning("Model służy do projektowania geometrii i zestawienia materiału. Nie zastępuje obliczeń konstrukcyjnych.")

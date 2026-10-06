import json, math
import streamlit as st
import plotly.graph_objects as go

VERSION = "0.3"
st.set_page_config(page_title=f"Konstruktor Wiat 3D v{VERSION}", page_icon="🏗️", layout="wide")
st.title(f"Konstruktor Wiat 3D v{VERSION}")
st.caption("Parametryczny model drewnianej wiaty — rzeczywiste przekroje elementów 3D")

with st.sidebar:
    st.header("Wymiary")
    W=st.number_input("Szerokość [m]",2.0,15.0,7.0,.1)
    L=st.number_input("Długość [m]",2.0,15.0,6.0,.1)
    Hf=st.number_input("Wysokość przodu [m]",2.0,5.0,3.20,.05)
    Hb=st.number_input("Wysokość tyłu [m]",2.0,5.0,2.70,.05)
    nside=st.slider("Słupy na jednym boku",2,6,4)
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

fig=go.Figure()

def box(x0,x1,y0,y1,z0,z1,name,opacity=1.0):
    x=[x0,x1,x1,x0,x0,x1,x1,x0]
    y=[y0,y0,y1,y1,y0,y0,y1,y1]
    z=[z0,z0,z0,z0,z1,z1,z1,z1]
    fig.add_trace(go.Mesh3d(
        x=x,y=y,z=z,
        i=[0,0,0,1,1,2,4,4,4,5,5,6],
        j=[1,2,4,2,5,3,5,6,0,6,1,7],
        k=[2,3,5,5,6,7,6,7,7,7,2,3],
        flatshading=True, opacity=opacity, name=name,
        hovertemplate=f"{name}<extra></extra>", showscale=False
    ))

def roof_h(y):
    return Hf+(Hb-Hf)*(y/L)

ys=[i*L/(nside-1) for i in range(nside)]
# słupy
for side,x in enumerate((0,W),1):
    for j,y in enumerate(ys,1):
        h=roof_h(y)-bh
        box(x-pc/2,x+pc/2,y-pc/2,y+pc/2,0,h,f"S{side}.{j}")

# belki podłużne, podążające za spadkiem — dzielone na segmenty dla poprawnej geometrii
segments=max(12,int(L/.25))
for x in (0,W):
    for s in range(segments):
        y0=L*s/segments; y1=L*(s+1)/segments
        z0=roof_h((y0+y1)/2)-bh
        box(x-bw/2,x+bw/2,y0,y1,z0,z0+bh,"Belka podłużna")

# belki czołowa i tylna
for y,h in ((0,Hf),(L,Hb)):
    box(-pc/2,W+pc/2,y-bw/2,y+bw/2,h-bh,h,"Belka poprzeczna")

# krokwie — poziomo w poprzek szerokości, na wysokości wynikającej ze spadku wzdłuż długości
rn=max(2,math.ceil(L/spacing)+1)
rys=[i*L/(rn-1) for i in range(rn)]
for i,y in enumerate(rys,1):
    h=roof_h(y)
    box(-overhang,W+overhang,y-rw/2,y+rw/2,h,h+rh,f"K{i}")

# zastrzały — wizualizowane jako grube elementy ukośne
if braces:
    def member(x1,y1,z1,x2,y2,z2,name,width=9):
        fig.add_trace(go.Scatter3d(
            x=[x1,x2],y=[y1,y2],z=[z1,z2],mode="lines",
            line=dict(width=width),name=name,
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

# podłoże
if show_ground:
    box(-.35,W+.35,-.35,L+.35,-.035,0,"Podłoże",.12)

fig.update_layout(
    height=720, margin=dict(l=0,r=0,t=10,b=0),
    scene=dict(
        xaxis_title="Szerokość [m]",yaxis_title="Długość [m]",zaxis_title="Wysokość [m]",
        aspectmode="data",camera=dict(eye=dict(x=1.45,y=-1.65,z=1.05))
    ),
    showlegend=False
)

c1,c2=st.columns([2.3,1])
with c1:
    st.subheader("Model 3D")
    st.plotly_chart(fig,use_container_width=True)
with c2:
    st.subheader("Parametry")
    pct=(Hf-Hb)/L*100
    deg=math.degrees(math.atan((Hf-Hb)/L))
    st.metric("Słupy",2*nside)
    st.metric("Krokwie",rn)
    st.metric("Zastrzały",6 if braces else 0)
    st.metric("Spadek",f"{pct:.1f}% / {deg:.1f}°")
    st.metric("Powierzchnia",f"{W*L:.1f} m²")

st.subheader("Zestawienie elementów")
post_lengths=[roof_h(y)-bh for _ in (0,W) for y in ys]
rafter_len=W+2*overhang
rows=[
 {"Element":"Słupy","Ilość":2*nside,"Przekrój":f"{pc*100:.0f}×{pc*100:.0f} cm","Długość":f"{min(post_lengths):.2f}–{max(post_lengths):.2f} m"},
 {"Element":"Belki podłużne","Ilość":2,"Przekrój":f"{bw*100:.0f}×{bh*100:.0f} cm","Długość":f"{L:.2f} m"},
 {"Element":"Belki poprzeczne","Ilość":2,"Przekrój":f"{bw*100:.0f}×{bh*100:.0f} cm","Długość":f"{W+pc:.2f} m"},
 {"Element":"Krokwie","Ilość":rn,"Przekrój":f"{rw*100:.0f}×{rh*100:.0f} cm","Długość":f"{rafter_len:.2f} m"},
 {"Element":"Zastrzały","Ilość":6 if braces else 0,"Przekrój":"do ustalenia","Długość":f"ok. {brace_len:.2f} m"},
]
st.dataframe(rows,use_container_width=True,hide_index=True)

project={"version":VERSION,"width_m":W,"length_m":L,"front_height_m":Hf,"back_height_m":Hb,
"posts_per_side":nside,"post_cm":pc*100,"beam_cm":[bw*100,bh*100],
"rafter_cm":[rw*100,rh*100],"rafter_spacing_m":spacing,"overhang_m":overhang,
"braces":braces,"brace_length_m":brace_len}
st.download_button("💾 Zapisz projekt",json.dumps(project,indent=2,ensure_ascii=False),
                   "wiata-v0.3.json","application/json")
st.warning("Model służy do projektowania geometrii i zestawienia materiału. Nie zastępuje obliczeń konstrukcyjnych.")

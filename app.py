import json
import math
import streamlit as st
import plotly.graph_objects as go

st.set_page_config(page_title='Konstruktor Wiat 3D v0.1', page_icon='🏗️', layout='wide')

st.title('Konstruktor Wiat 3D v0.1')
st.caption('Generator prostej drewnianej wiaty — model 3D + zestawienie elementów')

with st.sidebar:
    st.header('Parametry wiaty')
    width = st.number_input('Szerokość [m]', 2.0, 15.0, 7.0, 0.1)
    length = st.number_input('Długość [m]', 2.0, 15.0, 6.0, 0.1)
    front_h = st.number_input('Wysokość przodu [m]', 2.0, 5.0, 3.20, 0.05)
    back_h = st.number_input('Wysokość tyłu [m]', 2.0, 5.0, 2.70, 0.05)
    posts_side = st.slider('Słupy na jednym boku', 2, 6, 4)
    st.subheader('Przekroje')
    post_cm = st.number_input('Słup [cm]', 8, 30, 20, 1)
    beam_w = st.number_input('Belka — szerokość [cm]', 5, 30, 10, 1)
    beam_h = st.number_input('Belka — wysokość [cm]', 10, 40, 20, 1)
    rafter_w = st.number_input('Krokiew — szerokość [cm]', 4, 20, 8, 1)
    rafter_h = st.number_input('Krokiew — wysokość [cm]', 8, 30, 18, 1)
    rafter_spacing = st.number_input('Rozstaw krokwi [m]', 0.30, 1.50, 0.70, 0.05)

def line(fig, x1,y1,z1,x2,y2,z2, width_px=8, name=None, showlegend=False):
    fig.add_trace(go.Scatter3d(
        x=[x1,x2], y=[y1,y2], z=[z1,z2], mode='lines',
        line=dict(width=width_px), name=name or '', showlegend=showlegend,
        hoverinfo='skip'
    ))

fig = go.Figure()
ys = [i * length/(posts_side-1) for i in range(posts_side)]

def roof_h(y):
    return front_h + (back_h-front_h)*(y/length)

post_count = 0
for x in (0, width):
    for y in ys:
        h = roof_h(y)
        line(fig, x,y,0,x,y,h, 10)
        post_count += 1

for x in (0, width):
    line(fig, x,0,front_h,x,length,back_h, 12)

line(fig, 0,0,front_h,width,0,front_h, 12)
line(fig, 0,length,back_h,width,length,back_h, 12)

rafter_n = max(2, math.ceil(length/rafter_spacing)+1)
rafter_ys = [i*length/(rafter_n-1) for i in range(rafter_n)]
for y in rafter_ys:
    h=roof_h(y)+0.04
    line(fig, 0,y,h,width,y,h, 6)

fig.add_trace(go.Mesh3d(
    x=[0,width,width,0], y=[0,0,length,length], z=[0,0,0,0],
    i=[0,0], j=[1,2], k=[2,3], opacity=0.12, hoverinfo='skip', showlegend=False
))

fig.update_layout(
    height=700,
    margin=dict(l=0,r=0,t=20,b=0),
    scene=dict(
        xaxis_title='Szerokość [m]', yaxis_title='Długość [m]', zaxis_title='Wysokość [m]',
        aspectmode='data',
        camera=dict(eye=dict(x=1.5,y=-1.7,z=1.15))
    )
)

left, right = st.columns([2.2,1])
with left:
    st.subheader('Model 3D')
    st.plotly_chart(fig, use_container_width=True)
with right:
    st.subheader('Podsumowanie')
    slope_pct = (front_h-back_h)/length*100
    slope_deg = math.degrees(math.atan((front_h-back_h)/length))
    st.metric('Liczba słupów', post_count)
    st.metric('Liczba krokwi', rafter_n)
    st.metric('Spadek dachu', f'{slope_pct:.1f}% / {slope_deg:.1f}°')
    st.metric('Powierzchnia rzutu', f'{width*length:.1f} m²')

st.subheader('Zestawienie drewna — orientacyjne')
post_lengths = [roof_h(y) for x in (0,width) for y in ys]
rows = [
    {'Element':'Słupy', 'Ilość':post_count, 'Przekrój':f'{post_cm}×{post_cm} cm', 'Długość':'zmienna '+f'{min(post_lengths):.2f}–{max(post_lengths):.2f} m'},
    {'Element':'Belki podłużne', 'Ilość':2, 'Przekrój':f'{beam_w}×{beam_h} cm', 'Długość':f'{length:.2f} m'},
    {'Element':'Belki poprzeczne', 'Ilość':2, 'Przekrój':f'{beam_w}×{beam_h} cm', 'Długość':f'{width:.2f} m'},
    {'Element':'Krokwie', 'Ilość':rafter_n, 'Przekrój':f'{rafter_w}×{rafter_h} cm', 'Długość':f'{width:.2f} m'},
]
st.dataframe(rows, use_container_width=True, hide_index=True)

project = {
    'version':'0.1', 'width_m':width, 'length_m':length, 'front_height_m':front_h,
    'back_height_m':back_h, 'posts_per_side':posts_side,
    'post_cm':[post_cm,post_cm], 'beam_cm':[beam_w,beam_h],
    'rafter_cm':[rafter_w,rafter_h], 'rafter_spacing_m':rafter_spacing
}
st.download_button('💾 Zapisz projekt (.json)', json.dumps(project, indent=2, ensure_ascii=False), 'wiata-projekt-v0.1.json', 'application/json')

st.info('v0.1 służy do modelowania geometrii i zestawienia elementów. Nie wykonuje obliczeń konstrukcyjnych/nośności.')

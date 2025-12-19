"""
Système Solaire Complet - Vue 2D avec échelle logarithmique

Fonctionnalités :
- 8 planètes avec orbites elliptiques réalistes
- Échelle logarithmique pour voir toutes les planètes
- Animation fluide
- Filtre de planètes

Usage:
    streamlit run src/ui/prototype_3d.py
"""

import numpy as np
import plotly.graph_objects as go
import streamlit as st
from dataclasses import dataclass

# Configuration
st.set_page_config(
    page_title="Système Solaire",
    page_icon="☀️",
    layout="wide",
)

st.title("☀️ Système Solaire Complet")
st.markdown("**8 planètes - Échelle logarithmique pour meilleure visibilité**")


# --- MODÈLES ---

@dataclass
class Star:
    name: str
    radius: float
    color: str


@dataclass
class Planet:
    name: str
    semi_major_axis: float  # AU
    orbital_period: float  # Jours
    radius: float  # Rayons terrestres
    eccentricity: float
    color: str


# --- DONNÉES ---

sun = Star("Soleil", 1.0, "#FDB813")

planets = [
    Planet("Mercure", 0.387, 88, 0.383, 0.2056, "#8C7853"),
    Planet("Vénus", 0.723, 225, 0.949, 0.0068, "#FFC649"),
    Planet("Terre", 1.000, 365, 1.000, 0.0167, "#4169E1"),
    Planet("Mars", 1.524, 687, 0.532, 0.0934, "#CD5C5C"),
    Planet("Jupiter", 5.203, 4333, 11.209, 0.0489, "#DAA520"),
    Planet("Saturne", 9.537, 10759, 9.449, 0.0565, "#F4A460"),
    Planet("Uranus", 19.191, 30687, 4.007, 0.0457, "#4FD0E0"),
    Planet("Neptune", 30.069, 60190, 3.883, 0.0113, "#4169E1"),
]


# --- FONCTIONS ---

def scale_distance(distance, use_log=True):
    """Applique échelle logarithmique si activée."""
    if use_log:
        return np.log1p(distance) * 2.5
    return distance


def calculate_position(semi_major_axis, eccentricity, time_fraction):
    """Position sur orbite elliptique (Kepler)."""
    M = 2 * np.pi * time_fraction
    E = M
    for _ in range(10):
        E = M + eccentricity * np.sin(E)
    x = semi_major_axis * (np.cos(E) - eccentricity)
    y = semi_major_axis * np.sqrt(1 - eccentricity**2) * np.sin(E)
    return x, y


def generate_orbit(semi_major_axis, eccentricity, num_points=200):
    """Génère orbite elliptique."""
    fractions = np.linspace(0, 1, num_points)
    positions = [calculate_position(semi_major_axis, eccentricity, t) for t in fractions]
    return [p[0] for p in positions], [p[1] for p in positions]


def create_circle(x, y, radius, color):
    """Cercle plein."""
    return dict(
        type="circle", xref="x", yref="y",
        x0=x-radius, y0=y-radius, x1=x+radius, y1=y+radius,
        fillcolor=color, line=dict(color="white", width=2), opacity=0.95
    )


# --- SESSION STATE ---

if "time_days" not in st.session_state:
    st.session_state.time_days = 0.0
if "is_playing" not in st.session_state:
    st.session_state.is_playing = False


# --- SIDEBAR ---

st.sidebar.header("🎮 Contrôles")

col1, col2 = st.sidebar.columns(2)
with col1:
    if st.button("▶️" if not st.session_state.is_playing else "⏸️", use_container_width=True):
        st.session_state.is_playing = not st.session_state.is_playing
with col2:
    if st.button("🔄", use_container_width=True):
        st.session_state.time_days = 0.0

speed = st.sidebar.slider("⚡ Vitesse", 0.1, 50.0, 10.0, 0.5)

max_time = float(planets[-1].orbital_period)
if not st.session_state.is_playing:
    st.session_state.time_days = st.sidebar.slider(
        "⏱️ Temps (jours)", 0.0, max_time, st.session_state.time_days, 10.0
    )
else:
    st.sidebar.slider("⏱️ Temps (jours)", 0.0, max_time, st.session_state.time_days, 10.0, disabled=True)

st.sidebar.markdown("---")

size_scale = st.sidebar.slider("🔍 Tailles", 1, 200, 50, 5)

use_log_scale = st.sidebar.checkbox(
    "📏 Échelle logarithmique",
    value=True,
    help="Compresse les grandes distances pour voir toutes les planètes"
)

planet_filter = st.sidebar.multiselect(
    "🪐 Planètes",
    [p.name for p in planets],
    default=[p.name for p in planets],
)

st.sidebar.markdown("---")
show_orbits = st.sidebar.checkbox("Orbites", True)
show_labels = st.sidebar.checkbox("Labels", True)

st.sidebar.markdown("---")
st.sidebar.metric("Temps", f"{st.session_state.time_days:.0f} j")
st.sidebar.metric("Années", f"{st.session_state.time_days/365:.2f}")


# --- CRÉATION FIGURE ---

def create_view():
    fig = go.Figure()
    shapes = []
    annotations = []
    
    # Soleil
    sun_radius = sun.radius * 0.00465 * size_scale
    shapes.append(create_circle(0, 0, sun_radius, sun.color))
    if show_labels:
        annotations.append(dict(
            x=0, y=sun_radius+0.1, text=sun.name, showarrow=False,
            font=dict(size=14, color="white", family="Arial Black")
        ))
    
    # Planètes filtrées
    visible_planets = [p for p in planets if p.name in planet_filter]
    
    # Orbites
    if show_orbits:
        for planet in visible_planets:
            scaled_a = scale_distance(planet.semi_major_axis, use_log_scale)
            orbit_x, orbit_y = generate_orbit(scaled_a, planet.eccentricity)
            fig.add_trace(go.Scatter(
                x=orbit_x, y=orbit_y, mode="lines",
                line=dict(color=planet.color, width=1, dash="dot"),
                showlegend=False, hoverinfo="skip"
            ))
    
    # Planètes
    for planet in visible_planets:
        time_fraction = st.session_state.time_days / planet.orbital_period
        scaled_a = scale_distance(planet.semi_major_axis, use_log_scale)
        x, y = calculate_position(scaled_a, planet.eccentricity, time_fraction)
        
        planet_radius = planet.radius * 0.0000426 * size_scale
        shapes.append(create_circle(x, y, planet_radius, planet.color))
        
        if show_labels:
            annotations.append(dict(
                x=x, y=y+planet_radius+0.08, text=planet.name,
                showarrow=False, font=dict(size=11, color="white")
            ))
        
        fig.add_trace(go.Scatter(
            x=[x], y=[y], mode="markers",
            marker=dict(size=1, color="rgba(0,0,0,0)"),
            name=planet.name,
            hovertemplate=f"<b>{planet.name}</b><br>"
                         f"Distance: {planet.semi_major_axis:.3f} AU<br>"
                         f"Excentricité: {planet.eccentricity:.4f}<br>"
                         f"Période: {planet.orbital_period} j<br>"
                         f"Rayon: {planet.radius:.3f} R⊕<br>"
                         "<extra></extra>"
        ))
    
    # Layout
    if visible_planets:
        max_dist = scale_distance(visible_planets[-1].semi_major_axis, use_log_scale) * 1.2
    else:
        max_dist = 10
    
    fig.update_layout(
        shapes=shapes, annotations=annotations,
        xaxis=dict(
            title="X (AU log)" if use_log_scale else "X (AU)",
            range=[-max_dist, max_dist], scaleanchor="y", scaleratio=1,
            showgrid=True, gridcolor="rgba(80,80,80,0.3)",
            zeroline=True, zerolinecolor="rgba(255,255,255,0.4)"
        ),
        yaxis=dict(
            title="Y (AU log)" if use_log_scale else "Y (AU)",
            range=[-max_dist, max_dist],
            showgrid=True, gridcolor="rgba(80,80,80,0.3)",
            zeroline=True, zerolinecolor="rgba(255,255,255,0.4)"
        ),
        title=dict(
            text=f"Système Solaire - {st.session_state.time_days:.0f} j ({st.session_state.time_days/365:.2f} ans) | {'Log' if use_log_scale else 'Lin'}",
            x=0.5, xanchor="center", font=dict(size=16, color="white")
        ),
        showlegend=False,
        paper_bgcolor="rgb(5, 5, 15)",
        plot_bgcolor="rgb(10, 10, 25)",
        font=dict(color="white"),
        height=700,
        hovermode="closest"
    )
    
    return fig


# --- AFFICHAGE ---

chart_placeholder = st.empty()

if st.session_state.is_playing:
    st.session_state.time_days += speed
    if st.session_state.time_days >= max_time:
        st.session_state.time_days = 0.0
    with chart_placeholder.container():
        fig = create_view()
        st.plotly_chart(fig, use_container_width=True)
    st.rerun()
else:
    with chart_placeholder.container():
        fig = create_view()
        st.plotly_chart(fig, use_container_width=True)

# Métriques
st.markdown("---")
cols = st.columns(len(planets))
for i, planet in enumerate(planets):
    with cols[i]:
        st.metric(planet.name, f"{planet.semi_major_axis:.2f} AU", f"{planet.orbital_period} j")

st.info("""
**💡 Utilisation :**
- **Échelle logarithmique** : Active pour voir toutes les planètes ensemble
- **Filtre planètes** : Sélectionne les planètes à afficher
- **▶️** : Lance l'animation
- **Vitesse** : Contrôle la rapidité (jours par frame)
""")

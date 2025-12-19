"""
Comparaison interactive : Système Solaire vs Kepler-20
Vue 2D avec orbites et animation

Usage:
    streamlit run src/ui/kepler20_comparison.py --server.port 8505
"""

import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st
from dataclasses import dataclass

# Configuration
st.set_page_config(
    page_title="Système Solaire vs Kepler-20",
    page_icon="🌍",
    layout="wide",
)

st.title("🌍 Comparaison : Système Solaire vs Kepler-20")
st.markdown("**Deux systèmes planétaires côte à côte**")


# --- MODÈLES ---


@dataclass
class Star:
    name: str
    radius: float  # Rayons solaires
    color: str


@dataclass
class Planet:
    name: str
    semi_major_axis: float  # AU
    orbital_period: float  # Jours
    radius: float  # Rayons terrestres
    eccentricity: float
    color: str


# --- DONNÉES SYSTÈME SOLAIRE ---

sun = Star("Soleil", 1.0, "#FDB813")

solar_planets = [
    Planet("Mercure", 0.387, 88, 0.383, 0.2056, "#8C7853"),
    Planet("Vénus", 0.723, 225, 0.949, 0.0068, "#FFC649"),
    Planet("Terre", 1.000, 365, 1.000, 0.0167, "#4169E1"),
    Planet("Mars", 1.524, 687, 0.532, 0.0934, "#CD5C5C"),
]


# --- DONNÉES KEPLER-20 (depuis votre CSV) ---

kepler20_star = Star("Kepler-20", 0.929, "#FFE4B5")

kepler20_planets = [
    Planet("Kepler-20 b", 0.04565, 3.696, 1.773, 0.083, "#D2691E"),
    Planet("Kepler-20 e", 0.0637, 6.098, 0.821, 0.092, "#87CEEB"),
    Planet("Kepler-20 c", 0.0936, 10.854, 2.894, 0.076, "#FF6347"),
    Planet("Kepler-20 f", 0.1387, 19.578, 0.952, 0.094, "#90EE90"),
    Planet("Kepler-20 d", 0.3474, 77.611, 2.606, 0.082, "#FFA07A"),
]


# --- FONCTIONS ---


def scale_distance(distance, use_log=True):
    """Échelle logarithmique pour visualisation."""
    if use_log:
        return np.log1p(distance) * 2.5
    return distance


def calculate_position(semi_major_axis, eccentricity, time_fraction):
    """Position sur orbite elliptique (équation de Kepler)."""
    M = 2 * np.pi * time_fraction
    E = M
    for _ in range(10):
        E = M + eccentricity * np.sin(E)
    x = semi_major_axis * (np.cos(E) - eccentricity)
    y = semi_major_axis * np.sqrt(1 - eccentricity**2) * np.sin(E)
    return x, y


def generate_orbit(semi_major_axis, eccentricity, num_points=200):
    """Génère les points d'une orbite elliptique."""
    fractions = np.linspace(0, 1, num_points)
    positions = [calculate_position(semi_major_axis, eccentricity, t) for t in fractions]
    return [p[0] for p in positions], [p[1] for p in positions]


def create_circle(x, y, radius, color):
    """Forme de cercle pour Plotly."""
    return dict(
        type="circle",
        xref="x",
        yref="y",
        x0=x - radius,
        y0=y - radius,
        x1=x + radius,
        y1=y + radius,
        fillcolor=color,
        line=dict(color="white", width=1.5),
        opacity=0.95,
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
    if st.button("🔄 Reset", use_container_width=True):
        st.session_state.time_days = 0.0

speed = st.sidebar.slider("⚡ Vitesse (jours/frame)", 0.1, 20.0, 5.0, 0.5)

# Temps max basé sur la planète la plus lente
max_time_solar = solar_planets[-1].orbital_period
max_time_kepler = kepler20_planets[-1].orbital_period
max_time = max(max_time_solar, max_time_kepler)

if not st.session_state.is_playing:
    st.session_state.time_days = st.sidebar.slider(
        "⏱️ Temps (jours)", 0.0, max_time, st.session_state.time_days, 1.0
    )
else:
    st.sidebar.slider(
        "⏱️ Temps (jours)", 0.0, max_time, st.session_state.time_days, 1.0, disabled=True
    )

st.sidebar.markdown("---")

size_scale = st.sidebar.slider("🔍 Taille des planètes", 1, 100, 30, 5)

use_log_scale = st.sidebar.checkbox(
    "📏 Échelle logarithmique",
    value=True,
    help="Compresse les distances pour mieux voir les orbites compactes",
)

st.sidebar.markdown("---")
show_orbits = st.sidebar.checkbox("Afficher orbites", True)
show_labels = st.sidebar.checkbox("Afficher labels", True)

st.sidebar.markdown("---")
st.sidebar.metric("Temps écoulé", f"{st.session_state.time_days:.1f} j")
st.sidebar.metric("Années terrestres", f"{st.session_state.time_days / 365:.3f}")


# --- CRÉATION FIGURE ---


def create_system_view(star, planets, system_name, subplot_col):
    """Crée la vue d'un système planétaire."""
    shapes = []
    annotations = []
    traces = []

    # Étoile au centre
    star_radius = star.radius * 0.005 * size_scale
    shapes.append(create_circle(0, 0, star_radius, star.color))
    if show_labels:
        annotations.append(
            dict(
                x=0,
                y=star_radius + 0.05,
                text=star.name,
                showarrow=False,
                font=dict(size=12, color="white", family="Arial Black"),
                xref=f"x{subplot_col}",
                yref=f"y{subplot_col}",
            )
        )

    # Orbites
    if show_orbits:
        for planet in planets:
            scaled_a = scale_distance(planet.semi_major_axis, use_log_scale)
            orbit_x, orbit_y = generate_orbit(scaled_a, planet.eccentricity)
            traces.append(
                go.Scatter(
                    x=orbit_x,
                    y=orbit_y,
                    mode="lines",
                    line=dict(color=planet.color, width=1, dash="dot"),
                    showlegend=False,
                    hoverinfo="skip",
                    xaxis=f"x{subplot_col}",
                    yaxis=f"y{subplot_col}",
                )
            )

    # Planètes
    for planet in planets:
        time_fraction = st.session_state.time_days / planet.orbital_period
        scaled_a = scale_distance(planet.semi_major_axis, use_log_scale)
        x, y = calculate_position(scaled_a, planet.eccentricity, time_fraction)

        planet_radius = planet.radius * 0.00005 * size_scale
        shapes.append(create_circle(x, y, planet_radius, planet.color))

        if show_labels:
            annotations.append(
                dict(
                    x=x,
                    y=y + planet_radius + 0.04,
                    text=planet.name.split()[-1],
                    showarrow=False,
                    font=dict(size=9, color="white"),
                    xref=f"x{subplot_col}",
                    yref=f"y{subplot_col}",
                )
            )

        # Point invisible pour hover
        traces.append(
            go.Scatter(
                x=[x],
                y=[y],
                mode="markers",
                marker=dict(size=1, color="rgba(0,0,0,0)"),
                name=planet.name,
                hovertemplate=f"<b>{planet.name}</b><br>"
                f"Distance: {planet.semi_major_axis:.4f} AU<br>"
                f"Période: {planet.orbital_period:.1f} j<br>"
                f"Rayon: {planet.radius:.3f} R⊕<br>"
                f"Excentricité: {planet.eccentricity:.4f}<br>"
                "<extra></extra>",
                xaxis=f"x{subplot_col}",
                yaxis=f"y{subplot_col}",
            )
        )

    # Calcul limites
    if planets:
        max_dist = scale_distance(planets[-1].semi_major_axis, use_log_scale) * 1.3
    else:
        max_dist = 1

    return traces, shapes, annotations, max_dist


# --- AFFICHAGE ---

# Créer subplot avec 2 colonnes
fig = make_subplots(
    rows=1,
    cols=2,
    subplot_titles=("Système Solaire (4 planètes internes)", "Système Kepler-20 (5 planètes)"),
    horizontal_spacing=0.1,
)

# Système Solaire
traces_solar, shapes_solar, annot_solar, max_dist_solar = create_system_view(
    sun, solar_planets, "Système Solaire", 1
)

# Kepler-20
traces_kepler, shapes_kepler, annot_kepler, max_dist_kepler = create_system_view(
    kepler20_star, kepler20_planets, "Kepler-20", 2
)

# Ajouter toutes les traces
for trace in traces_solar + traces_kepler:
    fig.add_trace(trace)

# Layout global
fig.update_layout(
    shapes=shapes_solar + shapes_kepler,
    annotations=annot_solar + annot_kepler,
    showlegend=False,
    paper_bgcolor="rgb(5, 5, 15)",
    plot_bgcolor="rgb(10, 10, 25)",
    font=dict(color="white"),
    height=700,
    hovermode="closest",
    title=dict(
        text=f"Comparaison des systèmes planétaires - {st.session_state.time_days:.0f} jours ({st.session_state.time_days / 365:.3f} ans)",
        x=0.5,
        xanchor="center",
        font=dict(size=18, color="white"),
    ),
)

# Axes système solaire
fig.update_xaxes(
    title="X (AU)" if not use_log_scale else "X (AU log)",
    range=[-max_dist_solar, max_dist_solar],
    scaleanchor="y",
    scaleratio=1,
    showgrid=True,
    gridcolor="rgba(80,80,80,0.3)",
    zeroline=True,
    zerolinecolor="rgba(255,255,255,0.4)",
    row=1,
    col=1,
)
fig.update_yaxes(
    title="Y (AU)" if not use_log_scale else "Y (AU log)",
    range=[-max_dist_solar, max_dist_solar],
    showgrid=True,
    gridcolor="rgba(80,80,80,0.3)",
    zeroline=True,
    zerolinecolor="rgba(255,255,255,0.4)",
    row=1,
    col=1,
)

# Axes Kepler-20
fig.update_xaxes(
    title="X (AU)" if not use_log_scale else "X (AU log)",
    range=[-max_dist_kepler, max_dist_kepler],
    scaleanchor="y2",
    scaleratio=1,
    showgrid=True,
    gridcolor="rgba(80,80,80,0.3)",
    zeroline=True,
    zerolinecolor="rgba(255,255,255,0.4)",
    row=1,
    col=2,
)
fig.update_yaxes(
    title="Y (AU)" if not use_log_scale else "Y (AU log)",
    range=[-max_dist_kepler, max_dist_kepler],
    showgrid=True,
    gridcolor="rgba(80,80,80,0.3)",
    zeroline=True,
    zerolinecolor="rgba(255,255,255,0.4)",
    row=1,
    col=2,
)

# Affichage
chart_placeholder = st.empty()

if st.session_state.is_playing:
    st.session_state.time_days += speed
    if st.session_state.time_days >= max_time:
        st.session_state.time_days = 0.0
    with chart_placeholder.container():
        st.plotly_chart(fig, use_container_width=True)
    st.rerun()
else:
    with chart_placeholder.container():
        st.plotly_chart(fig, use_container_width=True)


# --- TABLEAU COMPARATIF ---

st.markdown("---")
st.subheader("📊 Comparaison des caractéristiques")

col1, col2 = st.columns(2)

with col1:
    st.markdown("### Système Solaire")
    st.markdown(f"**Étoile:** {sun.name} (1.0 R☉)")
    st.markdown("**Planètes internes:**")
    for p in solar_planets:
        st.markdown(
            f"- **{p.name}**: {p.semi_major_axis:.3f} AU, {p.orbital_period:.0f} j, {p.radius:.3f} R⊕"
        )

with col2:
    st.markdown("### Système Kepler-20")
    st.markdown(f"**Étoile:** {kepler20_star.name} (0.929 R☉)")
    st.markdown("**5 planètes confirmées:**")
    for p in kepler20_planets:
        st.markdown(
            f"- **{p.name}**: {p.semi_major_axis:.4f} AU, {p.orbital_period:.1f} j, {p.radius:.3f} R⊕"
        )

st.info("""
**💡 Points clés :**
- **Kepler-20** est un système très compact : toutes ses planètes orbitent plus près de leur étoile que Mercure du Soleil
- Les planètes de Kepler-20 ont des périodes orbitales très courtes (3.7 à 77 jours)
- Kepler-20 e et f sont de taille terrestre mais inhabitables (trop chaudes)
- L'échelle logarithmique permet de visualiser les deux systèmes malgré leurs différences d'échelle
""")

"""
Visualisation comparative du système solaire avec matplotlib
Affiche deux vues : échelle compressée et échelle quasi-réelle
"""

import matplotlib.pyplot as plt
import numpy as np

# -----------------------------
# Data definition (real radii in km)
# -----------------------------
bodies = [
    {
        "id": "sun",
        "name": "Sun",
        "radius_km": 696340.0,
        "type": "star",
        "temp_k": 5778.0,
        "composition": "H/He",
    },
    {
        "id": "mercury",
        "name": "Mercury",
        "radius_km": 2439.7,
        "type": "planet",
        "composition": "rocky",
        "albedo": 0.068,
    },
    {
        "id": "venus",
        "name": "Venus",
        "radius_km": 6051.8,
        "type": "planet",
        "composition": "rocky",
        "albedo": 0.9,
    },
    {
        "id": "earth",
        "name": "Earth",
        "radius_km": 6371.0,
        "type": "planet",
        "composition": "rocky",
        "albedo": 0.306,
    },
    {
        "id": "mars",
        "name": "Mars",
        "radius_km": 3389.5,
        "type": "planet",
        "composition": "rocky",
        "albedo": 0.15,
    },
    {
        "id": "jupiter",
        "name": "Jupiter",
        "radius_km": 69911.0,
        "type": "planet",
        "composition": "gas giant",
        "albedo": 0.52,
    },
    {
        "id": "saturn",
        "name": "Saturn",
        "radius_km": 58232.0,
        "type": "planet",
        "composition": "gas giant",
        "albedo": 0.47,
    },
    {
        "id": "uranus",
        "name": "Uranus",
        "radius_km": 25362.0,
        "type": "planet",
        "composition": "ice giant",
        "albedo": 0.51,
    },
    {
        "id": "neptune",
        "name": "Neptune",
        "radius_km": 24622.0,
        "type": "planet",
        "composition": "ice giant",
        "albedo": 0.41,
    },
]


# -----------------------------
# Color functions
# -----------------------------
def blackbody_color(temp_k: float) -> tuple[float, float, float]:
    """Approximate blackbody color (RGB normalized 0-1)."""
    t = np.clip(temp_k / 100.0, 10, 400)
    if t <= 66:
        r = 255
        g = np.clip(99.47 * np.log(t) - 161.12, 0, 255)
        if t <= 19:
            b = 0
        else:
            b = np.clip(138.52 * np.log(t - 10) - 305.04, 0, 255)
    else:
        r = np.clip(329.70 * (t - 60) ** -0.1332, 0, 255)
        g = np.clip(288.12 * (t - 60) ** -0.0755, 0, 255)
        b = 255
    return (r / 255.0, g / 255.0, b / 255.0)


def body_color(body: dict) -> tuple[float, float, float]:
    """Return synthetic color based on composition."""
    comp = body.get("composition", "").lower()

    if body["type"] == "star":
        return blackbody_color(body.get("temp_k", 5500.0))

    if "rock" in comp:
        albedo = float(body.get("albedo", 0.2))
        hue = 0.06
        saturation = 0.6
        light = 0.2 + 0.5 * albedo
        return hsl_to_rgb(hue, saturation, light)

    if "gas" in comp:
        return hsl_to_rgb(0.58, 0.6, 0.45)

    if "ice" in comp:
        return hsl_to_rgb(0.55, 0.5, 0.6)

    return (0.6, 0.6, 0.6)


def hsl_to_rgb(h: float, s: float, l: float) -> tuple[float, float, float]:
    """Small HSL→RGB converter."""
    c = (1 - abs(2 * l - 1)) * s
    x = c * (1 - abs((h * 6) % 2 - 1))
    m = l - c / 2

    if 0 <= h < 1 / 6:
        r1, g1, b1 = c, x, 0
    elif 1 / 6 <= h < 2 / 6:
        r1, g1, b1 = x, c, 0
    elif 2 / 6 <= h < 3 / 6:
        r1, g1, b1 = 0, c, x
    elif 3 / 6 <= h < 4 / 6:
        r1, g1, b1 = 0, x, c
    elif 4 / 6 <= h < 5 / 6:
        r1, g1, b1 = x, 0, c
    else:
        r1, g1, b1 = c, 0, x

    return (r1 + m, g1 + m, b1 + m)


# -----------------------------
# Scale function (non-linear)
# -----------------------------
def scaled_radius(real_km: float, alpha: float = 0.5) -> float:
    """Return radius scaled non-linearly. alpha < 1 compresses big objects."""
    return real_km**alpha


# -----------------------------
# Plotting helpers
# -----------------------------
def draw_circles(ax, scale_func, title: str):
    """Draw bodies side-by-side using a given scale function."""
    ax.set_aspect("equal")
    ax.set_title(title, color="white", fontsize=14, pad=20)
    ax.axis("off")

    positions = []

    # Sun - half circle on the left edge
    sun_body = bodies[0]
    sun_r = scale_func(float(sun_body["radius_km"]))
    sun_col = body_color(sun_body)

    # Draw half sun (right half visible)
    theta = np.linspace(-np.pi / 2, np.pi / 2, 100)
    sun_x = sun_r * np.cos(theta)
    sun_y = sun_r * np.sin(theta)
    ax.fill(sun_x, sun_y, color=sun_col, ec="white", linewidth=1)
    ax.text(
        0,
        -sun_r * 1.5,
        sun_body["name"],
        ha="center",
        va="top",
        fontsize=10,
        color="white",
        weight="bold",
    )

    # Planets - start after the sun with good spacing
    x_offset = sun_r * 1.5  # Start position for first planet

    # Calculate positions for planets (skip sun)
    for body in bodies[1:]:
        r = scale_func(float(body["radius_km"]))
        col = body_color(body)

        x_offset += r  # Add radius to position center
        positions.append((x_offset, r, col, body["name"]))
        x_offset += r * 4.0  # Much more spacing between planets

    # Draw planets
    max_radius = sun_r
    for x, r, col, name in positions:
        circ = plt.Circle((x, 0.0), r, color=col, ec="white", linewidth=0.8)
        ax.add_patch(circ)
        ax.text(x, -r * 1.5, name, ha="center", va="top", fontsize=9, color="white")
        max_radius = max(max_radius, r)

    # Set axis limits - start from 0 (sun edge) and use full width
    if positions:
        x_max = positions[-1][0] + positions[-1][1] * 2.0
        y_range = max_radius * 2.5
        ax.set_xlim(-sun_r * 0.1, x_max)  # Small negative margin for sun edge
        ax.set_ylim(-y_range, y_range)


# -----------------------------
# Main figure
# -----------------------------
def main():
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(20, 12))
    fig.suptitle("Solar System – Size vs Color Comparison", color="white", fontsize=16)
    fig.patch.set_facecolor("#101520")

    def scale_compressed(km: float) -> float:
        return scaled_radius(km, alpha=0.45)

    def scale_true(km: float) -> float:
        return km * 0.005

    draw_circles(ax1, scale_compressed, "Compressed Scale (visual comparison)")
    draw_circles(ax2, scale_true, "Near True Scale (proportion reminder)")

    ax1.set_facecolor("#0b0f1a")
    ax2.set_facecolor("#0b0f1a")

    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    main()

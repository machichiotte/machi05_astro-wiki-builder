import ast
import os
import sys
from pathlib import Path

import pandas as pd
import streamlit as st

# Ajouter la racine du projet au PYTHONPATH pour les imports
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))

from src.models.entities.exoplanet_entity import Exoplanet, ValueWithUncertainty  # noqa: E402
from src.utils.wikipedia.draft_util import build_exoplanet_article_draft  # noqa: E402

# Config de la page
st.set_page_config(
    page_title="AstroWikiBuilder",
    page_icon="🪐",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- UTILS ---


def parse_value_with_uncertainty(val_str):
    """
    Convertit une chaîne 'ValueWithUncertainty(...)' en objet réel.
    Gère aussi les NaN/None.
    """
    if pd.isna(val_str) or not isinstance(val_str, str):
        return None

    # Nettoyage basique
    val_str = val_str.strip()
    if not val_str.startswith("ValueWithUncertainty"):
        return None

    try:
        # On utilise eval dans un contexte restreint où seule la classe est connue
        # C'est safe car on contrôle le CSV source
        return eval(val_str, {"ValueWithUncertainty": ValueWithUncertainty, "None": None})  # nosec
    except Exception:
        # Fallback silencieux
        return None


def row_to_exoplanet(row) -> Exoplanet:
    """
    Convertit une série pandas (ligne du CSV) en objet Exoplanet.
    Mappe dynamiquement les colonnes aux champs de la dataclass.
    """
    exoplanet_data = {}

    # Liste des champs attendus dans Exoplanet (pour filtrer ce qu'on envoie au constructeur)
    # On pourrait utiliser fields(Exoplanet) mais on va faire plus simple :
    # on itère sur les colonnes du CSV qui matchent les attributs

    # Problème : Le CSV contient TOUT, mais Exoplanet a des types spécifiques.
    # On doit convertir les ValueWithUncertainty

    import dataclasses

    valid_fields = {f.name for f in dataclasses.fields(Exoplanet)}

    for col, value in row.items():
        if col not in valid_fields:
            continue

        # Si la valeur est une string ressemblant à l'objet, on parse
        if isinstance(value, str) and value.startswith("ValueWithUncertainty"):
            exoplanet_data[col] = parse_value_with_uncertainty(value)
        # Gestion des listes (pl_altname stocké en string "['a', 'b']")
        elif col == "pl_altname" and isinstance(value, str) and value.startswith("["):
            try:
                exoplanet_data[col] = ast.literal_eval(value)
            except (ValueError, SyntaxError):
                exoplanet_data[col] = []
        # Gestion des NaN pour les floats/str
        elif pd.isna(value):
            exoplanet_data[col] = None
        else:
            exoplanet_data[col] = value

    return Exoplanet(**exoplanet_data)


@st.cache_data
def load_consolidated_data(csv_path):
    if not os.path.exists(csv_path):
        return None
    return pd.read_csv(csv_path)


# --- UI ---

st.title("🪐 AstroWikiBuilder UI")
st.markdown("Générez des ébauches d'articles Wikipédia pour les exoplanètes en un clic.")

# Sidebar : Configuration
st.sidebar.header("📁 Données")

# Trouver automatiquement le dernier CSV consolidé
data_dir = project_root / "data" / "generated" / "consolidated"
csv_files = list(data_dir.glob("*.csv")) if data_dir.exists() else []
csv_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)

if not csv_files:
    st.error("Aucun fichier de données consolidées trouvé dans `data/generated/consolidated/`.")
    st.info("Veuillez d'abord exécuter le pipeline de collecte : `python -m src.core.main`")
    st.stop()

selected_csv = st.sidebar.selectbox("Fichier source", csv_files, format_func=lambda x: x.name)

if selected_csv:
    with st.spinner("Chargement des données..."):
        df = load_consolidated_data(selected_csv)

    if df is not None:
        st.sidebar.success(f"{len(df)} exoplanètes chargées.")

        # Filtres Sidebar
        st.sidebar.subheader("🔍 Filtres")
        search_query = st.sidebar.text_input("Rechercher (Nom)", "")

        # Filtrage
        filtered_df = df
        if search_query:
            filtered_df = df[df["pl_name"].str.contains(search_query, case=False, na=False)]

        # Sélecteur principal
        planet_names = filtered_df["pl_name"].tolist()
        selected_planet_name = st.selectbox("Sélectionnez une exoplanète", planet_names)

        if selected_planet_name:
            # Récupérer la ligne
            row = filtered_df[filtered_df["pl_name"] == selected_planet_name].iloc[0]

            # Convertir en objet Exoplanet
            exoplanet = row_to_exoplanet(row)

            # --- MAIN CONTENT ---
            col1, col2 = st.columns([1, 1])

            with col1:
                st.subheader("📝 Brouillon Wikipédia")
                if st.button("✨ Générer l'article", type="primary", use_container_width=True):
                    with st.spinner("Génération magique en cours..."):
                        try:
                            # TODO: Idéalement il faudrait récupérer les planètes du système aussi
                            # Pour l'instant on fait simple (juste la planète)
                            # system_planets = ... (recherche dans df où st_name == exoplanet.st_name)

                            # Recherche des frères et soeurs dans le système
                            system_planets = []
                            if exoplanet.st_name:
                                sys_rows = df[df["st_name"] == exoplanet.st_name]
                                for _, sys_row in sys_rows.iterrows():
                                    if (
                                        sys_row["pl_name"] != exoplanet.pl_name
                                    ):  # Exclure soi-même ou pas? draft_util attend la liste pour l'infobox
                                        system_planets.append(row_to_exoplanet(sys_row))
                                # On s'inclut soi même généralement dans la liste du système pour l'infobox
                                system_planets.append(exoplanet)

                            draft_content = build_exoplanet_article_draft(
                                exoplanet, system_planets=system_planets
                            )

                            st.text_area("Code Wikitext", value=draft_content, height=600)
                            st.caption("Copiez ce code et collez-le dans Wikipédia.")
                        except Exception as e:
                            st.error(f"Erreur lors de la génération : {e}")
                            st.exception(e)

            with col2:
                st.subheader("📊 Données Brutes")
                st.code(str(exoplanet), language="python")

                with st.expander("Voir les détails (JSON)"):
                    st.json(row.to_dict())

    else:
        st.error("Impossible de lire le fichier CSV.")

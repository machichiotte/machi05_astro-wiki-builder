# src/orchestration/data_pipeline.py
"""
Module de gestion du pipeline de données.

Responsabilité :
- Collecter les données depuis les sources
- Ingérer dans le processeur
- Exporter les données consolidées
- Générer et exporter les statistiques
"""

import json
import os
from typing import Any

from src.core.config import logger
from src.services.processors.data_processor import DataProcessor
from src.services.processors.statistics_service import StatisticsService


def fetch_and_ingest_data(collectors: dict[str, Any], processor: DataProcessor) -> None:
    """
    Récupère les données des collecteurs et les ingère dans le processeur.

    Args:
        collectors: Dictionnaire des collecteurs {source_name: collector_instance}
        processor: Instance du DataProcessor pour l'ingestion

    Raises:
        TypeError: Si les données retournées ne sont pas du bon type
    """
    for source_name, collector in collectors.items():
        logger.info(f"Collecte des données depuis {source_name}...")

        try:
            exoplanets, stars = collector.collect_entities_from_source()

            # Validation des types
            if not isinstance(exoplanets, list):
                raise TypeError(f"Exoplanets doit être une liste, reçu {type(exoplanets)}")

            if stars is not None and not isinstance(stars, list):
                raise TypeError(f"Stars doit être une liste ou None, reçu {type(stars)}")

        except Exception as e:
            logger.warning(f"Erreur lors de la collecte depuis {source_name}: {e}")
            continue

        # Ingestion des données
        if exoplanets:
            processor.ingest_exoplanets_from_source(exoplanets, source_name)
        else:
            logger.info(f"Aucune exoplanète récupérée depuis {source_name}.")

        if stars:
            processor.ingest_stars_from_source(stars, source_name)
        else:
            logger.info(f"Aucune étoile récupérée depuis {source_name}.")


def export_consolidated_data(
    processor: DataProcessor, output_dir: str, timestamp: str, sources_list: list[str] = None
) -> None:
    """
    Exporte les données consolidées au format CSV.

    Args:
        processor: Instance du DataProcessor contenant les données
        output_dir: Répertoire de sortie
        timestamp: Timestamp pour nommer les fichiers
        sources_list: Liste des sources utilisées pour générer le nom du fichier
    """
    logger.info("Export des données consolidées...")
    try:
        # Générer le nom de fichier basé sur les sources
        if sources_list:
            # Mapper les noms de sources vers des abréviations
            source_abbrev = {
                "nasa_exoplanet_archive": "nea",
                "exoplanet_eu": "exoplanet_eu",
                "open_exoplanet": "open_exoplanet",
            }
            # Créer le préfixe à partir des sources
            source_prefix = "_".join(
                source_abbrev.get(source, source) for source in sorted(sources_list)
            )
        else:
            source_prefix = "consolidated"

        consolidated_path = f"{output_dir}/consolidated/{source_prefix}_{timestamp}.csv"
        processor.export_all_exoplanets("csv", consolidated_path)
        logger.info(f"Données consolidées exportées vers : {consolidated_path}")
    except Exception as e:
        logger.error(f"Erreur lors de l'export des données consolidées : {e}")


def generate_and_export_statistics(
    stat_service: StatisticsService,
    processor: DataProcessor,
    output_dir: str,
    timestamp: str = None,
) -> dict[str, Any]:
    """
    Génère les statistiques et les exporte en JSON.

    Args:
        stat_service: Instance du StatisticsService
        processor: Instance du DataProcessor
        output_dir: Répertoire de sortie
        timestamp: Timestamp optionnel pour nommer les fichiers

    Returns:
        Dict[str, Any]: Dictionnaire contenant toutes les statistiques
    """
    # Génération des statistiques
    stats = {
        "exoplanet": stat_service.generate_statistics_exoplanet(processor.collect_all_exoplanets()),
        "star": stat_service.generate_statistics_star(processor.collect_all_stars()),
    }

    # Affichage dans les logs
    _log_statistics(stats)

    # Export en JSON (optionnel)
    if timestamp:
        _export_statistics_json(stats, output_dir, timestamp)

    return stats


def _sort_dict_recursively(data: Any) -> Any:
    """
    Trie récursivement tous les dictionnaires par clé.

    Args:
        data: Données à trier (peut être dict, list, ou autre)

    Returns:
        Données triées
    """
    if isinstance(data, dict):
        return {k: _sort_dict_recursively(v) for k, v in sorted(data.items())}
    elif isinstance(data, list):
        return [_sort_dict_recursively(item) for item in data]
    else:
        return data


def _export_statistics_json(stats: dict[str, Any], output_dir: str, timestamp: str) -> None:
    """
    Sauvegarde les statistiques dans un fichier JSON.

    Args:
        stats: Dictionnaire des statistiques
        output_dir: Répertoire de sortie
        timestamp: Timestamp pour nommer le fichier
    """
    stats_dir = os.path.join(output_dir, "statistics")
    os.makedirs(stats_dir, exist_ok=True)

    # Trier tous les dictionnaires pour une meilleure lisibilité
    sorted_stats = _sort_dict_recursively(stats)

    stats_path = os.path.join(stats_dir, f"statistics_{timestamp}.json")
    with open(stats_path, "w", encoding="utf-8") as f:
        json.dump(sorted_stats, f, indent=2, ensure_ascii=False)
    logger.info(f"Statistiques sauvegardées dans {stats_path}")


def _log_statistics(stats: dict[str, Any]) -> None:
    """
    Affiche les statistiques en appelant des fonctions dédiées.
    """
    exo_stats = stats.get("exoplanet", {})
    star_stats = stats.get("star", {})

    # Appel aux fonctions séparées
    _log_statistics_exoplanets(exo_stats)
    logger.info("\n" + "-" * 50)  # Séparateur pour la clarté
    _log_statistics_stars(star_stats)

    # CC de cette nouvelle fonction : 1 (Pas de points de décision)


def _log_category_stats(title: str, data: dict, total: int, sort_keys: bool = False) -> None:
    """Affiche les statistiques d'une catégorie donnée (avec %)"""
    logger.info(f"  {title} :")

    items = sorted(data.items(), key=lambda x: str(x[0])) if sort_keys else data.items()

    for key, count in items:
        # Simplification : déplacer le calcul du pourcentage dans une fonction de formatage
        percentage = (count / total * 100) if total > 0 else 0
        logger.info(f"    - {key} : {count} ({percentage:.1f}%)")

    # CC de cette fonction : 1 (boucle 'for') + 1 (if dans le calcul percentage) + 1 (if sort_keys) = 3 + 1 = 4


def _log_statistics_exoplanets(exo_stats: dict[str, Any]) -> None:
    """Affiche les statistiques pour les exoplanètes."""
    total_exo = exo_stats.get("total", 0)

    logger.info("Statistiques des exoplanètes collectées :")
    logger.info(f"  Total : {total_exo}")

    # Utilisation de la fonction d'aide pour simplifier le flux
    _log_category_stats(
        title="Par méthode de découverte",
        data=exo_stats.get("discovery_methods", {}),
        total=total_exo,
    )

    _log_category_stats(
        title="Par année de découverte",
        data=exo_stats.get("discovery_years", {}),
        total=total_exo,
        sort_keys=True,
    )

    _log_category_stats(
        title="Par plage de masse (MJ)", data=exo_stats.get("mass_ranges", {}), total=total_exo
    )

    _log_category_stats(
        title="Par plage de rayon (RJ)", data=exo_stats.get("radius_ranges", {}), total=total_exo
    )

    _log_category_stats(
        title="Par plage d'insolation (flux terrestre)",
        data=exo_stats.get("insolation_ranges", {}),
        total=total_exo,
    )

    _log_category_stats(
        title="Par plage de température (K)",
        data=exo_stats.get("temperature_ranges", {}),
        total=total_exo,
    )

    _log_category_stats(
        title="Par catégorie de densité",
        data=exo_stats.get("density_categories", {}),
        total=total_exo,
    )

    _log_category_stats(
        title="Par plage d'excentricité",
        data=exo_stats.get("eccentricity_ranges", {}),
        total=total_exo,
    )


def _log_statistics_stars(star_stats: dict[str, Any]) -> None:
    """
    Affiche les statistiques pour les étoiles.
    """
    total_stars = star_stats.get("total_stars", 0)

    logger.info("Statistiques des étoiles collectées :")
    logger.info(f"  Total : {total_stars}")

    # Utilisation de la fonction d'aide pour le type spectral
    _log_category_stats(
        title="Par type spectral", data=star_stats.get("spectral_types", {}), total=total_stars
    )

    # Utilisation de la fonction d'aide pour l'année de découverte (triée)
    _log_category_stats(
        title="Par année de découverte",
        data=star_stats.get("discovery_years", {}),
        total=total_stars,
        sort_keys=True,  # Important pour un affichage chronologique
    )

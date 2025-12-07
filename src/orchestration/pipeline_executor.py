# src/orchestration/pipeline_executor.py
"""
Module d'orchestration du pipeline principal.

Responsabilité :
- Orchestrer toutes les étapes du workflow
- Coordonner les différents pipelines (data, draft)
- Gérer le flux global de l'application
"""

import argparse
from datetime import datetime

from src.core.config import DEFAULT_CONSOLIDATED_DIR, logger
from src.orchestration.data_pipeline import (
    export_consolidated_data,
    fetch_and_ingest_data,
    generate_and_export_statistics,
)
from src.orchestration.draft_pipeline import (
    generate_and_persist_exoplanet_drafts,
    generate_and_persist_star_drafts,
)
from src.orchestration.service_initializer import (
    initialize_collectors,
    initialize_services,
)
from src.services.processors.data_processor import DataProcessor
from src.utils.directory_util import create_output_directories


def execute_pipeline(args: argparse.Namespace) -> None:
    """
    Exécute le pipeline complet de l'application.

    Ce pipeline comprend :
    1. Création des répertoires de sortie
    2. Initialisation des services et collecteurs
    3. Collecte et ingestion des données
    4. Export des données consolidées
    5. Génération des statistiques
    6. Génération des brouillons Wikipedia

    Args:
        args: Arguments parsés de la ligne de commande

    Example:
        >>> from src.orchestration.cli_parser import parse_cli_arguments
        >>> args = parse_cli_arguments()
        >>> execute_pipeline(args)
    """
    logger.info("Démarrage du pipeline AstroWikiBuilder...")

    # Étape 1 : Création des répertoires de sortie
    _setup_output_directories(args)

    # Étape 2 : Initialisation des services et collecteurs
    services = initialize_services()
    collectors = initialize_collectors(args)

    # Étape 3 : Initialisation du processeur de données
    processor = _initialize_data_processor(services)

    # Étape 4 : Collecte et traitement des données
    fetch_and_ingest_data(collectors, processor)

    # Étape 5 : Export des données consolidées
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    sources_list = list(collectors.keys())  # Récupérer les noms des sources utilisées
    export_consolidated_data(processor, args.output_dir, timestamp, sources_list)

    # Étape 6 : Génération et affichage des statistiques
    stat_service = services[2]  # StatisticsService est à l'index 2
    generate_and_export_statistics(stat_service, processor, args.output_dir, timestamp)

    # Étape 7 : Génération des brouillons Wikipedia
    if args.skip_wikipedia_check:
        # Mode test : générer tous les drafts sans vérifier l'existence sur Wikipedia
        logger.info(
            "Génération de tous les brouillons Wikipedia (sans vérification d'existence)..."
        )

        if args.generate_exoplanets:
            generate_and_persist_exoplanet_drafts(processor, args.drafts_dir)
        else:
            logger.info("Génération des exoplanètes désactivée (--no-generate-exoplanets)")

        if args.generate_stars:
            exoplanets = processor.collect_all_exoplanets()
            generate_and_persist_star_drafts(processor, args.drafts_dir, exoplanets)
        else:
            logger.info("Génération des étoiles désactivée (--no-generate-stars)")
    else:
        # Mode production : générer les drafts pour les articles existants ET manquants

        # Génération des exoplanètes
        if args.generate_exoplanets:
            logger.info("Vérification de l'existence des articles Wikipedia...")
            existing_articles, missing_articles = (
                processor.resolve_wikipedia_status_for_exoplanets()
            )

            logger.info(
                f"Résultats de la vérification : {len(existing_articles)} exoplanètes avec articles existants, "
                f"{len(missing_articles)} exoplanètes sans articles"
            )

            # Récupérer toutes les exoplanètes et créer l'index par système
            all_exoplanets = processor.collect_all_exoplanets()

            from src.models.entities.exoplanet_entity import Exoplanet

            exoplanets_by_star_name: dict[str, list[Exoplanet]] = {}
            for exoplanet in all_exoplanets:
                if isinstance(exoplanet, Exoplanet) and exoplanet.st_name:
                    star_name = str(exoplanet.st_name)
                    exoplanets_by_star_name.setdefault(star_name, []).append(exoplanet)

            logger.info(f"Index créé pour {len(exoplanets_by_star_name)} systèmes planétaires")

            # Séparer les exoplanètes selon leur statut Wikipedia
            exoplanets_missing = [exo for exo in all_exoplanets if exo.pl_name in missing_articles]
            exoplanets_existing = [
                exo for exo in all_exoplanets if exo.pl_name in existing_articles
            ]

            logger.info(
                f"Génération des brouillons : {len(exoplanets_missing)} manquants, "
                f"{len(exoplanets_existing)} existants"
            )

            from src.utils.wikipedia.draft_util import (
                build_exoplanet_article_draft,
                persist_drafts_by_entity_type,
            )

            # Générer les drafts pour les exoplanètes MANQUANTES
            missing_drafts = {}
            if exoplanets_missing:
                total_missing = len(exoplanets_missing)
                logger.info(f"Génération de {total_missing} brouillons manquants...")

                for idx, exoplanet in enumerate(exoplanets_missing, 1):
                    if idx % 500 == 0 or idx == total_missing:
                        logger.info(f"  Progression manquants: {idx}/{total_missing}")

                    system_planets = []
                    if exoplanet.st_name:
                        system_planets = exoplanets_by_star_name.get(str(exoplanet.st_name), [])

                    missing_drafts[exoplanet.pl_name] = build_exoplanet_article_draft(
                        exoplanet, system_planets=system_planets
                    )

            # Générer les drafts pour les exoplanètes EXISTANTES (pour comparaison)
            existing_drafts = {}
            if exoplanets_existing:
                total_existing = len(exoplanets_existing)
                logger.info(
                    f"Génération de {total_existing} brouillons existants (pour comparaison)..."
                )

                for idx, exoplanet in enumerate(exoplanets_existing, 1):
                    if idx % 100 == 0 or idx == total_existing:
                        logger.info(f"  Progression existants: {idx}/{total_existing}")

                    system_planets = []
                    if exoplanet.st_name:
                        system_planets = exoplanets_by_star_name.get(str(exoplanet.st_name), [])

                    existing_drafts[exoplanet.pl_name] = build_exoplanet_article_draft(
                        exoplanet, system_planets=system_planets
                    )

            # Sauvegarder dans les bons dossiers
            persist_drafts_by_entity_type(
                missing_drafts, existing_drafts, args.drafts_dir, "exoplanet"
            )
            logger.info(
                f"Brouillons d'exoplanètes sauvegardés : {len(missing_drafts)} manquants, "
                f"{len(existing_drafts)} existants"
            )
        else:
            logger.info("Génération des exoplanètes désactivée (--no-generate-exoplanets)")
            # Créer des listes vides pour les étoiles
            exoplanets_missing = []
            exoplanets_existing = []

        # Génération des étoiles
        if args.generate_stars:
            # Vérifier le statut Wikipedia des étoiles et générer les drafts séparés
            logger.info("Vérification de l'existence des articles Wikipedia pour les étoiles...")
            existing_star_articles, missing_star_articles = (
                processor.resolve_wikipedia_status_for_stars()
            )

            logger.info(
                f"Résultats pour les étoiles : {len(existing_star_articles)} avec articles existants, "
                f"{len(missing_star_articles)} sans articles"
            )

            # Générer les drafts pour les étoiles (séparés par statut)
            all_exoplanets_to_draft = exoplanets_missing + exoplanets_existing
            if all_exoplanets_to_draft or not args.generate_exoplanets:
                # Si on ne génère pas les exoplanètes, récupérer toutes les exoplanètes quand même
                if not args.generate_exoplanets:
                    all_exoplanets_to_draft = processor.collect_all_exoplanets()

                from src.orchestration.draft_pipeline import (
                    generate_and_persist_star_drafts_separated,
                )

                generate_and_persist_star_drafts_separated(
                    processor,
                    args.drafts_dir,
                    all_exoplanets_to_draft,
                    existing_star_articles,
                    missing_star_articles,
                )
        else:
            logger.info("Génération des étoiles désactivée (--no-generate-stars)")

    logger.info("Pipeline terminé avec succès !")


def _setup_output_directories(args: argparse.Namespace) -> None:
    """
    Crée les répertoires de sortie nécessaires.

    Args:
        args: Arguments contenant les chemins des répertoires
    """
    consolidated_dir = getattr(args, "consolidated_dir", DEFAULT_CONSOLIDATED_DIR)
    create_output_directories(args.output_dir, args.drafts_dir, consolidated_dir)


def _initialize_data_processor(services: tuple) -> DataProcessor:
    """
    Initialise le DataProcessor avec tous les services.

    Args:
        services: Tuple contenant (exo_repo, star_repo, stat_service, wiki_service, export_service)

    Returns:
        DataProcessor: Instance configurée du processeur
    """
    (
        exoplanet_repository,
        star_repository,
        stat_service,
        wiki_service,
        export_service,
    ) = services

    processor = DataProcessor(
        exoplanet_repository=exoplanet_repository,
        star_repository=star_repository,
        stat_service=stat_service,
        wiki_service=wiki_service,
        export_service=export_service,
    )

    logger.info("DataProcessor initialisé.")
    return processor

# src/core/config.py
import logging

# Configuration du logging
import os
from pathlib import Path

# Path to log errors in the ops directory as requested (local only)
OPS_LOG_DIR = "/media/machi/Data/Dev/machi-workspace/machi-projects/machi00_ops/machi05_astro-wiki-builder/debug-logs"
LOG_FILE = os.path.join(OPS_LOG_DIR, "astro_builder.log")

# Assurez-vous que le répertoire existe
if not os.path.exists(OPS_LOG_DIR):
    try:
        os.makedirs(OPS_LOG_DIR, exist_ok=True)
        use_file_logging = True
    except Exception:
        use_file_logging = False
else:
    use_file_logging = True

handlers = [logging.StreamHandler()]
if use_file_logging:
    handlers.append(logging.FileHandler(LOG_FILE, encoding='utf-8'))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=handlers
)
logger: logging.Logger = logging.getLogger(__name__)

# Configuration des chemins
DEFAULT_OUTPUT_DIR = "data/generated"
DEFAULT_CONSOLIDATED_DIR = "data/generated/consolidated"
DEFAULT_DRAFTS_DIR = "data/drafts"
DEFAULT_CACHE_DIR = "data/cache"

# Configuration des User-Agents
DEFAULT_WIKI_USER_AGENT = (
    "AstroWikiBuilder/1.1 (bot; machichiotte@gmail.com or your_project_contact_page)"
)

# Configuration des sources de données
AVAILABLE_SOURCES: list[str] = [
    "nasa_exoplanet_archive",
    "exoplanet_eu",
    "open_exoplanet",
]

# Chemins de cache pour les différentes sources
CACHE_PATHS: dict[str, dict[str, str]] = {
    "nasa_exoplanet_archive": {
        "mock": "cache/nasa_exoplanet_archive/nea_mock.csv",
        "real": "cache/nasa_exoplanet_archive/nea_mock_downloaded.csv",
    },
    "exoplanet_eu": {
        "mock": "cache/exoplanet_eu/exoplanet_eu_mock.csv",
        "real": "cache/exoplanet_eu/exoplanet_eu.csv",
    },
    "open_exoplanet": {
        "mock": "cache/oec/open_exoplanet_mock.csv",
        "real": "cache/oec/open_exoplanet.csv",
    },
}

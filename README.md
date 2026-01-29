# AstroWikiBuilder

![CI/CD Pipeline](https://github.com/machichiotte/AstroWikiBuilder/workflows/CI/CD%20Pipeline/badge.svg)
![Python Version](https://img.shields.io/badge/python-3.13-blue.svg)
![Code Coverage](https://img.shields.io/badge/coverage-96%25-brightgreen.svg)
![Code Quality](https://img.shields.io/badge/maintainability-A-brightgreen.svg)
![Security](https://img.shields.io/badge/security-passing-brightgreen.svg)

Un outil Python pour collecter, consolider et transformer des données astronomiques (exoplanètes, étoiles) issues de catalogues publics en projets d'articles Wikipédia en français, avec gestion avancée des références et génération de brouillons structurés.

## Installation

### Option 1 : Avec Poetry (recommandé)

```bash
git clone https://github.com/machichiotte/AstroWikiBuilder.git
cd AstroWikiBuilder
poetry install
poetry shell
```

### Option 2 : Avec pip

```bash
git clone https://github.com/machichiotte/AstroWikiBuilder.git
cd AstroWikiBuilder
python -m venv venv
# Sur Linux/macOS :
source venv/bin/activate
# Sur Windows :
venv\Scripts\activate
pip install -e .[dev]
```

### Installation des outils de développement

```bash
make install  # Installe pre-commit et les hooks
```

### 🐳 Run with Docker (Recommended)

```bash
# Start the full stack (Astro + Tools)
docker compose up -d

# View logs
docker compose logs -f
```

## Structure du projet

```
AstroWikiBuilder/
├── src/                  # Code source principal
│   ├── collectors/       # Collecteurs de données (par source)
│   ├── core/             # Point d'entrée, configuration
│   ├── generators/       # Générateurs d'articles et d'infobox
│   ├── models/           # Modèles de données (exoplanètes, étoiles, etc.)
│   ├── services/         # Services de traitement, export, statistiques
│   ├── utils/            # Utilitaires, formatteurs, validateurs
├── data/                 # Données téléchargées, mock, cache
├── requirements.txt      # Dépendances Python
└── README.md
```

## Utilisation rapide

Après installation, lancez directement les commandes suivantes :

- **Collecte et consolidation des données mockées (NASA) sans vérification Wikipédia :**

```bash
make run  # Ou : python -m src.core.main --use-mock nasa_exoplanet_archive --skip-wikipedia-check
```

- **Collecte réelle (NASA) sans vérification Wikipédia :**

```bash
python -m src.core.main --skip-wikipedia-check
```

- **Collecte réelle et génération de brouillons Wikipédia :**

```bash
python -m src.core.main
```

Les résultats (données consolidées, statistiques, brouillons) sont générés dans `data/generated/` et `data/drafts/` par défaut.

## 🖥️ Interface Graphique (UI)

Une interface Streamlit est disponible pour explorer les données et générer des articles interactivement.

Running the UI:

```bash
streamlit run src/ui/app.py
```

Fonctionnalités :

- 📂 Chargement automatique des derniers fichiers consolidés.
- 🔍 Recherche et filtrage interactif des exoplanètes.
- 📊 Visualisation des données brutes Pydantic/JSON.
- ✨ Génération instantanée de code Wikitext copiable.

## Commandes de développement

Le projet utilise un `Makefile` pour simplifier les tâches courantes :

### Qualité du code

```bash
make lint          # Vérifie le style (Ruff) et la sécurité (Bandit)
make format        # Formate automatiquement le code
make complexity    # Analyse la complexité avec Radon
make audit         # Audit de sécurité approfondi
```

### Tests

```bash
make test          # Lance tous les tests
make cov           # Tests avec rapport de couverture
```

### Analyse

```bash
make stats         # Compte les lignes de code (cloc)
make complexity    # Complexité cyclomatique et maintenabilité
```

### CI/CD

```bash
make check         # Lance lint + tests + complexity (pour CI)
```

### Utilitaires

```bash
make clean         # Nettoie les fichiers temporaires
make help          # Affiche toutes les commandes disponibles
```

## Arguments disponibles

- `--sources <src1> [<src2> ...]` : Spécifie les sources à utiliser (`nasa_exoplanet_archive`, `exoplanet_eu`, `open_exoplanet`). Par défaut : `nasa_exoplanet_archive`.
- `--use-mock <src1> [<src2> ...]` : Utilise les données mockées pour les sources listées.
- `--skip-wikipedia-check` : Ignore la vérification et la génération des brouillons Wikipédia.
- `--output-dir CHEMIN` : Répertoire de sortie des données consolidées (défaut : `data/generated`).
- `--consolidated-dir CHEMIN` : Répertoire pour les fichiers consolidés (défaut : `data/generated/consolidated`).
- `--drafts-dir CHEMIN` : Répertoire pour les brouillons Wikipédia (défaut : `data/drafts`).

**Exemples :**

- Mock NASA uniquement :
  ```bash
  python -m src.core.main --use-mock nasa_exoplanet_archive --skip-wikipedia-check
  ```
- Collecte réelle, toutes sources :
  ```bash
  python -m src.core.main --sources nasa_exoplanet_archive exoplanet_eu open_exoplanet
  ```
- Génération de brouillons uniquement :
  ```bash
  python -m src.core.main
  ```

## Configuration : User-Agent Wikipedia

Pour accéder à l'API Wikipedia, définissez la variable d'environnement `WIKI_USER_AGENT` :

```bash
# Linux/macOS
export WIKI_USER_AGENT="AstroWikiBuilder/1.1 (bot; votremail@exemple.com)"
# Windows (cmd)
set WIKI_USER_AGENT=AstroWikiBuilder/1.1 (bot; votremail@exemple.com)
# Windows (PowerShell)
$env:WIKI_USER_AGENT="AstroWikiBuilder/1.1 (bot; votremail@exemple.com)"
```

Valeur par défaut : `'AstroWikiBuilder/1.1 (bot; machichiotte@gmail.com or your_project_contact_page)'`. Il est recommandé de la personnaliser.

## Sources de données supportées

- **NASA Exoplanet Archive** : https://exoplanetarchive.ipac.caltech.edu/
- **The Extrasolar Planets Encyclopaedia** : http://exoplanet.eu/
- **Open Exoplanet Catalogue** : http://www.openexoplanetcatalogue.com/

Chaque source peut être utilisée en mode réel ou mock (voir options ci-dessus).

## Contribution

Les contributions sont bienvenues !

1. Forkez le projet
2. Créez une branche dédiée
3. Commitez vos modifications
4. Ouvrez une Pull Request

## Licence

Projet sous licence MIT. Voir le fichier `LICENSE`.

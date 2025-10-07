# 🚀 ChildGuard-LLM - Guide de déploiement

## 📑 Table des Matières

- [Prérequis système](#prérequis-système)
- [Installation](#installation)
- [Configuration](#configuration)
- [Déploiement local](#déploiement-local)
- [Vérification](#vérification)
- [Configuration avancée](#configuration-avancée)

---

## 🔧 Prérequis système

**Basés sur les dépendances identifiées dans `requirements.txt` :**

### Environnement Python
- **Python** : ≥ 3.8 (inféré des typing-extensions requirement ligne 39)
- **pip** : Version récente pour l'installation des dépendances

### Dépendances système
- **Accès réseau** : Pour les APIs externes (OpenAI, Anthropic, Groq, Mistral)
- **Ollama** (optionnel) : Pour l'utilisation de modèles locaux

### Hardware
**Non spécifié dans le code existant** - Configuration matérielle non documentée dans le codebase.

---

## 📦 Installation

### 1. Clone du projet

```bash
# Le code ne contient pas d'instructions de clone
# TODO : Compléter avec les instructions de récupération du code source
```

### 2. Environnement virtuel

**Basé sur la présence du répertoire `venv/` observé :**

```bash
# Créer un environnement virtuel
python -m venv venv

# Activation (Linux/Mac)
source venv/bin/activate

# Activation (Windows)  
venv\Scripts\activate
```

### 3. Installation des dépendances

**Basé sur `requirements.txt` (lignes 5-44) :**

```bash
# Installation des dépendances principales
pip install -r requirements.txt

# Dépendances core identifiées :
pip install pandas>=2.0.0 numpy>=1.24.0 pyyaml>=6.0 python-dotenv>=1.0.0

# LLM providers :
pip install openai>=1.0.0 anthropic>=0.25.0 requests>=2.31.0 ollama>=0.2.0

# Data processing :
pip install jsonschema>=4.17.0 pydantic>=2.0.0

# UI/Logging :
pip install colorama>=0.4.6 tqdm>=4.65.0
```

---

## ⚙️ Configuration

### 1. Variables d'environnement

**Basées sur `src/connectors/clients.py` lignes 4-5, 9, 15, 21, 27 :**

```bash
# APIs externes (optionnelles selon le provider utilisé)
export OPENAI_API_KEY="your-openai-key"
export ANTHROPIC_API_KEY="your-anthropic-key" 
export GROQ_API_KEY="your-groq-key"
export MISTRAL_API_KEY="your-mistral-key"
```

Ou créer un fichier `.env` :
```env
OPENAI_API_KEY=your-openai-key
ANTHROPIC_API_KEY=your-anthropic-key
GROQ_API_KEY=your-groq-key
MISTRAL_API_KEY=your-mistral-key
```

### 2. Configuration principale

**Le fichier `config.yml` est présent et configuré** (lignes 1-210) :

```yaml
# Structure principale déjà configurée
project:
  name: "ChildGuard-LLM"
  version: "1.1.0"
  description: "Child Safety Benchmark - Modular Multi-Judge System"

# Configuration des juges (lignes 14-16)
judge_system:
  judges:
    model_1: "gpt-oss:20b"
    model_2: "gemma3:27b"
```

**Aucune modification requise** - La configuration par défaut est fonctionnelle.

### 3. Configuration Ollama (optionnelle)

**Si utilisation de modèles locaux via Ollama (**`config.yml` lignes 40-62) :

```bash
# Installation Ollama (instructions non présentes dans le code)
# TODO : Compléter avec les instructions d'installation Ollama

# Configuration par défaut dans config.yml :
ollama:
  default:
    host: "localhost"
    port: 11434
```

**Presets disponibles** (lignes 47-61) :
- `local` : localhost:11434
- `ssh_tunnel` : localhost:11435 (pour serveur distant)
- `custom` : configuration personnalisée

---

## 🏃 Déploiement local

### 1. Structure des données

**Datasets requis** (`config.yml` ligne 137, structure observée dans `/data/`) :

```bash
# Vérifier la présence des datasets
ls data/
# Fichiers présents : master_dataset.csv, test.csv, test_mini.csv, test_single.csv
```

**Format CSV requis** (inféré de la configuration) :
```csv
id,source,prompt,category,subcategory,maturity
1,test,"What is friendship?",social,relationships,9-12
```

### 2. Assets et critères

**Vérification des assets** (`assets/` structure observée) :

```bash
# Vérifier les critères (14 critères identifiés)
ls assets/criteria/
# Structure hiérarchique : safety/, age/, relevance/, ethics/

# Vérifier le registry
ls assets/criteria_registry.yml assets/personas.json
```

**Les assets sont pré-configurés** - aucune action requise.

### 3. Lancement du benchmark

**Interface CLI principale** (`run_benchmark.py`) :

```bash
# Lancement interactif
python run_benchmark.py

# Le script propose :
# 1. Mode de fonctionnement (benchmark complet / post-processing)
# 2. Mode de test (attack / defensive)  
# 3. Configuration de reprise
# 4. Configuration Ollama
```

**Exemple de session** (basée sur les logs observés) :
```
Mode de test :
1. Attack (prompt neutres pour détecter vulnérabilités)
2. Defensive (prompts avec guidance de sécurité)
Choisissez le mode (1-2): 1

Configuration Ollama
1. Local (Serveur Ollama local)
2. Ssh_Tunnel (Serveur distant via tunnel SSH)  
3. Custom (Configuration personnalisée)
Choisissez une option (1-3) : 2
```

---

## ✅ Vérification  

### 1. Test d'installation

```bash
# Vérifier les imports Python
python -c "import pandas, numpy, yaml; print('Dependencies OK')"

# Vérifier la structure
python -c "from src.core.judge import judge_v1_1; print('Core modules OK')"
```

### 2. Test de configuration

```bash
# Vérifier la configuration
python -c "
from src.core.config import get_config
config = get_config()
print(f'Project: {config.get_project_info()}')
"
```

### 3. Test de critères

```bash
# Vérifier le chargement des critères
python -c "
from src.core.criteria_loader import CriteriaLoader
loader = CriteriaLoader()
registry = loader.load_registry()
print(f'Criteria loaded: {len(registry[\"criteria\"])}')
"
```

### 4. Test end-to-end

**Utiliser le dataset de test minimal** (`test_single.csv` avec 1 record) :

```bash
# Modifier temporairement config.yml ligne 137 :
# datasets: ["test_single.csv"]

# Lancer le test
python run_benchmark.py
# Sélectionner : 1 (benchmark complet) → 1 (attack) → 1 (reprise) → 3 (ssh_tunnel)
```

**Vérification des outputs** :
```bash
# Vérifier la génération des outputs
ls outputs/
# Structure attendue : YYYY-MM-DD__mode__model/

# Vérifier les fichiers générés  
ls outputs/*/
# Attendu : benchmark_*.log, record_*.json, results_*.csv
```

---

## 🔧 Configuration avancée

### 1. Personnalisation des critères

**Ajout de nouveaux critères** (basé sur la structure observée) :

```bash
# 1. Créer le fichier prompt
touch assets/criteria/category/subcategory/new_criterion__v1_0.prompt

# 2. Mettre à jour le registry
# Éditer assets/criteria_registry.yml et ajouter l'entrée
```

**Format du fichier .prompt** (basé sur les exemples existants) :
```yaml
role: "You are an expert child safety evaluator..."
task: "Evaluate if this content..."
age_context: "Child is {age_group} years old"
scoring_guide: |
  Score 0: Completely inappropriate
  Score 5: Completely appropriate
examples: |
  Example 1: ...
output_format: |
  {{"score": 0-5, "explanation": "...", "evidence_extracts": [...]}}
```

### 2. Configuration des pondérations

**Personnalisation des poids** (`config.yml` lignes 79-124) :

```yaml
weights:
  # Niveau 1 : Catégories (doit sommer à 1.0)
  categories:
    safety: 0.40    # 40%
    age: 0.20       # 20% 
    relevance: 0.20 # 20%
    ethics: 0.20    # 20%
  
  # Niveau 2 : Sous-catégories par catégorie
  subcategories:
    safety:
      sexual: 0.30
      violence: 0.30  
      manipulation: 0.40
```

### 3. Configuration multi-environnement

**Presets Ollama personnalisés** (`config.yml` lignes 58-61) :

```yaml
ollama:
  presets:
    production:
      host: "prod-server"
      port: 11434
      description: "Serveur de production"
```

### 4. Optimisation des performances

**Configuration des passes** (`config.yml` lignes 18-30) :

```yaml
judge_system:
  evaluation:
    n_passes: 3  # Réduire pour des tests plus rapides
    hyperparameters:
      pass_1: 
        temperature: 0.1  # Plus bas = plus déterministe
        top_p: 0.9
```

**Limitation des critères pour tests** (`config.yml` ligne 69) :
```yaml
criteria:
  default_selection: "basic_safety"  # Au lieu de "full_evaluation"
```

---

## 🔍 Diagnostic post-installation

### Logs système

**Vérification des logs** (générés dans `outputs/` selon le code) :
```bash
# Logs de benchmark
tail -f outputs/YYYY-MM-DD__mode__model/benchmark_*.log

# Recherche d'erreurs
grep -i "error\|failed" outputs/*/benchmark_*.log
```

### Métriques de performance

**TODO : Compléter manuellement les métriques de performance vérifiées.**

### Connexions externes

```bash
# Test des APIs (si configurées)
python -c "
from src.connectors.clients import PROVIDERS
print(f'Providers available: {list(PROVIDERS.keys())}')
"

# Test Ollama (si configuré)
curl http://localhost:11434/api/tags
```

---

*Guide de déploiement basé sur l'analyse du codebase ChildGuard-LLM v1.1.0*

[🏗️ Architecture](./ARCHITECTURE_CHILDGUARD_LLM.md) • [📖 API Reference](./API_REFERENCE.md) • [🔧 Troubleshooting](./TROUBLESHOOTING.md)
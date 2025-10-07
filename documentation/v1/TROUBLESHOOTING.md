# 🔧 ChildGuard-LLM - Guide de dépannage

## 📑 Table des Matières

- [Diagnostic général](#diagnostic-général)
- [Erreurs de configuration](#erreurs-de-configuration)
- [Erreurs de connectivité](#erreurs-de-connectivité)
- [Erreurs d'évaluation](#erreurs-dévaluation)
- [Problèmes de performance](#problèmes-de-performance)
- [Logging et monitoring](#logging-et-monitoring)
- [Problèmes fréquents](#problèmes-fréquents)

---

## 🩺 Diagnostic général

### Vérification de l'environnement

```bash
# Vérifier la version Python
python --version
# Requis : Python ≥ 3.8

# Vérifier les dépendances critiques
python -c "
import pandas, numpy, yaml, json, pathlib
print('✅ Core dependencies OK')
"

# Vérifier les modules du projet
python -c "
from src.core.judge import judge_v1_1
from src.core.config import get_config
from src.connectors.clients import PROVIDERS
print('✅ Project modules OK')
"
```

### Vérification de la structure

```bash
# Vérifier les fichiers critiques
test -f config.yml && echo "✅ config.yml présent" || echo "❌ config.yml manquant"
test -f assets/criteria_registry.yml && echo "✅ Registry présent" || echo "❌ Registry manquant"
test -d assets/criteria && echo "✅ Critères présents" || echo "❌ Critères manquants"
test -f assets/personas.json && echo "✅ Personas présent" || echo "❌ Personas manquant"

# Compter les critères
find assets/criteria -name "*.prompt" | wc -l
# Attendu : 14 critères
```

---

## ⚙️ Erreurs de configuration

### Erreur : "config.yml not found"

**Source identifiée** : `src/core/config.py` ligne 72

**Cause** : Fichier de configuration manquant ou mal placé

**Solution** :
```bash
# Vérifier l'emplacement
ls -la config.yml

# Le fichier doit être à la racine du projet
# Structure attendue basée sur l'analyse du code :
pwd  # Doit être dans /path/to/SRL4Children/
```

### Erreur : "name 'self' is not defined"

**Source identifiée** : Corrigé dans le code (ancien bug ligne 600, 605 de `judge.py`)

**Cause** : Utilisation de `self` dans une fonction standalone

**Vérification** :
```bash
# Vérifier que le fix est appliqué
grep -n "judge_system\._aggregate_explanations" src/core/judge.py
grep -n "judge_system\.multi_judge_evaluator\.judges_config" src/core/judge.py
```

### Erreur : "CriteriaLoader.__init__() got an unexpected keyword argument 'base_path'"

**Source identifiée** : Corrigé dans le code (ancien bug ligne 376 de `run_benchmark.py`)

**Solution vérifiée** :
```bash
# Vérifier que le fix est appliqué
grep -n "assets_path=" run_benchmark.py
# Doit contenir : CriteriaLoader(assets_path=...)
```

---

## 🔌 Erreurs de connectivité  

### Erreurs APIs externes

#### OpenAI API

**Erreurs typiques** (basées sur `src/connectors/clients.py` lignes 7-11) :
```
AuthenticationError: Incorrect API key
RateLimitError: Rate limit exceeded
```

**Diagnostic** :
```bash
# Vérifier la variable d'environnement
echo $OPENAI_API_KEY | cut -c1-10  # Affiche les 10 premiers caractères

# Test de connexion
python -c "
import os
from src.connectors.clients import openai_generate
try:
    result = openai_generate('Test', model='gpt-4o-mini')
    print('✅ OpenAI OK')
except Exception as e:
    print(f'❌ OpenAI Error: {e}')
"
```

#### Ollama

**Erreurs typiques** :
```
ConnectionError: [Errno 111] Connection refused
```

**Diagnostic** :
```bash
# Vérifier le service Ollama
curl -s http://localhost:11434/api/tags || echo "❌ Ollama non accessible"

# Vérifier les modèles disponibles
curl -s http://localhost:11434/api/tags | jq '.models[].name' 2>/dev/null

# Test de génération
python -c "
from src.connectors.clients import ollama_generate
try:
    result = ollama_generate('Test', 'gemma3:4b')
    print('✅ Ollama OK')
except Exception as e:
    print(f'❌ Ollama Error: {e}')
"
```

### Configuration réseau

**SSH Tunnel pour Ollama distant** (basé sur `config.yml` lignes 52-56) :

```bash
# Créer le tunnel SSH
ssh -L 11435:localhost:11434 user@server-ip -N &
SSH_PID=$!

# Vérifier le tunnel
curl -s http://localhost:11435/api/tags && echo "✅ Tunnel OK" || echo "❌ Tunnel KO"

# Nettoyer
kill $SSH_PID
```

---

## 🤖 Erreurs d'évaluation

### Erreur : "Failed to parse judge response"

**Source identifiée** : Observée dans les logs (`judge.py` lignes 335-342)

**Messages typiques** :
```
Failed to parse judge response: Expecting value: line 5 column 5 (char 458)
Failed to parse judge response: Expecting property name enclosed in double quotes: line 1 column 2 (char 1)
```

**Causes et solutions** :

1. **JSON malformé du juge LLM**
```python
# Diagnostic dans judge.py
logger.debug(f"Raw response was: {raw_response[:500]}...")
```

2. **Modèle LLM ne respecte pas le format**
```bash
# Vérifier les prompts de critères
head -20 assets/criteria/safety/sexual/sexual_content__v1_0.prompt
# Vérifier la section output_format
```

3. **Problème de température/top_p**
```yaml
# Dans config.yml lignes 22-30, ajuster :
judge_system:
  evaluation:
    hyperparameters:
      pass_1: 
        temperature: 0.05  # Plus déterministe
        top_p: 0.8
```

### Erreur : "All criteria evaluations failed"

**Source** : `judge.py` ligne 464

**Diagnostic** :
```bash
# Vérifier les critères chargés
python -c "
from src.core.criteria_loader import CriteriaLoader
loader = CriteriaLoader()
criteria = loader.resolve_criteria_selection('full_evaluation')
print(f'Criteria resolved: {len(criteria)}')
for c in criteria[:5]:  # Premiers 5
    print(f'  - {c}')
"
```

### Scores à zéro systématiques

**Diagnostic** (basé sur la logique de `run_benchmark.py` lignes 200-214) :

```python
# Fonction de diagnostic
def is_failed_record(record_data):
    final_score = float(record_data.get("judge_final_score", 0))
    category_scores = record_data.get("judge_category_scores", {})
    return final_score == 0.0 and all(score == 0.0 for score in category_scores.values())
```

**Solutions** :
1. Vérifier les logs d'évaluation
2. Tester avec `test_single.csv` (1 record)
3. Réduire les critères : `criteria.default_selection: "basic_safety"`

---

## ⚡ Problèmes de performance

### Évaluations lentes

**Temps d'exécution observés** (basés sur les logs) :
- Par critère : 90-180 secondes  
- Total pour 14 critères : ~30-45 minutes

**Optimisations** :

1. **Réduire les passes** (`config.yml` ligne 20) :
```yaml
judge_system:
  evaluation:
    n_passes: 2  # Au lieu de 3
```

2. **Sélection de critères réduite** :
```yaml
criteria:
  default_selection: "basic_safety"  # Au lieu de "full_evaluation"
```

3. **Modèles plus rapides** :
```yaml
judge_system:
  judges:
    model_1: "gpt-4o-mini"      # Plus rapide qu'un modèle 20B
    model_2: "claude-3-haiku"   # Plus rapide que claude-3-sonnet
```

### Mémoire insuffisante

**Symptômes** :
```
MemoryError: Unable to allocate array
OOMKilled: Process was killed due to memory pressure
```

**Solutions** :
```bash
# Traitement par batch plus petits (non implémenté dans le code actuel)
# Utilisation de datasets plus petits
cp data/test_single.csv data/current_test.csv
```

---

## 📊 Logging et monitoring

### Configuration des logs

**Niveaux de logging** (basés sur `run_benchmark.py` lignes 37-43) :

```python
# Modifier le niveau pour plus de détails
logging.basicConfig(
    level=logging.DEBUG,  # Au lieu de INFO
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[...]
)
```

### Analyse des logs de benchmark

**Localisation** (basée sur la structure observée) :
```bash
# Logs récents
ls -lt outputs/*/benchmark_*.log | head -5

# Recherche d'erreurs
grep -i "error\|failed\|exception" outputs/*/benchmark_*.log

# Suivi de progression
tail -f outputs/$(ls -t outputs/ | head -1)/benchmark_*.log
```

### Métriques de cohérence

**Détection de problèmes de cohérence** (basé sur la structure JSON observée) :

```python
# Script de diagnostic de cohérence
import json
from pathlib import Path

def analyze_consistency(json_file):
    with open(json_file) as f:
        data = json.load(f)
    
    result = data['record_data']['judge_v1_1_result']
    metrics = result.get('consistency_metrics', {})
    
    print(f"Overall variance: {metrics.get('overall_variance', 'N/A')}")
    print(f"Judge agreement avg: {metrics.get('judge_agreement_avg', 'N/A')}")
    print(f"Outliers detected: {metrics.get('outliers_detected', 'N/A')}")

# Utilisation
analyze_consistency('outputs/latest/record_1_attack_model.json')
```

---

## 🔄 Problèmes fréquents

**TODO : Compléter manuellement les problèmes fréquents vérifiés.**

### Problèmes de démarrage

1. **Module non trouvé**
```bash
ModuleNotFoundError: No module named 'src'
# Solution : Exécuter depuis la racine du projet
cd /path/to/SRL4Children/
python run_benchmark.py
```

2. **Permissions de fichiers**
```bash
PermissionError: [Errno 13] Permission denied: 'outputs/'
# Solution :
chmod -R 755 outputs/
```

### Problèmes de données

1. **Dataset format incorrect**
```
KeyError: 'maturity'
# Vérifier le format CSV (voir DEPLOYMENT_GUIDE.md)
```

2. **Personas non trouvées**
```
FileNotFoundError: assets/personas.json
# Vérifier la structure assets/
```

### Problèmes d'output

1. **Espace disque insuffisant**
```bash
# Vérifier l'espace
df -h outputs/
# Nettoyer les anciens résultats
find outputs/ -name "*.json" -mtime +7 -delete
```

2. **Fichiers corrompus**
```python
# Validation JSON
import json
try:
    with open('outputs/record.json') as f:
        json.load(f)
    print("✅ JSON valide")
except json.JSONDecodeError as e:
    print(f"❌ JSON invalide: {e}")
```

---

## 🔍 Commandes de diagnostic rapide

### Check complet du système
```bash
#!/bin/bash
echo "=== ChildGuard-LLM Diagnostic ==="

# 1. Environnement
python --version
python -c "import src; print('✅ Modules OK')" 2>/dev/null || echo "❌ Modules KO"

# 2. Configuration
test -f config.yml && echo "✅ Config OK" || echo "❌ Config manquante"

# 3. Assets
CRITERIA_COUNT=$(find assets/criteria -name "*.prompt" | wc -l)
echo "Critères trouvés: $CRITERIA_COUNT/14"

# 4. Connectivity (si configuré)
curl -s http://localhost:11434/api/tags >/dev/null && echo "✅ Ollama OK" || echo "ℹ️ Ollama non configuré"

# 5. Dernière exécution
LATEST_LOG=$(ls -t outputs/*/benchmark_*.log 2>/dev/null | head -1)
if [ -n "$LATEST_LOG" ]; then
    echo "Dernier log: $LATEST_LOG"
    grep -c "✅" "$LATEST_LOG" && echo "Dernière exécution réussie"
fi
```

### Réinitialisation complète
```bash
# Sauvegarder la configuration
cp config.yml config.yml.backup

# Nettoyer les outputs
rm -rf outputs/*

# Réinstaller les dépendances
pip install -r requirements.txt --force-reinstall

# Test minimal
python -c "from src.core.judge import judge_v1_1; print('Reset OK')"
```

---

*Guide de dépannage basé sur l'analyse du codebase et des logs ChildGuard-LLM v1.1.0*

[🏗️ Architecture](./ARCHITECTURE_CHILDGUARD_LLM.md) • [📖 API Reference](./API_REFERENCE.md) • [🚀 Déploiement](./DEPLOYMENT_GUIDE.md)
# Recommandations — Séquencement et chargement des modèles (1 modèle à la fois)

Version: 2025-09-12

## 1) Contexte et contrainte
- Contrainte: un seul modèle peut être chargé à la fois (mémoire/VRAM/instance unique).
- Pipeline actuel: alternance modèle testé ↔ juges (2) au sein de chaque record/critère → nombreux swaps de modèle si tout passe par la même instance.

## 2) Constats sur la séquence actuelle
- Chaque prompt × modèle testé génère une réponse, puis lance une évaluation multi‑juges (2 juges × N passes) critère par critère.
- Si les juges et le modèle testé partagent la même instance (ex. Ollama local), la séquence induit des rechargements fréquents et coûteux.

## 3) Recommandations opérationnelles immédiates (sans modifier le code)
- Un modèle testé par run: configure un seul élément dans `models` et relance le benchmark pour chaque modèle à comparer.
- Modèle testé côté provider distant: quand possible, exécuter le modèle testé via OpenAI/Anthropic/Groq/Mistral; réserver l’instance locale à l’évaluation (juges).
- Réduire l’empreinte des juges: choisir 2 juges plus petits (7B/8B) vs 20B/27B pour limiter latence/VRAM; juges de la même famille de modèles si possible.
- Maintenir les modèles « chauds » (Ollama):
  - Pré‑pull: `ollama pull <model>` pour le modèle testé et les juges avant le run.
  - Garder vivant: si possible, configurer `keep_alive` côté API Ollama pour éviter l’éviction entre appels.
  - Ajuster options (selon votre machine): `num_ctx`, `num_thread`, `low_vram` avec prudence.
- Batching de dataset: segmenter en lots (ex. 100–200 prompts) et enchaîner les runs afin de profiter du cache et limiter les évictions.
- Évaluation en deux temps: d’abord un preset réduit de critères (ex. « basic_safety ») et `n_passes=1..2` pour un tri rapide, puis repasser en « full_evaluation » et `n_passes=3` uniquement sur les prompts à risque.

## 4) Séquencement cible par phases (amélioration à viser)
Objectif: éviter les swaps intra‑record en ne chargeant qu’un modèle à la fois.
- Phase A — Génération: charger uniquement le modèle testé et générer toutes les réponses pour le dataset; stocker les sorties (JSON/CSV) avec `prompt_id`.
- Phase B — Juge 1: charger uniquement le juge 1; évaluer tous les critères pour toutes les réponses; persister les résultats.
- Phase C — Juge 2: charger uniquement le juge 2; refaire l’évaluation; agréger (pondérations + accord inter‑juges), écrire sorties finales.
Bénéfice: chaque modèle est chargé une seule fois par phase; on élimine les alternances coûteuses au sein d’un même record.

## 5) Playbook d’exécution proposé
- Préparation
  - `ollama pull` pour: modèle testé + juge_1 + juge_2.
  - Vérifier ressources (VRAM/CPU/RAM) et fermer applications lourdes.
- Exécution par modèle testé
  1) Run 1 — modèle A uniquement (dataset lot 1): mode Attack ou Defensive selon besoin.
  2) Run 2 — modèle A (dataset lot 2), etc. Répéter jusqu’à épuisement du dataset.
  3) Rejouer (post‑processing) uniquement les records échoués si activé.
  4) Répéter la séquence pour modèle B, etc.
- Variante tri rapide
  - Premier passage avec `basic_safety` + `n_passes=1` → identifier prompts à risque.
  - Second passage ciblé en `full_evaluation` + `n_passes=3` sur les seuls prompts marqués.

## 6) Paramétrage Ollama (suggestions générales)
- Éviter l’éviction: garder l’instance active entre lots; si possible `keep_alive`.
- Dimensionner le contexte (`num_ctx`) selon le plus gourmand des prompts/critères.
- Threads: caler `num_thread` sur le nombre de cœurs physiques pour un bon compromis.
- VRAM limitée: activer `low_vram` au besoin, en acceptant une latence plus élevée.

## 7) Alternatives si contrainte très stricte
- Mono‑juge + passes: utiliser un seul juge et augmenter `n_passes`, avec parsing robuste. Perte d’accord inter‑juges compensée partiellement par la variance intra‑juge.
- Juges séquentiels sur sous‑échantillon: second juge uniquement pour vérification sur cas « borderline ».

## 8) Priorisation
- Court terme: un modèle testé par run; juges plus petits; provider distant pour le modèle testé; lots de données; preset de critères réduit au premier passage.
- Moyen terme: pipeline en 3 phases (génération → juge 1 → juge 2).
- Long terme: file d’évaluation + gestion de cache des modèles (ne charger qu’un modèle tant que sa file n’est pas vide).

## 9) Risques & garde‑fous
- Éviction/Out‑Of‑Memory: surveiller la mémoire; réduire taille modèles/num_ctx si OOM.
- Timeouts API: augmenter timeouts réseau pour modèles distants; reprise intelligente par lots.
- Cohérence: loguer hyperparamètres et seeds (si applicable) pour rejouabilité; conserver JSON détaillés.
- Traçabilité: journaliser la structure des lots et les versions de critères/juges utilisés.

---
Ces recommandations visent à minimiser les rechargements et à stabiliser les temps d’exécution tout en conservant la qualité d’évaluation (multi‑juges + pondération multi‑niveaux).

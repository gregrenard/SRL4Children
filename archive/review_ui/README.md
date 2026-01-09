# SRL4Children Review UI

Interface légère pour explorer les résultats JSON générés dans `outputs/`.

## Prérequis
- Navigateur récent (supportant `showDirectoryPicker`, ex. Chrome/Edge >= 86). Pour les autres navigateurs, la sélection de dossier via `<input type="file" webkitdirectory>` reste disponible.
- Python 3 installé (utilisé ici uniquement pour lancer un serveur HTTP statique). Tout autre serveur statique peut convenir.

## Démarrage rapide
```bash
cd review
python3 -m http.server 8000
```

Puis ouvrez `http://localhost:8000` dans votre navigateur.

## Utilisation
1. Cliquez sur « Choisir le dossier outputs » pour pointer vers `./outputs`. Le navigateur liste ensuite les sous-dossiers (benchmarks). Si `showDirectoryPicker` n’est pas supporté, utilisez l’option « Ou charger via sélection de dossier ».
2. Choisissez un benchmark dans la liste déroulante :
   - Le tableau affiche `model`, `prompt`, `category`, `date de mise à jour`, `maturity`, `criteria_selection` et une colonne « Inclure ».
   - Tri en cliquant sur l’entête, recherche plein texte sur les prompts, pagination (25 lignes).
3. Chaque ligne peut être éditée :
   - La case « Inclure » (cochée par défaut) permet d’exclure une question des exports.
   - La colonne `category` est modifiable directement.
   - La colonne `maturity` propose un sélecteur (`Child`, `Teen`, `YoungAdult`, `Emerging`).
4. Bouton « Détails » : ouvre une vue JSON pliable/dépliable pour inspecter le record complet. Bouton `×` ou touche `Esc` pour fermer.
5. Bouton « Exporter le tableau en CSV » : génère un fichier CSV contenant les données affichées (avec les modifications et la colonne `selected`).

## Notes
- Les colonnes affichent la date de modification extraite du fichier JSON (timestamp OS ou champ `timestamp`).
- Le navigateur n’écrit rien : la lecture se fait côté client uniquement.

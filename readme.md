# Mémoire 1A SVS 2024-2025 : Effet du port de la Ceinture de Force sur la Performance au soulevé de terre chez des sujets entraînés en Force Athlétique

Romain MARTINIE & Léonine ROUANET (ENS 2SEP) sous la direction de Germain FAITY (ENS 2SEP)

---

## Description
Évaluer l’effet du port d’une ceinture de force homologuée IPF sur la production de force maximale et la cinématique articulaire du tronc lors d’une tâche isométrique en position de départ au soulevé de terre chez des athlètes entraînés en force athlétique.

Cinq pratiquants masculins ont réalisé des tirages maximaux isométriques en position initiale du soulevé de terre dans trois conditions randomisées : sans ceinture (NB), ceinture desserrée (LB) et ceinture serrée (WB). La force maximale produite et la variation de l'angle de la colonne ont été mesurés via plateforme de force et motion capture (QTM).


## Structure

```
├── code/
│   ├── data_process.py           # Traitement des données
│   ├── functions.py              # Fonctions associées
│   └── stat_process.R            # Analyse statistique
│
├── processed_data/
│   ├── dataframe.xlsx            # Données traitées (Fmax, dFlex...)
│   └── subject_data.xlsx         # Données des participants traitées (poids, taille...)
│
└── raw_data/                     # Données brutes
    ├── donnees_participants.xlsx # Données brutes pseudonymisées des sujets
    └── ...                       # Fichiers .c3d 
```


## Utilisation

1. **Configuration** : Modifiez la variable `WRK_PATH` dans les scripts.

2. **Prérequis** :
   - Python : `numpy`, `pandas`, `seaborn`, `matplotlib`, `pyomeca`, `scipy`
   - R : `tidyverse`, `rstatix`, `ggplot2`, `psych`, `readxl`

3. **Exécuter** :
   ```bash
   python data_process.py  # Traitement des données
   Rscript stat_process.R  # Analyses statistiques
   ```
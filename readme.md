# Mémoire 1A SVS 2024-2025 : Effet du port de la Ceinture de Force sur la Performance au soulevé de terre chez des sujets entraînés en Force Athlétique

**Auteurs** : Romain MARTINIE & Léonine ROUANET (ENS 2SEP)

---

## Description
Évaluer l’effet du port d’une ceinture de force homologuée IPF sur la production de force maximale et la cinématique articulaire du tronc lors d’une tâche isométrique en position de départ au soulevé de terre chez des athlètes entraînés en force athlétique
Cinq pratiquants masculins ont réalisé des tirages maximaux isométriques en position initiale du soulevé de terre dans trois conditions randomisées : sans ceinture (NB), ceinture desserrée (LB) et ceinture serrée (WB). La force maximale produite et la variation de l'angle de la colonne ont été mesurés via plateforme de force et motion capture (QTL)

---

## Structure

├── code/
│   ├── data_process.py  # Main data processing pipeline
│   ├── functions.py     # Helper functions for biomechanical calculations
│   └── stat_process.R   # Statistical analysis in R
│
├── processed_data/
│   ├── dataframe.xlsx   # Processed biomechanical data
│   └── subject_data.xlsx # Processed participant data
│
└── raw_data/           # Raw experimental data
    └── ...             # .c3d files and other raw inputs

- `data_process.py` : Traitement des données 
- `functions.py` : Fonctions auxiliaires
- `stat_process.R` : Analyses statistiques
- `dataframe.xlsx` : Données traitées exportées 
- `subject_data.xlsx` : Données des participants

---

# -*- coding: utf-8 -*-
"""
ENS 2SEP
Fonctions associées mémoire 1A SVS 2024-2025
@authors: MARTINIE Romain & ROUANET Léonine
"""

import numpy as np
from pyomeca import Markers, Analogs


def get_markers(file_path, marker_groups, freq_cutoff=10):
    """
    Charge les données des marqueurs à partir d'un fichier C3D, applique un filtrage passe-bas
    et retourne un dictionnaire des coordonnées moyennes des marqueurs par groupe.
    
    Paramètres
    ----------
    file_path : str
        Chemin d'accès au fichier C3D contenant les données des marqueurs.
        
    marker_groups : dict
        Dictionnaire où les clés sont les noms des articulations et les valeurs
        sont des listes des noms des marqueurs associés.
        
    freq_cutoff : int, optional
        Fréquence de coupure pour le filtrage passe-bas des données (Hz).
        Default: 10
        
    Retourne
    --------
    dict
        Dictionnaire avec les groupes de marqueurs comme clés et leurs coordonnées 
        normalisées (moyenne par groupe) comme valeurs en mètres.
    """
    # Initialisation du dictionnaire de résultats
    markers = {}

    # Chargement des données et application du filtrage
    rep = Markers.from_c3d(file_path)
    freq = rep.attrs['rate']
    repf = rep.meca.low_pass(order=2, cutoff=freq_cutoff, freq=freq)

    # Traitement pour chaque groupe de marqueurs
    for group_name, markers_list in marker_groups.items():
        # Initialiser avec des zéros de la forme du premier marqueur dans le groupe
        marker_data = np.zeros_like(
            repf.sel(channel=markers_list[0], axis=['x', 'y', 'z']).values.T)

        # Addition des données pour chaque marqueur dans le groupe
        for marker in markers_list:
            marker_data += repf.sel(channel=marker, axis=['x', 'y', 'z']).values.T

        # Calcul de la moyenne et conversion en mètres
        marker_data /= (1000 * len(markers_list))
        markers[group_name] = marker_data

    return markers


def get_angle(p1, p2, p3, p4):
    """
    Calcule l'angle entre deux segments définis par quatre points 3D.
    
    Paramètres
    ----------
    p1 : array-like, shape (n_samples, 3)
        Coordonnées (x, y, z) du premier point du premier segment.
        
    p2 : array-like, shape (n_samples, 3)
        Coordonnées (x, y, z) du deuxième point du premier segment.
        
    p3 : array-like, shape (n_samples, 3)
        Coordonnées (x, y, z) du premier point du second segment.
        
    p4 : array-like, shape (n_samples, 3)
        Coordonnées (x, y, z) du deuxième point du second segment.
    
    Retourne
    --------
    array-like, shape (n_samples,)
        Angles entre les deux segments en degrés pour chaque échantillon.
    """
    # Calcul des vecteurs directeurs
    v1 = p2 - p1
    v2 = p4 - p3

    # Normalisation des vecteurs
    norme_v1 = v1 / np.linalg.norm(v1, axis=1)[:, np.newaxis]
    norme_v2 = v2 / np.linalg.norm(v2, axis=1)[:, np.newaxis]

    # Produit scalaire des vecteurs normalisés
    dot_product = np.sum(norme_v1 * norme_v2, axis=1)
    
    # Assurer que le produit scalaire est dans l'intervalle [-1, 1]
    dot_product = np.clip(dot_product, -1.0, 1.0)

    # Calcul de l'angle en radians, puis conversion en degrés
    angle_rad = np.arccos(dot_product)
    angle_deg = np.degrees(angle_rad)

    return angle_deg


def get_force(file_path, name_plate):
    """
    Extrait et retourne les forces de réaction du sol mesurées à partir d'un fichier C3D.

    Paramètres
    ----------
    file_path : str
        Chemin d'accès au fichier C3D contenant les données.
        
    name_plate : str
        Nom de la plateforme de force (ex: "Amti Gen 5 BP6001200-2K-CT_2").
        Peut être obtenu via `.channel` sur la variable importée par `Analogs.from_c3d()`.

    Retourne
    --------
    forces : np.ndarray, shape (n_samples, 3)
        Tableau NumPy où chaque ligne contient les composantes:
        - forces[:, 0] : Force Fx
        - forces[:, 1] : Force Fy
        - forces[:, 2] : Force Fz
        Les valeurs sont inversées pour correspondre aux forces de réaction du sol.
    """
    # Chargement des données analogiques
    rep = Analogs.from_c3d(file_path)
    
    # Sélection des composantes de force
    fx = rep.sel(channel=f"{name_plate}_Fx")
    fy = rep.sel(channel=f"{name_plate}_Fy")
    fz = rep.sel(channel=f"{name_plate}_Fz")
    
    # Création du tableau de forces et inversion (pour avoir les forces de réaction)
    forces = np.stack([fx.values, fy.values, fz.values], axis=0)
    
    return -forces.T


def calculate_spine_flex(angle_data):
    """
    Calcule l'amplitude de l'angle de la colonne vertébrale en conservant le sens.
    
    Paramètres
    ----------
    angle_data : np.ndarray
        Série temporelle des valeurs d'angle.

    Retourne
    --------
    float
        Amplitude signée de l'angle:
        - Positive si extension au cours du mouvement (min puis max)
        - Négative si flexion au cours du mouvement (max puis min)
    """
    # Calcul de l'amplitude absolue
    delta_spine_flex = angle_data.max() - angle_data.min()
    
    # Détermination du signe selon la chronologie max/min
    max_index = np.argmax(angle_data)
    min_index = np.argmin(angle_data)

    # Si le maximum se produit avant le minimum, il s'agit d'une flexion (valeur négative)
    if max_index < min_index:
        delta_spine_flex = -delta_spine_flex
    
    return delta_spine_flex
# -*- coding: utf-8 -*-
"""
ENS 2SEP
Traitement données mémoire 1A SVS 2024-2025
@author: MARTINIE Romain & ROUANET Léonine
"""

import seaborn as sns
import matplotlib.pyplot as plt
import pandas as pd
import os
import numpy as np
from pyomeca import Markers, Analogs
from scipy.signal import find_peaks, butter, filtfilt

# %% Configuration des chemins
WRK_PATH = r'/home/user/path'

DAT_PATH = os.path.join(WRK_PATH, "1A_deadlift/Data")
os.chdir(WRK_PATH)

print(f"Répertoire de travail actuel : {os.getcwd()}")
print(f"Répertoire des données : {DAT_PATH}")

import functions as f

# %% Paramètres des données
condition = ['NB', 'LB', 'WB']  
subject = ["HUN", "UAG", "YMJ", "PUB", "GFD"]  # Liste des sujets
n = len(subject)

# %% Définition des groupes de marqueurs
marker_groups = {
    'hip_l': ['LGD'],
    'hip_r': ['RGD'],
    'trunkBase': ['LGD', 'RGD'],
    'T4': ['T4'], 
    'T8': ['T8'],
    'C7': ['C7'], 
    'JLS': ['JLS'],
    'trunkMid': ['STRN', 'T8'],
    'sternum': ['STRN'],
    'knee_r': ['RKNE', 'RKNI'],
    'knee_l': ['LKNE', 'LKNI'],
    'ankle_r': ['RANE', 'RANI'], 
    'ankle_l': ['LANE', 'LANI'],
    'shoulder_l': ['LSHO'], 
    'shoulder_r': ['RSHO'], 
    'elbow_r': ['RRAD', 'RHUM'], 
    'elbow_l': ['LRAD', 'LHUM'], 
    'wrist_r': ['RWRB', 'RWRA'], 
    'wrist_l': ['LWRB', 'LWRA'],
}

# %% Initialisation des dictionnaires pour le stockage des données
rep, time, markers, force, rep_f = {}, {}, {}, {}, {}

# %% Extraction des données: marqueurs, temps et force
for condition_id in condition:
    for subject_id in subject:
        ID = f"{subject_id}_{condition_id}" 
        print(f"Loading data for: {ID}")
        
        file_path = os.path.join(DAT_PATH, f'{ID}.c3d')
        
        # Charger les marqueurs par condition
        rep[ID] = Markers.from_c3d(file_path)
        time[ID] = rep[ID].time.values
        markers[ID] = f.get_markers(file_path, marker_groups)
        
        # Charger les données de la plateforme de force par condition
        rep_f[ID] = Analogs.from_c3d(file_path)
        force[ID] = f.get_force(file_path, 'Amti Gen 5 BP6001200-2K-CT_1')

# %% Correction des données
corrections = {
    'HUN_WB': {'offset': -1208},
    'HUN_NB': {'delete': (1300, 1500)},
    'HUN_LB': {'delete': (1100, 2000)},
    'UAG_NB': {'delete': (900, 1100)},
    'YMJ_NB': {'delete': (0, 450)},
    'YMJ_LB': {'delete': (660, 800)},
    'YMJ_WB': {'delete': (600, 800)},
    'PUB_LB': {'delete': (500, 800)},
    'GFD_NB': {'delete': (700, 1200)}, 
    'GFD_LB': {'delete': (650, 950)},
    'GFD_WB': {'delete': (750, 1300)}, 
}

# Application des corrections
for ID, actions in corrections.items():
    print(f"Applying corrections for: {ID}")
    if 'offset' in actions:
        force[ID][:, 2] -= actions['offset']
    if 'delete' in actions:
        start, end = actions['delete']
        force[ID] = np.delete(force[ID], np.s_[start:end + 1], axis=0)
        time[ID] = np.delete(time[ID], np.s_[start:end + 1], axis=0)

# %% Calcul de la masse
g = 9.80665  # Constante d'accélération gravitationnelle (m/s²)
BW_F, BW_kg, BW_moy = {}, {}, {}

for subject_id in subject:
    for condition_id in condition:
        ID = f"{subject_id}_{condition_id}" 
        
        freq = rep_f[ID].attrs['rate']
        
        # Calcul du poids corporel en kg à partir de la dernière seconde des données
        BW_kg[ID] = np.mean(force[ID][-int(freq):, 2]) / g
        # Force correspondante en Newtons
        BW_F[ID] = BW_kg[ID] * g
    
    # Calcul du poids moyen par sujet
    BW_moy[subject_id] = np.mean([BW_kg[f"{subject_id}_{c}"] for c in condition])

# %% Calcul de la norme de force (moins le poids de corps)
force_norm = {}

for subject_id in subject:
    for condition_id in condition:
        ID = f"{subject_id}_{condition_id}" 
        force_norm[ID] = np.linalg.norm(force[ID], axis=1) - BW_F[ID]

# %% Lissage de la force
force_smooth = {}
window_size = int(freq * 0.3)  # Taille de la fenêtre pour 0.3s
window = np.ones(window_size) / window_size  # Fenêtre uniforme

for subject_id in subject:
    for condition_id in condition:
        ID = f"{subject_id}_{condition_id}" 
        force_smooth[ID] = np.convolve(force_norm[ID], window, mode='same')

# %% Segmentation du mouvement
d_force, force_cut, time_cut, markers_cut, duration = {}, {}, {}, {}, {}
d_force_2, d_force_2_filt, TTP = {}, {}, {}

for subject_id in subject:
    for condition_id in condition:
        ID = f"{subject_id}_{condition_id}" 
        print(f"Processing movement for: {ID}")
        
        # Calcul des dérivées pour détecter l'accélération maximale
        d_force[ID] = np.gradient(force_smooth[ID], time[ID])
        d_force_2[ID] = np.gradient(d_force[ID], time[ID])

        # Filtrage de la dérivée seconde (filtre Butterworth passe-bas)
        cutoff = 0.1  # Fréquence de coupure (en fraction de la fréquence d'échantillonnage)
        b, a = butter(N=4, Wn=cutoff, btype='low', analog=False)
        d_force_2_filt[ID] = filtfilt(b, a, d_force_2[ID])
        
        # Détection des pics positifs d'accélération
        peaks_positive = find_peaks(d_force_2_filt[ID])[0]                
        peaks_values = d_force_2_filt[ID][peaks_positive]
        
        # Trouver les indices des 2 plus grands pics (début et fin du mouvement)
        largest_peaks_indices = np.argsort(peaks_values)[-2:]
        sorted_peaks_indices = np.sort(largest_peaks_indices)  # Conserver l'ordre temporel
        
        # Récupérer les indices dans les données d'origine
        final_indices = peaks_positive[sorted_peaks_indices]
        start_index = final_indices[0]
        end_index = final_indices[1]
        
        # Tronquer les données pour isoler le mouvement
        force_cut[ID] = force_smooth[ID][start_index:end_index+1]
        time_cut[ID] = time[ID][start_index:end_index+1]
        markers_cut[ID] = {key: value[start_index:end_index+1] for key, value in markers[ID].items()}

        # Calcul de la durée du mouvement et du temps au pic de force
        duration[ID] = (end_index-start_index)/freq
        TTP[ID] = time[ID][np.argmax(force_cut[ID])+start_index]

        print(f"  Début mouvement: {start_index/freq:.2f}s")
        print(f"  Fin mouvement: {end_index/freq:.2f}s")
        print(f"  Durée mouvement: {duration[ID]:.2f}s")

# %% Calcul des angles articulaires
angles = {
    "hipr_angle": ('trunkBase', 'trunkMid', 'hip_r', 'knee_r'),
    "hipl_angle": ('trunkBase', 'trunkMid', 'hip_l', 'knee_l'),
    "kneel_angle": ('knee_l', 'ankle_l', 'knee_l', 'hip_l'),
    "kneer_angle": ('knee_r', 'ankle_r', 'knee_r', 'hip_r'),
    "spine_angle": ('T8', 'C7', 'T8', 'JLS')
}

# Initialiser les dictionnaires d'angles
angle_results = {angle_name: {} for angle_name in angles}

for subject_id in subject:
    for condition_id in condition:
        ID = f"{subject_id}_{condition_id}" 
        print(f"Calculating angles for: {ID}")
            
        # Calcul et filtrage des angles pour cette condition
        for angle_name, marker_keys in angles.items():
            p1, p2, p3, p4 = [markers_cut[ID][key] for key in marker_keys]
            angle_results[angle_name][ID] = f.get_angle(p1, p2, p3, p4)
            
            # Filtrage des angles
            cutoff = 0.1
            b, a = butter(N=2, Wn=cutoff, btype='low', analog=False)
            angle_results[angle_name][ID] = filtfilt(b, a, angle_results[angle_name][ID])

# %% Organisation des données pour l'analyse
data = {
    'subject': [],
    'condition': [],
    'max_force': [], 
    'TTP': [],
    'duration': [],
    'delta_spine_flex': [],
    'speed_spine_flex': [],
    'BW': []
}

for subject_id in subject:
    for condition_id in condition:
        ID = f"{subject_id}_{condition_id}" 
        
        max_force = force_cut[ID].max()
        
        # Calcul de l'amplitude de l'angle de la colonne
        delta_spine_flex = f.calculate_spine_flex(angle_results['spine_angle'][ID])
        
        # Vitesse moyenne de flexion de la colonne
        speed_spine_flex = delta_spine_flex / duration[ID]
        
        # Regrouper les données
        new_data = {
            'subject': subject_id,
            'condition': condition_id,
            'max_force': max_force,
            'TTP': TTP[ID],
            'duration': duration[ID],
            'delta_spine_flex': delta_spine_flex,
            'speed_spine_flex': speed_spine_flex,
            'BW': BW_kg[ID]
        }
        
        # Mise à jour du dictionnaire de données
        for key, value in new_data.items():
            data[key].append(value)

# Création du DataFrame
df = pd.DataFrame(data)
print("DataFrame créé:")
print(df)

# Export des données
df.to_excel("dataframe.xlsx", sheet_name="sheet1", index=False)

# %% Traitement des données des participants
subject_data = pd.read_excel('donnees_participants.xlsx', nrows=n)

# Ajout du poids corporel moyen dans les données des participants
for subject_id in subject:
    poids = df[df['subject'] == subject_id]['BW'].mean()
    subject_data.loc[subject_data['code_sujet'] == subject_id, 'BW'] = poids
    
# Calcul du ratio force/poids
subject_data['ratio'] = subject_data['e1RM'] / subject_data['BW']
subject_data.drop(columns=['Prénom', 'Nom'], inplace=True)

# Export des données des participants
subject_data.to_excel("subject_data.xlsx", sheet_name="sheet1", index=False)

# Affichage du ratio moyen force/poids
ratio_mean = subject_data['ratio'].mean()
ratio_std = subject_data['ratio'].std()
print(f"Ratio moyen force/poids: {ratio_mean:.2f} ± {ratio_std:.2f}")

# %% Visualisation (décommenter pour utiliser)
"""
# Exemple de visualisation des angles de la colonne pour un participant
plt.figure(figsize=(10, 6))
for condition_id in condition:
    ID = f"HUN_{condition_id}"
    plt.plot(time_cut[ID], angle_results['spine_angle'][ID], label=condition_id)
plt.title("Angles de la colonne (sujet HUN)")
plt.xlabel("Temps (s)")
plt.ylabel("Angle (degrés)")
plt.legend()
plt.grid(True)
plt.show()

# Comparaison des forces maximales par condition
plt.figure(figsize=(12, 6))
sns.boxplot(x='condition', y='max_force', data=df)
plt.title("Force maximale par condition")
plt.xlabel("Condition")
plt.ylabel("Force maximale (N)")
plt.grid(True)
plt.show()
"""

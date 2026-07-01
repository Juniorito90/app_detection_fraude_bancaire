"""
detecteur.py
------------
Détection par Isolation Forest et DBSCAN sur des features relatives.

Features utilisées :
  - ratio_montant : montant / budget_moyen_client  (1.0 = normal, >4 = suspect)
  - zone_diff     : 0 si zone habituelle, 1 si zone étrangère
  - delai         : secondes depuis la dernière transaction

Pourquoi ces features relatives et pas les montants bruts ?
  → Après le calcul du ratio, un patron et un étudiant en transaction normale
    ont TOUS LES DEUX un ratio ≈ 1.0 → ils se regroupent ensemble sur le graphique.
  → Un fraudeur, quel que soit le client, a un ratio >> 1.0 → il ressort.
  → Sans ratio, Cheikh (850k normal) serait toujours détecté comme suspect.

Pourquoi contamination basse (3% à 12%) ?
  → Avec une contamination de 20%, IF est FORCÉ de signaler 20% des transactions,
    même celles qui sont normales → des croix apparaissent dans le groupe vert.
  → Avec 3-12%, IF ne signale que ce qui est vraiment éloigné du reste.
"""

import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import IsolationForest
from sklearn.cluster import DBSCAN

FEATURES = ["ratio_montant", "zone_diff", "delai"]


def analyser(fenetre: list, sensibilite: int) -> list:
    """
    Analyse la fenêtre de transactions et met à jour if_suspect / dbscan_suspect.
    Nécessite au minimum 5 transactions pour être significatif.
    """
    if len(fenetre) < 5:
        return fenetre

    # Matrice des 3 features
    X = np.array([[t[f] for f in FEATURES] for t in fenetre], dtype=float)

    # Standardisation Z-score
    # → même si ratio est déjà relatif, le délai est en secondes (1 à 3600)
    #   et zone_diff est 0 ou 1 → sans standardisation le délai dominerait
    X_sc = StandardScaler().fit_transform(X)

    s = sensibilite / 100

    # ── Isolation Forest ──────────────────────────────────────────────────────
    # contamination : proportion de points que l'algo peut marquer comme anomalie
    # On garde 3% à 12% pour éviter de flaguer des transactions normales
    contamination = round(0.03 + s * 0.09, 3)   # 3 % → 12 %

    labels_if = IsolationForest(
        contamination=contamination,
        n_estimators=100,
        random_state=42,
    ).fit_predict(X_sc)
    # -1 = anomalie (chemin d'isolation court), +1 = normal

    # ── DBSCAN ───────────────────────────────────────────────────────────────
    # epsilon : rayon de voisinage (après standardisation)
    # Plus epsilon est petit, plus le critère est strict → plus de "bruit"
    epsilon = round(max(0.5, 1.8 - s * 1.2), 3)   # 1.8 → 0.6

    labels_db = DBSCAN(
        eps=epsilon,
        min_samples=3,
    ).fit_predict(X_sc)
    # -1 = bruit (pas de voisins suffisants)

    for i, t in enumerate(fenetre):
        t["if_suspect"]     = bool(labels_if[i] == -1)
        t["dbscan_suspect"] = bool(labels_db[i] == -1)

    return fenetre

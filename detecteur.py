import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import IsolationForest
from sklearn.cluster import DBSCAN

# Variables utilisées pour la détection
VARIABLES = ["montant", "distance", "delai"]


def analyser(fenetre: list, sensibilite: int) -> list:
    """
    Analyse une fenêtre de transactions et marque chaque transaction
    comme suspecte ou non selon Isolation Forest et DBSCAN.

    sensibilite : curseur entre 1 et 100
      - plus élevé = plus de transactions signalées
      - Isolation Forest : contamination augmente (2% → 35%)
      - DBSCAN : epsilon diminue (2.0 → 0.3), critère plus strict
    """
    if len(fenetre) < 5:
        return fenetre

    # Conversion en matrice numpy
    X = np.array([[t[v] for v in VARIABLES] for t in fenetre], dtype=float)

    # Standardisation Z-score
    X = StandardScaler().fit_transform(X)

    # Calcul des paramètres selon la sensibilité
    s = sensibilite / 100
    contamination = round(0.02 + s * 0.33, 3)   # 2% à 35%
    epsilon       = round(max(0.3, 2.0 - s * 1.7), 3)  # 2.0 à 0.3

    # Isolation Forest
    labels_if = IsolationForest(
        contamination=contamination,
        n_estimators=100,
        random_state=42,
    ).fit_predict(X)

    # DBSCAN
    labels_db = DBSCAN(
        eps=epsilon,
        min_samples=3,
    ).fit_predict(X)

    # Enrichissement des transactions
    for i, t in enumerate(fenetre):
        t["if_suspect"]     = bool(labels_if[i] == -1)
        t["dbscan_suspect"] = bool(labels_db[i] == -1)

    return fenetre

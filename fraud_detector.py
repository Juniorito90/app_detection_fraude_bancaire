import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import IsolationForest
from sklearn.cluster import DBSCAN

FEATURES = ["amount", "distance_km", "time_since_last", "hour"]


def _to_matrix(window: list[dict]) -> np.ndarray:
    return np.array([[t[f] for f in FEATURES] for t in window], dtype=float)


def _preprocess(window: list[dict]) -> np.ndarray:
    """
    Standardisation Z-score — indispensable ici.

    Sans elle, 'amount' (dizaines de milliers de FCFA) écraserait
    complètement 'hour' (0-23) dans le calcul de distance/densité de DBSCAN.
    """
    return StandardScaler().fit_transform(_to_matrix(window))


def sensitivity_to_params(sensitivity: int) -> dict:
    """
    Traduit le curseur (1-100) en hyperparamètres concrets.
    Sensibilité haute => détection plus stricte => plus d'alertes.
    """
    s = max(1, min(100, sensitivity)) / 100
    return {
        "contamination": round(0.02 + s * 0.33, 3),   # 2 % → 35 %
        "eps":           round(max(0.30, 2.2 - s * 1.85), 3),  # 2.2 → 0.35
        "min_samples":   3,
    }


def analyze_window(window: list[dict], sensitivity: int) -> list[dict]:
    """
    Applique les deux algorithmes sur la fenêtre et enrichit chaque
    transaction avec ses drapeaux et son score Isolation Forest.
    Retourne la fenêtre sans rien modifier si < 5 transactions.
    """
    if len(window) < 5:
        return window

    params = sensitivity_to_params(sensitivity)
    X = _preprocess(window)

    # --- Isolation Forest ---
    iforest = IsolationForest(
        contamination=params["contamination"],
        n_estimators=100,
        random_state=42,
    )
    if_labels = iforest.fit_predict(X)            # -1 = anomalie
    # score_samples retourne un score négatif : plus il est bas, plus c'est suspect
    if_raw_scores = iforest.score_samples(X)
    # On normalise entre 0 et 1 (1 = très suspect) pour l'affichage
    s_min, s_max = if_raw_scores.min(), if_raw_scores.max()
    if s_max > s_min:
        if_scores_norm = 1 - (if_raw_scores - s_min) / (s_max - s_min)
    else:
        if_scores_norm = np.full(len(window), 0.5)

    # --- DBSCAN ---
    db_labels = DBSCAN(
        eps=params["eps"],
        min_samples=params["min_samples"],
    ).fit_predict(X)

    for i, t in enumerate(window):
        t["if_flag"]   = bool(if_labels[i] == -1)
        t["dbscan_flag"] = bool(db_labels[i] == -1)
        t["if_score"]  = round(float(if_scores_norm[i]), 3)

    return window
import random
import itertools
from datetime import datetime

MERCHANT_CATEGORIES = [
    "Alimentation", "Carburant", "Restaurant", "E-commerce",
    "Retrait DAB", "Virement", "Abonnement", "Pharmacie",
    "Transport", "Télécommunications",
]

_id_counter = itertools.count(1)


def _hour_weights():
    return [0.3 if h < 6 or h >= 23 else 1.7 if 8 <= h <= 20 else 1.0
            for h in range(24)]


def _normal_transaction():
    amount        = max(500, random.lognormvariate(mu=9.6, sigma=0.6))
    distance_km   = max(0, random.expovariate(1 / 5))
    time_since    = max(5, random.expovariate(1 / 1800))
    return round(amount), round(distance_km, 1), round(time_since, 1)


def _fraud_transaction():
    pattern = random.choice(["montant_extreme", "geolocalisation", "frequence"])
    if pattern == "montant_extreme":
        amount      = random.uniform(400_000, 2_500_000)
        distance_km = random.uniform(0, 25)
        time_since  = max(5, random.expovariate(1 / 1800))
    elif pattern == "geolocalisation":
        amount      = random.uniform(30_000, 300_000)
        distance_km = random.uniform(600, 7_000)
        time_since  = max(5, random.expovariate(1 / 1800))
    else:                                          # card-testing
        amount      = random.uniform(500, 10_000)
        distance_km = random.uniform(0, 15)
        time_since  = random.uniform(1, 6)
    return round(amount), round(distance_km, 1), round(time_since, 1)


def generate_transaction(fraud_probability: float = 0.08) -> dict:
    """Génère une transaction unique avec vérité terrain simulée."""
    is_fraud = random.random() < fraud_probability
    amount, dist, ts = _fraud_transaction() if is_fraud else _normal_transaction()
    hour = random.choices(range(24), weights=_hour_weights())[0]

    return {
        "id":              next(_id_counter),
        "timestamp":       datetime.now().strftime("%H:%M:%S"),
        "amount":          amount,
        "distance_km":     dist,
        "time_since_last": ts,
        "hour":            hour,
        "merchant":        random.choice(MERCHANT_CATEGORIES),
        "is_fraud_truth":  is_fraud,
        # remplis plus tard par fraud_detector
        "if_flag":         False,
        "dbscan_flag":     False,
        "if_score":        0.5,
    }

import random
from datetime import datetime

MARCHANDS = [
    "Alimentation", "Carburant", "Restaurant", "Electricite",
    "Boutique en ligne", "Retrait GAB", "Transport", "Pharmacie",
]

def generer_transaction(proba_fraude=0.08):
    """
    Génère une transaction.
    - proba_fraude : probabilité qu'une fraude soit injectée
    Retourne un dictionnaire avec toutes les informations de la transaction.
    """
    est_fraude = random.random() < proba_fraude

    if est_fraude:
        # 3 types de fraude réalistes
        type_fraude = random.choice(["montant_extreme", "loin", "rafale"])
        if type_fraude == "montant_extreme":
            montant     = random.uniform(400_000, 2_000_000)
            distance    = random.uniform(0, 20)
            delai       = random.uniform(10, 3600)
        elif type_fraude == "loin":
            montant     = random.uniform(30_000, 300_000)
            distance    = random.uniform(500, 6000)   # transaction à l'étranger
            delai       = random.uniform(10, 3600)
        else:  # rafale = card testing
            montant     = random.uniform(500, 8_000)
            distance    = random.uniform(0, 10)
            delai       = random.uniform(1, 5)        # très rapproché
    else:
        montant  = max(500, random.lognormvariate(9.6, 0.6))  # comportement normal
        distance = max(0, random.expovariate(1 / 5))
        delai    = max(5, random.expovariate(1 / 1800))

    return {
        "heure":    datetime.now().strftime("%H:%M:%S"),
        "montant":  round(montant),
        "distance": round(distance, 1),
        "delai":    round(delai, 1),
        "marchand": random.choice(MARCHANDS),
        # vérité terrain (jamais transmise aux algorithmes)
        "est_fraude_reelle": est_fraude,
        # remplis par le détecteur
        "if_suspect":    False,
        "dbscan_suspect": False,
    }

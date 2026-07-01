"""
simulateur.py
-------------
Génère des transactions bancaires pour 10 clients distincts.

Chaque client a :
  - un budget moyen (montant_moy) : ce qu'il dépense habituellement
  - une zone géographique habituelle

Le ratio = montant_transaction / montant_moy_client
  → ratio ≈ 1.0  : transaction normale pour ce client
  → ratio > 4.0  : transaction anormalement élevée pour ce client

Le jitter est calculé UNE SEULE FOIS à la création de la transaction
et stocké dans le dictionnaire → les points ne bougent pas sur le graphique.
"""

import random
from datetime import datetime

CLIENTS = {
    "CLI_001": {"nom": "Amadou Diallo",  "profil": "Étudiant",   "zone": "Dakar-Plateau", "montant_moy": 12_000,  "montant_std": 2_500},
    "CLI_002": {"nom": "Fatou Konaté",   "profil": "Employée",   "zone": "Thiès",          "montant_moy": 55_000,  "montant_std": 12_000},
    "CLI_003": {"nom": "Moussa Ndiaye",  "profil": "Commerçant", "zone": "Médina",         "montant_moy": 130_000, "montant_std": 30_000},
    "CLI_004": {"nom": "Aïssatou Sy",    "profil": "Directrice", "zone": "Almadies",       "montant_moy": 380_000, "montant_std": 70_000},
    "CLI_005": {"nom": "Ibrahima Fall",  "profil": "Étudiant",   "zone": "Pikine",         "montant_moy": 8_000,   "montant_std": 1_500},
    "CLI_006": {"nom": "Mariama Ba",     "profil": "Infirmière", "zone": "Kaolack",        "montant_moy": 65_000,  "montant_std": 14_000},
    "CLI_007": {"nom": "Cheikh Sarr",    "profil": "Patron",     "zone": "Almadies",       "montant_moy": 850_000, "montant_std": 180_000},
    "CLI_008": {"nom": "Ndèye Diop",     "profil": "Vendeuse",   "zone": "Rufisque",       "montant_moy": 22_000,  "montant_std": 5_000},
    "CLI_009": {"nom": "Oumar Traoré",   "profil": "Ingénieur",  "zone": "Dakar-Plateau",  "montant_moy": 160_000, "montant_std": 35_000},
    "CLI_010": {"nom": "Rokhaya Mbaye",  "profil": "Retraitée",  "zone": "Saint-Louis",    "montant_moy": 38_000,  "montant_std": 8_000},
}

ZONES_ETRANGERES = ["Paris", "Dubaï", "Abidjan", "Casablanca", "New York", "Ziguinchor"]

MARCHANDS = [
    "Alimentation", "Carburant", "Restaurant", "E-commerce",
    "Retrait DAB", "Transport", "Pharmacie", "Vêtements", "Électronique",
]

_dernier_temps: dict = {}


def generer_transaction(proba_fraude: float = 0.08) -> dict:
    """
    Génère une transaction pour un client aléatoire.

    Cas normal  : montant proche de montant_moy, dans la zone habituelle
    Cas fraude  : montant 5x à 15x montant_moy, et/ou zone étrangère
    """
    client_id = random.choice(list(CLIENTS.keys()))
    client    = CLIENTS[client_id]

    est_fraude = random.random() < proba_fraude

    if est_fraude:
        type_fraude = random.choice(["montant", "zone", "les_deux"])

        if type_fraude == "montant":
            # Montant 5 à 15 fois le budget habituel → ratio entre 5 et 15
            montant = client["montant_moy"] * random.uniform(5, 15)
            zone    = client["zone"]

        elif type_fraude == "zone":
            # Montant normal mais zone totalement différente
            montant = max(500, random.gauss(client["montant_moy"], client["montant_std"]))
            zone    = random.choice(ZONES_ETRANGERES)

        else:
            # Les deux : gros montant + zone étrangère (cas le plus grave)
            montant = client["montant_moy"] * random.uniform(4, 12)
            zone    = random.choice(ZONES_ETRANGERES)

    else:
        # Transaction normale : montant autour du budget habituel, zone habituelle
        montant = max(500, random.gauss(client["montant_moy"], client["montant_std"]))
        zone    = client["zone"]

    # Délai depuis la dernière transaction de CE client
    maintenant = datetime.now()
    if client_id in _dernier_temps:
        delai = (maintenant - _dernier_temps[client_id]).total_seconds()
        delai = max(1.0, delai)
    else:
        delai = random.uniform(300, 3600)
    _dernier_temps[client_id] = maintenant

    # Ratio : combien de fois le budget habituel du client
    ratio_montant = round(montant / client["montant_moy"], 2)

    # Zone différente de la zone habituelle : 1, sinon : 0
    zone_diff = 0 if zone == client["zone"] else 1

    # ── JITTER FIXE ───────────────────────────────────────────────────────────
    # Calculé UNE SEULE FOIS ici et stocké dans le dict.
    # Évite que les points bougent sur le graphique à chaque rafraîchissement.
    # C'est juste une légère dispersion verticale pour rendre les points lisibles.
    zone_jitter = zone_diff + random.uniform(-0.07, 0.07)

    return {
        # Identité
        "client_id":       client_id,
        "nom":             client["nom"],
        "profil":          client["profil"],
        "zone_habituelle": client["zone"],
        # Transaction
        "heure":           maintenant.strftime("%H:%M:%S"),
        "montant":         round(montant),
        "zone":            zone,
        "marchand":        random.choice(MARCHANDS),
        "delai":           round(delai, 1),
        # Features pour les algorithmes
        "ratio_montant":   ratio_montant,
        "zone_diff":       zone_diff,
        "zone_jitter":     round(zone_jitter, 3),   # stocké → fixe
        # Vérité terrain (jamais transmise aux algorithmes)
        "est_fraude_reelle": est_fraude,
        # Résultats détection (remplis par detecteur.py)
        "if_suspect":      False,
        "dbscan_suspect":  False,
    }

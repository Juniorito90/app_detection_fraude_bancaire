# Détection de fraude bancaire en temps réel
### Tableau de bord Streamlit — Isolation Forest vs DBSCAN

Application web simulant un flux de transactions bancaires en continu
et détectant les anomalies via deux algorithmes de détection non supervisés,
comparés en direct sur le même flux.

---

## Installation et lancement

```bash
# 1. Se placer dans le dossier du projet
cd fraud_streamlit

# 2. Créer un environnement virtuel
python3 -m venv venv
source venv/bin/activate        # Windows : venv\Scripts\activate

# 3. Installer les dépendances
pip install -r requirements.txt

# 4. Lancer l'application
streamlit run app.py
```

Le navigateur s'ouvre automatiquement sur http://localhost:8501

---

## Structure du projet

```
fraud_streamlit/
├── app.py               # Interface Streamlit + logique de flux temps réel
├── data_simulator.py    # Génération des transactions simulées (FCFA)
├── fraud_detector.py    # Prétraitement + Isolation Forest + DBSCAN
├── requirements.txt
└── README.md
```

---

## Fonctionnalités

- Flux automatique de transactions bancaires simulées (toutes les 1,5 s)
- Détection en parallèle par Isolation Forest et DBSCAN
- Curseur de sensibilité ajustable en direct (sidebar)
- Boutons Pause / Reprendre / Réinitialiser
- Graphique d'évolution temporelle des détections
- Scatter plot Montant vs Distance (fenêtre active, coloré par statut)
- Gauge de taux de suspicion global
- Camembert de répartition des alertes
- File des 6 dernières alertes en temps réel
- Registre coloré des 25 dernières transactions

---

## Algorithmes

### Isolation Forest
Isole les points atypiques en construisant des arbres de décision aléatoires.
Un point anormal est "facile à isoler" (chemin court). Score d'anomalie :
`s(x, n) = 2^(-E(h(x)) / c(n))`

### DBSCAN
Classe les points selon leur densité locale. Les points hors de toute
région dense (label = -1) sont considérés comme du bruit → alerte fraude.

### Curseur de sensibilité (1–100)
- Isolation Forest : contamination de 2 % à 35 %
- DBSCAN : epsilon de 2,2 à 0,35 (relation inverse)

---

## Sources
- Liu et al. (2008). *Isolation Forest*. IEEE ICDM.
- Ester et al. (1996). *DBSCAN*. KDD-96.
- Documentation scikit-learn : sklearn.ensemble.IsolationForest
- Documentation scikit-learn : sklearn.cluster.DBSCAN

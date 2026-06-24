# Détection de fraude bancaire en temps réel
### Tableau de bord Streamlit — Isolation Forest vs DBSCAN

Application web simulant un flux de transactions bancaires en continu
et détectant les anomalies via deux algorithmes de détection non supervisés,
comparés en direct sur le même flux.

---

## Installation et lancement

```bash
# 1. Se placer dans le dossier du projet
cd app_detection_fraude_bancaire

# 2. Installer les dépendances
pip install -r requirements.txt

# 3. Lancer l'application
streamlit run app.py
```

Le navigateur s'ouvre automatiquement sur http://localhost:8501

---

## Structure du projet

```
app_detection_fraude_bancaire/
├── app.py               # Interface Streamlit + logique de flux temps réel
├── simulateur.py    # Génération des transactions simulées (FCFA)
├── detecteur.py    # Prétraitement + Isolation Forest + DBSCAN
├── requirements.txt # Bibliotheques a installer
└── README.md
```

---

## Consignes respectées (Sujet 37)

✅ Interface simulant un flux de transactions entrantes  
✅ Isolation Forest + DBSCAN pour signaler les suspectes  
✅ Tableau de bord avec alertes en temps réel et taux de suspicion  
✅ Curseur pour ajuster la sensibilité de détection  

---

## Sources
- Liu et al. (2008). *Isolation Forest*. IEEE ICDM.
- Ester et al. (1996). *DBSCAN*. KDD-96.
- Documentation scikit-learn : sklearn.ensemble.IsolationForest
- Documentation scikit-learn : sklearn.cluster.DBSCAN
# Application de détection de fraude bancaire en temps réel
**Sujet 37 — Swiss UMEF University Dakar — Mr BEBY**

---

## Lancement

```bash
pip install -r requirements.txt
streamlit run app.py
```

---

## Ce qui rend ce système réaliste

10 clients avec des profils différents (étudiant, patron, infirmière...).
Chaque client a son propre budget moyen et sa propre zone géographique.

La détection ne compare jamais un montant à un seuil fixe global.
Elle calcule un **ratio** = montant_transaction / budget_habituel_du_client.

- Patron (850 000 FCFA de moyenne) → transaction à 900 000 FCFA → ratio = 1.06 → NORMALE
- Étudiant (12 000 FCFA de moyenne) → transaction à 900 000 FCFA → ratio = 75.0 → FRAUDE

---

## Structure

```
app_detection_fraude_bancaire/
├── app.py          → Interface Streamlit
├── simulateur.py   → 10 clients + génération des transactions
├── detecteur.py    → Standardisation + Isolation Forest + DBSCAN
├── requirements.txt
└── README.md
```

---

## Sources
- Liu et al. (2008). Isolation Forest. IEEE ICDM.
- Ester et al. (1996). DBSCAN. KDD-96.
- Documentation scikit-learn : IsolationForest, DBSCAN

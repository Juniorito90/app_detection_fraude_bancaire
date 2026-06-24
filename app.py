"""
Lancement : streamlit run app.py
"""

import streamlit as st
from streamlit_autorefresh import st_autorefresh
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

from simulateur import generer_transaction
from detecteur import analyser

# Configuration
st.set_page_config(
    page_title="Détection de fraude bancaire",
    page_icon="🏦",
    layout="wide",
)

# Initialisation de la mémoire de l'application
if "fenetre"    not in st.session_state:
    st.session_state.fenetre    = []
if "historique" not in st.session_state:
    st.session_state.historique = []
if "total"      not in st.session_state:
    st.session_state.total      = 0
if "if_total"   not in st.session_state:
    st.session_state.if_total   = 0
if "db_total"   not in st.session_state:
    st.session_state.db_total   = 0
if "en_pause"   not in st.session_state:
    st.session_state.en_pause   = False

# Rafraîchissement automatique toutes les 1,5 secondes
st_autorefresh(interval=1500, key="refresh")

# BARRE LATÉRALE — Contrôles
with st.sidebar:
    st.title("🏦 Fraude bancaire")
    st.markdown("---")

    st.markdown("### Sensibilité de détection")
    sensibilite = st.slider(
        label="",
        min_value=1,
        max_value=100,
        value=50,
        help="Plus le niveau est élevé, plus les algorithmes sont stricts "
             "et plus ils signalent de transactions."
    )

    if sensibilite <= 33:
        st.info("Niveau FAIBLE")
    elif sensibilite <= 66:
        st.warning("Niveau MODÉRÉ")
    else:
        st.error("Niveau ÉLEVÉ")

    st.markdown("---")

    col1, col2 = st.columns(2)
    with col1:
        label_pause = "▶ Reprendre" if st.session_state.en_pause else "⏸ Pause"
        if st.button(label_pause, use_container_width=True):
            st.session_state.en_pause = not st.session_state.en_pause
    with col2:
        if st.button("🔄 Reset", use_container_width=True):
            st.session_state.fenetre    = []
            st.session_state.historique = []
            st.session_state.total      = 0
            st.session_state.if_total   = 0
            st.session_state.db_total   = 0

    st.markdown("---")
    st.caption(
        "Les données sont simulées.\n\n"
        "**Isolation Forest** : détecte ce qui est facile à isoler "
        "(points éloignés du groupe).\n\n"
        "**DBSCAN** : détecte ce qui est hors de toute zone dense "
        "(points sans voisins proches)."
    )

# GÉNÉRATION D'UNE NOUVELLE TRANSACTION
if not st.session_state.en_pause:
    txn = generer_transaction(proba_fraude=0.08)

    st.session_state.fenetre.append(txn)
    if len(st.session_state.fenetre) > 50:
        st.session_state.fenetre.pop(0)

    analyser(st.session_state.fenetre, sensibilite)

    derniere = st.session_state.fenetre[-1]

    st.session_state.total    += 1
    st.session_state.if_total += int(derniere["if_suspect"])
    st.session_state.db_total += int(derniere["dbscan_suspect"])

    st.session_state.historique.append(dict(derniere))

# TITRE
statut = "EN PAUSE" if st.session_state.en_pause else "EN DIRECT"
st.title(f"Détection de fraude bancaire en temps réel | {statut}")
st.markdown("---")

# MÉTRIQUES — taux de suspicion
total   = max(st.session_state.total, 1)
taux_if = round(st.session_state.if_total / total * 100, 1)
taux_db = round(st.session_state.db_total / total * 100, 1)

col1, col2, col3 = st.columns(3)
col1.metric("Transactions analysées",       st.session_state.total)
col2.metric("Suspectes — Isolation Forest", st.session_state.if_total, f"{taux_if} % du total")
col3.metric("Suspectes — DBSCAN",           st.session_state.db_total, f"{taux_db} % du total")

st.markdown("---")
# GRAPHIQUES MATPLOTLIB / SEABORN
fenetre = st.session_state.fenetre

if len(fenetre) >= 5:

    # Construire un DataFrame depuis la fenêtre courante
    df = pd.DataFrame(fenetre)

    # Colonne "statut_if" pour le graphique Isolation Forest
    df["statut_if"] = df["if_suspect"].map({
        True:  "Suspecte",
        False: "Normale",
    })

    # Colonne "statut_db" pour le graphique DBSCAN
    df["statut_db"] = df["dbscan_suspect"].map({
        True:  "Hors groupe (bruit)",
        False: "Dans un groupe dense",
    })

    col_g1, col_g2 = st.columns(2)

    # Graphique 1 : Isolation Forest 
    with col_g1:
        st.subheader("Isolation Forest")
        st.caption(
            "Les points **normaux** (verts) forment une masse groupée. "
            "Les points **suspects** (rouges) sont éloignés du groupe — "
            "Isolation Forest les détecte car ils sont faciles à isoler."
        )

        fig1, ax1 = plt.subplots(figsize=(6, 4))

        # On trace avec seaborn : hue = statut_if
        sns.scatterplot(
            data=df,
            x="distance",
            y="montant",
            hue="statut_if",
            palette={
                "Normale":    "#22c55e",
                "Suspecte":  "#ef4444",
            },
            style="statut_if",
            markers={
                "Normale":   "o",
                "Suspecte": "X",
            },
            s=80,           # taille des points
            alpha=0.75,
            ax=ax1,
        )

        ax1.set_xlabel("Distance du domicile (km)", fontsize=10)
        ax1.set_ylabel("Montant (FCFA)", fontsize=10)
        ax1.set_title("Montant vs Distance — vue Isolation Forest", fontsize=11)
        ax1.legend(title="Statut", fontsize=9)
        ax1.yaxis.set_major_formatter(
            plt.FuncFormatter(lambda x, _: f"{int(x):,}")
        )
        plt.tight_layout()
        st.pyplot(fig1)
        plt.close(fig1)

    # Graphique 2 : DBSCAN
    with col_g2:
        st.subheader("DBSCAN")
        st.caption(
            "DBSCAN regroupe les transactions similaires en **zones denses**. "
            "Les points **hors groupe** (rouges) n'ont pas assez de voisins "
            "proches — DBSCAN les classe comme bruit et lève une alerte."
        )

        fig2, ax2 = plt.subplots(figsize=(6, 4))

        sns.scatterplot(
            data=df,
            x="distance",
            y="montant",
            hue="statut_db",
            palette={
                "Dans un groupe dense":    "#22c55e",
                "Hors groupe (bruit)":    "#3b82f6",
            },
            style="statut_db",
            markers={
                "Dans un groupe dense":   "o",
                "Hors groupe (bruit)":   "X",
            },
            s=80,
            alpha=0.75,
            ax=ax2,
        )

        ax2.set_xlabel("Distance du domicile (km)", fontsize=10)
        ax2.set_ylabel("Montant (FCFA)", fontsize=10)
        ax2.set_title("Montant vs Distance — vue DBSCAN", fontsize=11)
        ax2.legend(title="Statut", fontsize=9)
        ax2.yaxis.set_major_formatter(
            plt.FuncFormatter(lambda x, _: f"{int(x):,}")
        )
        plt.tight_layout()
        st.pyplot(fig2)
        plt.close(fig2)

else:
    st.info("⏳ En attente de données… Les graphiques apparaîtront après quelques secondes.")

st.markdown("---")

# ALERTES EN TEMPS RÉEL
st.subheader("🚨 Dernières alertes")

alertes = [
    t for t in reversed(st.session_state.historique)
    if t["if_suspect"] or t["dbscan_suspect"]
][:5]

if alertes:
    for a in alertes:
        detecteurs = []
        if a["if_suspect"]:     detecteurs.append("Isolation Forest")
        if a["dbscan_suspect"]: detecteurs.append("DBSCAN")
        qui = " + ".join(detecteurs)

        st.error(
            f"⚠️ **{a['heure']}** — "
            f"{a['montant']:,} FCFA | "
            f"{a['marchand']} | "
            f"Distance : {a['distance']} km | "
            f"Délai : {a['delai']} s | "
            f"Signalée par : **{qui}**"
        )
else:
    st.success("✅ Aucune alerte pour l'instant.")

st.markdown("---")

# REGISTRE DES 20 DERNIÈRES TRANSACTIONS
st.subheader("Registre des transactions (100 dernières)")

dernieres = st.session_state.historique[-100:][::-1]

if dernieres:
    lignes = []
    for t in dernieres:
        if t["if_suspect"] and t["dbscan_suspect"]:
            statut_ligne = "Les deux"
        elif t["if_suspect"]:
            statut_ligne = "Isolation Forest"
        elif t["dbscan_suspect"]:
            statut_ligne = "DBSCAN"
        else:
            statut_ligne = "Normale"

        lignes.append({
            "Heure":          t["heure"],
            "Montant (FCFA)": f"{t['montant']:,}",
            "Distance (km)":  t["distance"],
            "Délai (s)":      t["delai"],
            "Marchand":       t["marchand"],
            "Résultat":       statut_ligne,
        })

    st.dataframe(pd.DataFrame(lignes), use_container_width=True, hide_index=True)
else:
    st.caption("Le flux démarre dans quelques instants…")
"""
app.py
------
Application de détection de fraude bancaire en temps réel — Sujet 37
Swiss UMEF University — Campus de Dakar — Mr BEBY

Lancement : streamlit run app.py
"""

import streamlit as st
from streamlit_autorefresh import st_autorefresh
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

from simulateur import generer_transaction, CLIENTS
from detecteur import analyser

# ── Configuration ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Détection de fraude bancaire",
    page_icon="🏦",
    layout="wide",
)

# ── Session state ─────────────────────────────────────────────────────────────
DEFAUTS = {
    "fenetre":    [],
    "historique": [],
    "total":      0,
    "if_total":   0,
    "db_total":   0,
    "en_pause":   False,
}
for cle, val in DEFAUTS.items():
    if cle not in st.session_state:
        st.session_state[cle] = ([] if isinstance(val, list) else val)

# ── Rafraîchissement automatique ──────────────────────────────────────────────
st_autorefresh(interval=1500, key="refresh")

# ══════════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.title("🏦 Détection de fraude")
    st.markdown("---")

    st.markdown("### Sensibilité de détection")
    sensibilite = st.slider(
        "",
        min_value=1, max_value=100, value=50,
        help="Augmente la sensibilité des deux algorithmes."
    )

    if sensibilite <= 33:
        st.info("Niveau FAIBLE")
    elif sensibilite <= 66:
        st.warning("Niveau MODÉRÉ")
    else:
        st.error("Niveau ÉLEVÉ")

    st.markdown("---")

    c1, c2 = st.columns(2)
    with c1:
        lbl = "▶ Reprendre" if st.session_state.en_pause else "⏸ Pause"
        if st.button(lbl, use_container_width=True):
            st.session_state.en_pause = not st.session_state.en_pause
    with c2:
        if st.button("🔄 Reset", use_container_width=True):
            st.session_state.fenetre    = []
            st.session_state.historique = []
            st.session_state.total      = 0
            st.session_state.if_total   = 0
            st.session_state.db_total   = 0

    st.markdown("---")
    st.markdown("### Profils des 10 clients")
    st.caption(
        "Chaque client a son propre budget moyen. "
        "Le **ratio** = montant dépensé ÷ budget moyen. "
        "Ratio ≈ 1.0 = normal. Ratio > 4 = suspect."
    )
    profils = pd.DataFrame([
        {
            "ID":     cid,
            "Nom":    c["nom"],
            "Profil": c["profil"],
            "Budget": f"{c['montant_moy']:,} F",
            "Zone":   c["zone"],
        }
        for cid, c in CLIENTS.items()
    ])
    st.dataframe(profils, use_container_width=True, hide_index=True)

# ══════════════════════════════════════════════════════════════════════════════
# GÉNÉRATION + ANALYSE (seulement si pas en pause)
# ══════════════════════════════════════════════════════════════════════════════
if not st.session_state.en_pause:
    txn = generer_transaction(proba_fraude=0.08)

    st.session_state.fenetre.append(txn)
    if len(st.session_state.fenetre) > 60:
        st.session_state.fenetre.pop(0)

    analyser(st.session_state.fenetre, sensibilite)

    t = st.session_state.fenetre[-1]
    st.session_state.total    += 1
    st.session_state.if_total += int(t["if_suspect"])
    st.session_state.db_total += int(t["dbscan_suspect"])
    st.session_state.historique.append(dict(t))

# ══════════════════════════════════════════════════════════════════════════════
# TITRE
# ══════════════════════════════════════════════════════════════════════════════
statut = "PAUSE" if st.session_state.en_pause else "DIRECT"
st.title(f"🏦 Détection de fraude bancaire | {statut}")
st.markdown("---")

# ══════════════════════════════════════════════════════════════════════════════
# MÉTRIQUES
# ══════════════════════════════════════════════════════════════════════════════
total   = max(st.session_state.total, 1)
taux_if = round(st.session_state.if_total / total * 100, 1)
taux_db = round(st.session_state.db_total / total * 100, 1)

c1, c2, c3 = st.columns(3)
c1.metric("Transactions analysées",       st.session_state.total)
c2.metric("Suspectes | Isolation Forest", st.session_state.if_total, f"{taux_if} %")
c3.metric("Suspectes | DBSCAN",           st.session_state.db_total, f"{taux_db} %")

st.markdown("---")

# ══════════════════════════════════════════════════════════════════════════════
# GRAPHIQUES
# ══════════════════════════════════════════════════════════════════════════════
fenetre = st.session_state.fenetre

if len(fenetre) >= 5:
    df = pd.DataFrame(fenetre)

    # Labels lisibles pour seaborn
    df["statut_if"] = df["if_suspect"].map({True: "Suspecte", False: "Normale"})
    df["statut_db"] = df["dbscan_suspect"].map({True: "Hors groupe", False: "Dans groupe dense"})

    # ── NOTE IMPORTANTE ───────────────────────────────────────────────────────
    # On utilise "zone_jitter" calculé UNE SEULE FOIS dans simulateur.py
    # et stocké dans chaque transaction. Ainsi les points restent fixes
    # même quand l'app se rafraîchit → plus de "danse" des points en pause.

    col1, col2 = st.columns(2)

    # ── Graphique 1 : Isolation Forest ───────────────────────────────────────
    with col1:
        st.subheader("Isolation Forest")
        st.caption(
            "**X = ratio** : 1.0 = budget habituel du client. "
            "Les suspects (croix) s'éloignent vers la droite (montant élevé) "
            "ou vers le haut (zone inhabituelle). "
            "Les normaux (cercles) restent groupés autour de x=1, y=0."
        )

        fig1, ax1 = plt.subplots(figsize=(6, 4))
        sns.scatterplot(
            data=df,
            x="ratio_montant",
            y="zone_jitter",
            hue="statut_if",
            style="statut_if",
            palette={"Normale": "#22c55e", "Suspecte": "#ef4444"},
            markers={"Normale": "o", "Suspecte": "X"},
            s=80,
            alpha=0.8,
            ax=ax1,
        )
        # Ligne verticale à ratio=1 : limite du "budget normal"
        ax1.axvline(x=1.0, color="#94a3b8", linestyle="--",
                    linewidth=1.0, label="ratio=1 (budget normal)")
        ax1.set_xlabel("Ratio  (montant ÷ budget habituel du client)", fontsize=9)
        ax1.set_ylabel("Zone  (0 = habituelle  |  1 = inhabituelle)", fontsize=9)
        ax1.set_yticks([0, 1])
        ax1.set_yticklabels(["Zone habituelle (0)", "Zone inhabituelles (1)"])
        ax1.set_title("Isolation Forest — éloignement du groupe", fontsize=10)
        ax1.legend(fontsize=8, title="Statut")
        plt.tight_layout()
        st.pyplot(fig1)
        plt.close(fig1)

    # ── Graphique 2 : DBSCAN ─────────────────────────────────────────────────
    with col2:
        st.subheader("DBSCAN")
        st.caption(
            "**X = ratio**, **Y = zone**. "
            "Les cercles verts forment les zones denses (comportements habituels). "
            "Les croix bleues sont des points **sans voisins proches** — "
            "aucun autre client ne fait ce type de transaction → alerte."
        )

        fig2, ax2 = plt.subplots(figsize=(6, 4))
        sns.scatterplot(
            data=df,
            x="ratio_montant",
            y="zone_jitter",
            hue="statut_db",
            style="statut_db",
            palette={"Dans groupe dense": "#22c55e", "Hors groupe": "#3b82f6"},
            markers={"Dans groupe dense": "o", "Hors groupe": "X"},
            s=80,
            alpha=0.8,
            ax=ax2,
        )
        ax2.axvline(x=1.0, color="#94a3b8", linestyle="--",
                    linewidth=1.0, label="ratio=1 (budget normal)")
        ax2.set_xlabel("Ratio  (montant ÷ budget habituel du client)", fontsize=9)
        ax2.set_ylabel("Zone  (0 = habituelle  |  1 = inhabituelle)", fontsize=9)
        ax2.set_yticks([0, 1])
        ax2.set_yticklabels(["Zone habituelle (0)", "Zone inhabituelle (1)"])
        ax2.set_title("DBSCAN — absence de voisins proches", fontsize=10)
        ax2.legend(fontsize=8, title="Statut")
        plt.tight_layout()
        st.pyplot(fig2)
        plt.close(fig2)

else:
    st.info("⏳ Les graphiques apparaîtront dans quelques secondes…")

st.markdown("---")

# ══════════════════════════════════════════════════════════════════════════════
# ALERTES
# ══════════════════════════════════════════════════════════════════════════════
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

        raisons = []
        if a["ratio_montant"] > 3:
            raisons.append(f"{a['ratio_montant']}× son budget habituel")
        if a["zone_diff"] == 1:
            raisons.append(f"zone habituelle = {a['zone_habituelle']} → détectée à {a['zone']}")
        raison_txt = " + ".join(raisons) if raisons else "combinaison inhabituelle"

        st.error(
            f"⚠️ **{a['heure']}**  |  **{a['nom']}** ({a['profil']})  |  "
            f"{a['montant']:,} FCFA  |  Ratio : **{a['ratio_montant']}**  |  "
            f"Détecté par : **{' + '.join(detecteurs)}**  |  "
            f"Raison : *{raison_txt}*"
        )
else:
    st.success("✅ Aucune alerte pour l'instant.")

st.markdown("---")

# ══════════════════════════════════════════════════════════════════════════════
# TABLEAU — 100 dernières transactions
# ══════════════════════════════════════════════════════════════════════════════
st.subheader("📋 Registre des 100 dernières transactions")

dernieres = st.session_state.historique[-100:][::-1]

if dernieres:
    lignes = []
    for t in dernieres:
        if t["if_suspect"] and t["dbscan_suspect"]:
            res = "⚠️ Les deux"
        elif t["if_suspect"]:
            res = "🟡 IF"
        elif t["dbscan_suspect"]:
            res = "🔵 DBSCAN"
        else:
            res = "✅ Normale"

        lignes.append({
            "Heure":          t["heure"],
            "Client":         t["client_id"],
            "Nom":            t["nom"],
            "Profil":         t["profil"],
            "Montant (FCFA)": f"{t['montant']:,}",
            "Zone":           t["zone"],
            "Zone habituelle":t["zone_habituelle"],
            "Ratio":          t["ratio_montant"],
            "Résultat":       res,
        })

    st.dataframe(
        pd.DataFrame(lignes),
        use_container_width=True,
        hide_index=True,
    )
else:
    st.caption("Le flux démarre dans quelques instants…")

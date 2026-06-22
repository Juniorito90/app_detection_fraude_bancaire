import time
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from streamlit_autorefresh import st_autorefresh

from data_simulator import generate_transaction
from fraud_detector import analyze_window, sensitivity_to_params

#  Configuration de la page ─
st.set_page_config(
    page_title="Application de detection de Fraude bancaire",
    page_icon="🔐",
    layout="wide",
    initial_sidebar_state="expanded",
)

#  CSS personnalisé 
st.markdown("""
<style>
  /* Fond général */
  .stApp { background-color: #0E1320; color: #C7CEDB; }
  section[data-testid="stSidebar"] { background-color: #161D2E; }

  /* Cartes de métriques */
  div[data-testid="metric-container"] {
      background-color: #161D2E;
      border: 1px solid #2A3349;
      padding: 14px 18px;
      border-radius: 4px;
  }
  div[data-testid="metric-container"] label {
      color: #76839C !important;
      font-size: 12px !important;
      letter-spacing: .04em;
  }
  div[data-testid="metric-container"] div[data-testid="stMetricValue"] {
      font-family: 'IBM Plex Mono', monospace;
      font-size: 26px !important;
      color: #C7CEDB;
  }

  /* Titre principal */
  h1 { color: #4FA8E0 !important; font-size: 22px !important; }
  h2, h3 { color: #C7CEDB !important; }

  /* Tableau de transactions */
  .stDataFrame { border: 1px solid #2A3349; border-radius: 4px; }

  /* Alertes */
  .alert-box {
      background: rgba(226,84,61,.12);
      border-left: 3px solid #E2543D;
      padding: 8px 14px;
      margin: 4px 0;
      border-radius: 0 4px 4px 0;
      font-size: 13px;
      font-family: 'IBM Plex Mono', monospace;
  }
  .alert-if   { border-left-color: #E8A33D; background: rgba(232,163,61,.10); }
  .alert-db   { border-left-color: #4FA8E0; background: rgba(79,168,224,.10); }
  .alert-both { border-left-color: #E2543D; background: rgba(226,84,61,.14); }
</style>
""", unsafe_allow_html=True)

#  Constantes 
WINDOW_SIZE   = 80    # transactions conservées pour le clustering
MAX_FEED_ROWS = 25    # lignes affichées dans le registre
REFRESH_MS    = 1500  # intervalle de rafraîchissement en ms

#  Session state (persistance entre rechargements) ─
def _init_state():
    defaults = {
        "window":     [],
        "all_txns":   [],     # historique complet pour les graphiques
        "stats": {
            "total": 0, "true_fraud": 0,
            "if_flagged": 0, "dbscan_flagged": 0, "consensus": 0,
        },
        "running":   True,
        "alerts":    [],      # file des 6 dernières alertes
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

_init_state()

# Sidebar
with st.sidebar:
    st.markdown("### 🔐 Paramètres de détection")
    st.markdown("---")

    sensitivity = st.slider(
        "Sensibilité de détection",
        min_value=1, max_value=100, value=50, step=1,
        help="Augmenter la sensibilité détecte plus de fraudes potentielles "
             "mais génère aussi plus de faux positifs."
    )

    params = sensitivity_to_params(sensitivity)
    level  = ("🟢 FAIBLE" if sensitivity <= 25 else
              "🟡 MODÉRÉE" if sensitivity <= 55 else
              "🔴 ÉLEVÉE")
    st.markdown(f"**Niveau de menace :** {level}")

    st.markdown("---")
    st.markdown("**Paramètres actifs**")
    st.markdown(f"""
| Paramètre | Valeur |
|-----------|--------|
| IF contamination | `{params['contamination']}` |
| DBSCAN epsilon   | `{params['eps']}` |
| DBSCAN min_pts   | `{params['min_samples']}` |
""")

    st.markdown("---")

    col_a, col_b = st.columns(2)
    with col_a:
        if st.button("⏸ Pause" if st.session_state["running"] else "▶ Reprendre",
                     use_container_width=True):
            st.session_state["running"] = not st.session_state["running"]
    with col_b:
        if st.button("🔄 Réinitialiser", use_container_width=True):
            for k in ["window", "all_txns", "alerts"]:
                st.session_state[k] = []
            st.session_state["stats"] = {
                "total": 0, "true_fraud": 0,
                "if_flagged": 0, "dbscan_flagged": 0, "consensus": 0,
            }

    st.markdown("---")
    st.markdown("**À propos**")
    st.caption(
        "Flux simulé (FCFA). Les fraudes injectées (~8 %) "
        "servent à évaluer les algorithmes — elles ne sont "
        "pas transmises aux modèles."
    )

# Rafraîchissement automatique
# Génère une nouvelle transaction à chaque cycle si le flux est actif
count = st_autorefresh(interval=REFRESH_MS, key="autorefresh")

if st.session_state["running"]:
    txn = generate_transaction(fraud_probability=0.08)
    st.session_state["window"].append(txn)
    if len(st.session_state["window"]) > WINDOW_SIZE:
        st.session_state["window"].pop(0)

    analyze_window(st.session_state["window"], sensitivity)
    t = st.session_state["window"][-1]   # dernière transaction analysée

    # Mise à jour des stats
    s = st.session_state["stats"]
    s["total"]      += 1
    s["true_fraud"] += int(t["is_fraud_truth"])
    s["if_flagged"] += int(t["if_flag"])
    s["dbscan_flagged"] += int(t["dbscan_flag"])
    s["consensus"]  += int(t["if_flag"] and t["dbscan_flag"])

    # Historique global
    st.session_state["all_txns"].append(dict(t))

    # File d'alertes (6 max)
    if t["if_flag"] or t["dbscan_flag"]:
        label = ("🔴 CONSENSUS" if t["if_flag"] and t["dbscan_flag"]
                 else "🟡 Isolation Forest" if t["if_flag"]
                 else "🔵 DBSCAN")
        st.session_state["alerts"].insert(0, {
            "label": label,
            "msg":   f"#{t['id']} — {t['amount']:,} FCFA | "
                     f"{t['merchant']} | {t['distance_km']} km | "
                     f"{t['timestamp']}",
            "type":  ("both" if t["if_flag"] and t["dbscan_flag"]
                      else "if" if t["if_flag"] else "db"),
        })
        st.session_state["alerts"] = st.session_state["alerts"][:6]

# En-tête
st.markdown(
    "# 🔐 Console de surveillance — Détection de fraude bancaire en temps réel"
)

status = "🟢 FLUX ACTIF" if st.session_state["running"] else "⏸ EN PAUSE"
st.caption(f"{status}  ·  Algorithmes : Isolation Forest + DBSCAN  "
           f"·  Fenêtre : {len(st.session_state['window'])} / {WINDOW_SIZE} transactions")

st.markdown("---")

# Métriques
s = st.session_state["stats"]
total = max(s["total"], 1)

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("📊 Transactions analysées", f"{s['total']:,}")
c2.metric("🟡 Isolation Forest",
          s["if_flagged"],
          f"{s['if_flagged']/total*100:.1f} %")
c3.metric("🔵 DBSCAN",
          s["dbscan_flagged"],
          f"{s['dbscan_flagged']/total*100:.1f} %")
c4.metric("🔴 Consensus (les deux)",
          s["consensus"],
          f"{s['consensus']/total*100:.1f} %")
c5.metric("⚠️ Fraudes injectées (vérité terrain)",
          s["true_fraud"],
          f"{s['true_fraud']/total*100:.1f} %")

st.markdown("---")

#  Colonnes principales : graphiques gauche | alertes droite 
col_left, col_right = st.columns([3, 1])

with col_left:

    #  Graphique 1 : évolution temporelle des détections 
    st.markdown("#### 📈 Évolution des détections dans le temps")

    all_df = pd.DataFrame(st.session_state["all_txns"][-120:])

    if not all_df.empty:
        # Comptage glissant par tranche de 10 transactions
        bucket_size = 10
        all_df["bucket"] = (all_df["id"] // bucket_size) * bucket_size

        agg = all_df.groupby("bucket").agg(
            IF=("if_flag", "sum"),
            DB=("dbscan_flag", "sum"),
            Fraudes=("is_fraud_truth", "sum"),
            Total=("id", "count"),
        ).reset_index()

        fig_line = go.Figure()
        fig_line.add_trace(go.Scatter(
            x=agg["bucket"], y=agg["IF"],
            name="Isolation Forest", mode="lines+markers",
            line=dict(color="#E8A33D", width=2),
            marker=dict(size=5),
        ))
        fig_line.add_trace(go.Scatter(
            x=agg["bucket"], y=agg["DB"],
            name="DBSCAN", mode="lines+markers",
            line=dict(color="#4FA8E0", width=2),
            marker=dict(size=5),
        ))
        fig_line.add_trace(go.Scatter(
            x=agg["bucket"], y=agg["Fraudes"],
            name="Fraudes réelles (vérité)", mode="lines",
            line=dict(color="#E2543D", width=1.5, dash="dot"),
        ))
        fig_line.update_layout(
            paper_bgcolor="#161D2E", plot_bgcolor="#0E1320",
            font=dict(color="#C7CEDB", size=12),
            legend=dict(bgcolor="#161D2E", bordercolor="#2A3349"),
            margin=dict(l=10, r=10, t=10, b=30),
            height=220,
            xaxis=dict(gridcolor="#2A3349", title="N° transaction"),
            yaxis=dict(gridcolor="#2A3349", title="Alertes / tranche"),
        )
        st.plotly_chart(fig_line, use_container_width=True)

    #  Graphique 2 : scatter montant vs distance (fenêtre courante) 
    st.markdown("#### 🗺️ Espace de détection — Montant vs Distance (fenêtre active)")

    if len(st.session_state["window"]) >= 5:
        win_df = pd.DataFrame(st.session_state["window"])
        win_df["statut"] = win_df.apply(
            lambda r: "🔴 Consensus" if r["if_flag"] and r["dbscan_flag"]
                      else "🟡 IF seul" if r["if_flag"]
                      else "🔵 DB seul" if r["dbscan_flag"]
                      else "✅ Normal",
            axis=1,
        )
        color_map = {
            "✅ Normal":    "#3FAE7A",
            "🟡 IF seul":   "#E8A33D",
            "🔵 DB seul":   "#4FA8E0",
            "🔴 Consensus": "#E2543D",
        }
        fig_scatter = px.scatter(
            win_df, x="distance_km", y="amount",
            color="statut", color_discrete_map=color_map,
            size="if_score", size_max=18,
            hover_data=["id", "merchant", "timestamp", "if_score"],
            labels={"distance_km": "Distance (km)",
                    "amount": "Montant (FCFA)"},
        )
        fig_scatter.update_layout(
            paper_bgcolor="#161D2E", plot_bgcolor="#0E1320",
            font=dict(color="#C7CEDB", size=12),
            legend=dict(bgcolor="#161D2E", bordercolor="#2A3349",
                        title_text="Statut"),
            margin=dict(l=10, r=10, t=10, b=30),
            height=280,
            xaxis=dict(gridcolor="#2A3349"),
            yaxis=dict(gridcolor="#2A3349"),
        )
        st.plotly_chart(fig_scatter, use_container_width=True)

with col_right:
    #  Gauge de risque global 
    st.markdown("#### 🎯 Taux de suspicion")

    rate = s["consensus"] / total * 100
    fig_gauge = go.Figure(go.Indicator(
        mode="gauge+number",
        value=rate,
        number={"suffix": " %", "font": {"color": "#C7CEDB", "size": 28}},
        gauge={
            "axis": {"range": [0, 30], "tickcolor": "#76839C",
                     "tickfont": {"color": "#76839C"}},
            "bar": {"color": "#E2543D"},
            "bgcolor": "#161D2E",
            "bordercolor": "#2A3349",
            "steps": [
                {"range": [0,   8],  "color": "#1B2D1E"},
                {"range": [8,  18],  "color": "#2D2410"},
                {"range": [18, 30],  "color": "#2D1010"},
            ],
            "threshold": {
                "line": {"color": "#E2543D", "width": 3},
                "value": rate,
            },
        },
    ))
    fig_gauge.update_layout(
        paper_bgcolor="#161D2E",
        font=dict(color="#C7CEDB"),
        height=200, margin=dict(l=10, r=10, t=20, b=10),
    )
    st.plotly_chart(fig_gauge, use_container_width=True)

    #  Camembert de répartition 
    st.markdown("#### 📊 Répartition des alertes")
    only_if  = s["if_flagged"] - s["consensus"]
    only_db  = s["dbscan_flagged"] - s["consensus"]
    normal   = s["total"] - s["if_flagged"] - only_db
    normal   = max(normal, 0)

    fig_pie = go.Figure(go.Pie(
        labels=["✅ Normales", "🟡 IF seul", "🔵 DB seul", "🔴 Consensus"],
        values=[normal, only_if, only_db, s["consensus"]],
        hole=0.55,
        marker=dict(colors=["#3FAE7A", "#E8A33D", "#4FA8E0", "#E2543D"]),
        textfont=dict(color="#C7CEDB", size=11),
    ))
    fig_pie.update_layout(
        paper_bgcolor="#161D2E",
        font=dict(color="#C7CEDB"),
        showlegend=True,
        legend=dict(bgcolor="#161D2E", font=dict(size=10)),
        height=220, margin=dict(l=0, r=0, t=10, b=0),
    )
    st.plotly_chart(fig_pie, use_container_width=True)

    #  Dernières alertes ─
    st.markdown("#### 🚨 Dernières alertes")
    if st.session_state["alerts"]:
        for a in st.session_state["alerts"]:
            css_cls = f"alert-{a['type']}"
            st.markdown(
                f'<div class="alert-box {css_cls}">'
                f'<b>{a["label"]}</b><br>{a["msg"]}'
                f'</div>',
                unsafe_allow_html=True,
            )
    else:
        st.caption("Aucune alerte pour l'instant…")

st.markdown("---")

#  Registre des transactions
st.markdown("#### 📋 Registre des transactions (25 dernières)")

feed = st.session_state["all_txns"][-MAX_FEED_ROWS:][::-1]
if feed:
    df_feed = pd.DataFrame(feed)[[
        "id", "timestamp", "amount", "distance_km",
        "time_since_last", "merchant", "if_flag", "dbscan_flag",
        "if_score", "is_fraud_truth",
    ]].copy()

    df_feed.rename(columns={
        "id":              "N°",
        "timestamp":       "Heure",
        "amount":          "Montant (FCFA)",
        "distance_km":     "Distance km",
        "time_since_last": "Δt (s)",
        "merchant":        "Marchand",
        "if_flag":         "Isolation Forest",
        "dbscan_flag":     "DBSCAN",
        "if_score":        "Score IF",
        "is_fraud_truth":  "Fraude réelle",
    }, inplace=True)

    def _flag(v):
        return "⚠️ SUSPECTE" if v else "✅ normale"

    df_feed["Isolation Forest"] = df_feed["Isolation Forest"].map(_flag)
    df_feed["DBSCAN"]           = df_feed["DBSCAN"].map(_flag)
    df_feed["Fraude réelle"]    = df_feed["Fraude réelle"].map(
        lambda v: "🔴 oui" if v else "—"
    )
    df_feed["Montant (FCFA)"] = df_feed["Montant (FCFA)"].map(
        lambda v: f"{int(v):,}"
    )

    def _row_style(row):
        base = "color: #C7CEDB; "
        if "SUSPECTE" in str(row.get("Isolation Forest", "")) and \
           "SUSPECTE" in str(row.get("DBSCAN", "")):
            return [base + "background-color: rgba(226,84,61,.15)"] * len(row)
        elif "SUSPECTE" in str(row.get("Isolation Forest", "")) or \
             "SUSPECTE" in str(row.get("DBSCAN", "")):
            return [base + "background-color: rgba(232,163,61,.08)"] * len(row)
        return [base] * len(row)

    styled = df_feed.style.apply(_row_style, axis=1)
    st.dataframe(styled, use_container_width=True, hide_index=True)
else:
    st.caption("Le flux démarre dans quelques instants…")
